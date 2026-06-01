import ast
import re
from typing import List, Dict, Any
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import (
    logger,
    ERROR_PARSE,
    ERROR_HALLUCINATED_TOOL,
    ERROR_TOOL_TIMEOUT,
    ERROR_MAX_STEPS,
    ERROR_REPEATED_ACTION,
)
from src.telemetry.metrics import tracker

# Capture "Action: tool_name(...)" and "Final Answer: ..."
# Greedy args + no DOTALL so the call stays on one line and matches the LAST
# ")" — args may contain inner parentheses, e.g. slot="14:30 (04/06)".
_ACTION_RE = re.compile(r"Action:\s*([A-Za-z_]\w*)\s*\((.*)\)")
_FINAL_RE = re.compile(r"Final Answer:\s*(.+)", re.DOTALL)
_THOUGHT_RE = re.compile(r"Thought:\s*(.+?)(?:\n(?:Action|Final Answer):|$)", re.DOTALL)


class ReActAgent:
    """A ReAct-style agent following the Thought-Action-Observation loop."""

    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 6):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self.history: List[Dict[str, str]] = []
        # Working memory (tool observations + reasoning) carried across chat turns.
        self.scratchpad: str = ""

    def get_system_prompt(self) -> str:
        """System prompt: tool catalog + ReAct format + safety guardrail."""
        lines = []
        for t in self.tools:
            params = ", ".join(t["args_schema"].keys())
            lines.append(f"- {t['name']}: {t['description']} | Tham số: {params}")
        tool_descriptions = "\n".join(lines)

        return f"""Bạn là trợ lý y tế giúp bệnh nhân tìm bác sĩ phù hợp. Bạn có các công cụ:
{tool_descriptions}

Tuân thủ ĐÚNG định dạng ReAct, mỗi lượt chỉ xuất MỘT trong hai:
Thought: lý luận của bạn.
Action: tên_công_cụ(tham_số=giá_trị)
HOẶC khi đã đủ thông tin:
Thought: lý luận cuối.
Final Answer: câu trả lời cho bệnh nhân.

CÚ PHÁP Action bắt buộc — gọi hàm Python với tham số key=value, giá trị là chuỗi/list THẬT:
- ĐÚNG:  Action: classify_specialty(symptoms=["đau ngực", "khó thở"])
- ĐÚNG:  Action: search_doctors(specialty="Tim mạch")
- ĐÚNG:  Action: get_availability(doctor_id="BS01", time_window=["chiều thứ 5"])
- SAI:   Action: classify_specialty(symptoms: list[str] — "...")   ← không viết kiểu/dấu hai chấm
Tuyệt đối KHÔNG ghi tên kiểu dữ liệu hay dấu ":" trong Action.

Ví dụ một lượt hoàn chỉnh:
Thought: Cần xác định chuyên khoa trước.
Action: classify_specialty(symptoms=["đau ngực", "khó thở"])

Quy tắc:
- Phải gọi classify_specialty trước khi tìm bác sĩ.
- get_availability CẦN khung giờ rảnh của bệnh nhân. Nếu bệnh nhân CHƯA cho khung giờ:
  KHÔNG bịa khung giờ và KHÔNG gọi get_availability. Hãy Final Answer NGẮN GỌN (2–3 câu):
  nêu chuyên khoa + hỏi thẳng "Bạn rảnh khung giờ nào?". Không liệt kê dài dòng.
- Chỉ dựa vào Observation thật, KHÔNG bịa dữ liệu (slot, tên bác sĩ).
- Bác sĩ chưa công bố lịch (has_schedule=false): gợi ý bệnh nhân đặt và chờ phòng khám xếp giờ.
- ĐẶT LỊCH (book_appointment) là hành động KHÔNG THỂ HOÀN TÁC. Quy trình bắt buộc:
  1) Khi tìm được slot phù hợp, KHÔNG đặt ngay. Hãy Final Answer hỏi xác nhận:
     nêu rõ bác sĩ + khung giờ + "Bạn có muốn đặt lịch không?".
  2) CHỈ gọi book_appointment(doctor_id, slot) khi bệnh nhân đã XÁC NHẬN đồng ý
     (vd "có", "đồng ý", "đặt đi", "ok đặt"). Dùng đúng slot lấy từ Observation.
  3) Nếu bệnh nhân chưa xác nhận hoặc từ chối: KHÔNG gọi book_appointment.
- Sau khi viết "Action:", DỪNG lại, không tự viết Observation.
"""

    def run(self, user_input: str, reset: bool = True) -> str:
        """Run the ReAct loop until Final Answer or max_steps.

        reset=True starts a fresh problem. reset=False continues an ongoing
        conversation, keeping prior tool observations (real doctor_id/slot) so a
        follow-up like a booking confirmation uses grounded values, not guesses.
        """
        logger.log_event("AGENT_START", {"input": user_input, "model": self.llm.model_name})
        system_prompt = self.get_system_prompt()
        if reset or not self.scratchpad:
            self.scratchpad = f"Câu hỏi bệnh nhân: {user_input}\n"
            self.history = []
        else:
            self.scratchpad += f"Bệnh nhân: {user_input}\n"
        action_counts: Dict[str, int] = {}

        for step in range(1, self.max_steps + 1):
            result = self.llm.generate(self.scratchpad, system_prompt=system_prompt)
            tracker.track_request(
                provider=result.get("provider", "unknown"),
                model=self.llm.model_name,
                usage=result.get("usage", {}),
                latency_ms=result.get("latency_ms", 0),
            )
            text = result["content"]
            thought = self._extract_thought(text)

            # Final Answer wins if it appears before any Action.
            final_match = _FINAL_RE.search(text)
            action_match = _ACTION_RE.search(text)
            action_pos = action_match.start() if action_match else None

            if final_match is not None and (action_pos is None or final_match.start() < action_pos):
                answer = final_match.group(1).strip()
                logger.log_step(step, thought, "Final Answer", "", answer)
                self.history.append({"thought": thought, "action": "Final Answer", "observation": answer})
                logger.log_event("AGENT_END", {"steps": step, "status": "final_answer"})
                return answer

            if not action_match:
                logger.log_error(ERROR_PARSE, f"step {step}: no Action/Final Answer in: {text[:200]}")
                # Nudge the model back into format and retry.
                self.scratchpad += f"{text.strip()}\nObservation: Lỗi định dạng. Hãy xuất 'Action:' hoặc 'Final Answer:'.\n"
                continue

            tool_name = action_match.group(1)
            args_str = action_match.group(2)
            action_repr = f"{tool_name}({args_str})"

            # Loop guard: a model that re-issues an identical action is stuck.
            # Stop on the 3rd identical call instead of burning all steps.
            action_counts[action_repr] = action_counts.get(action_repr, 0) + 1
            if action_counts[action_repr] >= 3:
                logger.log_error(ERROR_REPEATED_ACTION, f"action repeated: {action_repr}")
                logger.log_event("AGENT_END", {"steps": step, "status": "repeated_action_loop"})
                return ("Tôi bị lặp lại cùng một bước mà không tiến triển nên dừng để tránh vòng lặp. "
                        "Vui lòng thử lại hoặc dùng model mạnh hơn.")

            observation = self._execute_tool(tool_name, args_str)
            logger.log_step(step, thought, action_repr, tool_name, str(observation))
            self.history.append({"thought": thought, "action": action_repr, "observation": str(observation)})
            self.scratchpad += f"Thought: {thought}\nAction: {action_repr}\nObservation: {observation}\n"

        logger.log_error(ERROR_MAX_STEPS, f"reached max_steps={self.max_steps}")
        logger.log_event("AGENT_END", {"steps": self.max_steps, "status": "max_steps"})
        return "Xin lỗi, tôi chưa thể hoàn tất trong số bước cho phép. Vui lòng thử lại."

    def _execute_tool(self, tool_name: str, args: str) -> Any:
        """Execute a tool by name with parsed arguments."""
        tool = next((t for t in self.tools if t["name"] == tool_name), None)
        if tool is None:
            logger.log_error(ERROR_HALLUCINATED_TOOL, f"tool not found: {tool_name}")
            return f"Lỗi: công cụ '{tool_name}' không tồn tại."

        try:
            arg_kwargs = self._parse_args(args)
        except Exception as e:  # noqa: BLE001 - surface parse failures as observation
            logger.log_error(ERROR_PARSE, f"arg parse failed for {tool_name}({args}): {e}")
            return f"Lỗi: không phân tích được tham số: {args}"

        try:
            return tool["func"](**arg_kwargs)
        except TimeoutError as e:
            logger.log_error(ERROR_TOOL_TIMEOUT, str(e))
            return f"Lỗi: công cụ {tool_name} hết thời gian chờ."
        except Exception as e:  # noqa: BLE001 - surface tool errors (wrong/missing args) as observation
            logger.log_error(ERROR_PARSE, f"{tool_name} execution failed: {e}")
            return f"Lỗi khi gọi {tool_name}: {e}"

    @staticmethod
    def _parse_args(args: str) -> Dict[str, Any]:
        """Parse 'key=value, key2=value2' into a kwargs dict via AST (safe eval)."""
        args = args.strip()
        if not args:
            return {}
        call = ast.parse(f"f({args})", mode="eval").body
        if not isinstance(call, ast.Call):
            raise ValueError("arguments are not a valid call expression")
        return {kw.arg: ast.literal_eval(kw.value) for kw in call.keywords if kw.arg}

    @staticmethod
    def _extract_thought(text: str) -> str:
        m = _THOUGHT_RE.search(text)
        return m.group(1).strip() if m else ""
