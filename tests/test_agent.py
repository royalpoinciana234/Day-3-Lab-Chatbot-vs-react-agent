"""ReAct agent loop tests using a scripted FakeLLM (no API key needed)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.llm_provider import LLMProvider
from src.agent.agent import ReActAgent
from src.tools import TOOLS


class FakeLLM(LLMProvider):
    """Replays a fixed list of model outputs, one per generate() call."""

    def __init__(self, turns):
        super().__init__("fake-model")
        self.turns = turns
        self.i = 0

    def generate(self, prompt, system_prompt=None):
        out = self.turns[min(self.i, len(self.turns) - 1)]
        self.i += 1
        return {
            "content": out,
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            "latency_ms": 1,
            "provider": "fake",
        }

    def stream(self, prompt, system_prompt=None):
        yield self.generate(prompt)["content"]


def test_full_trace_reaches_final_answer():
    turns = [
        'Thought: phân loại.\nAction: classify_specialty(symptoms=["đau ngực","khó thở"])',
        'Thought: tìm bác sĩ.\nAction: search_doctors(specialty="Tim mạch")',
        'Thought: check BS01.\nAction: get_availability(doctor_id="BS01", time_window=["x"])',
        'Thought: check BS02.\nAction: get_availability(doctor_id="BS02", time_window=["x"])',
        "Thought: đủ rồi.\nFinal Answer: BS. Lan rảnh 14:30 thứ 5.",
    ]
    agent = ReActAgent(FakeLLM(turns), TOOLS)
    answer = agent.run("đau ngực, khó thở")
    assert "BS. Lan" in answer
    assert len(agent.history) == 5
    assert agent.history[0]["action"].startswith("classify_specialty")


def test_hallucinated_tool_is_reported():
    turns = [
        "Thought: gọi tool lạ.\nAction: send_email(to=\"a@b.c\")",
        "Thought: thôi.\nFinal Answer: Xin lỗi.",
    ]
    agent = ReActAgent(FakeLLM(turns), TOOLS)
    agent.run("test")
    obs = agent.history[0]["observation"]
    assert "không tồn tại" in obs


def test_parse_recovery_on_bad_format():
    turns = [
        "Tôi không theo định dạng gì cả.",  # no Action / Final Answer
        "Thought: ok.\nFinal Answer: Đã hiểu.",
    ]
    agent = ReActAgent(FakeLLM(turns), TOOLS)
    answer = agent.run("test")
    assert answer == "Đã hiểu."


def test_books_only_after_confirmation():
    # Patient already confirmed -> agent may call book_appointment.
    turns = [
        'Thought: bệnh nhân đã đồng ý đặt lịch.\n'
        'Action: book_appointment(doctor_id="BS04", slot="2026-06-06 09:00")',
        "Thought: đã đặt xong.\nFinal Answer: Đã đặt lịch thành công.",
    ]
    agent = ReActAgent(FakeLLM(turns), TOOLS)
    agent.run("...bệnh nhân: đồng ý đặt lịch")
    booking_step = agent.history[0]
    assert booking_step["action"].startswith("book_appointment")
    assert "confirmed" in booking_step["observation"]


def test_repeated_action_loop_guard():
    # Same action every turn -> loop guard breaks on the 3rd identical call.
    loop_turn = 'Thought: lặp.\nAction: search_doctors(specialty="Tim mạch")'
    agent = ReActAgent(FakeLLM([loop_turn]), TOOLS, max_steps=10)
    answer = agent.run("test")
    assert "lặp lại" in answer
    # 2 executed (history), 3rd identical call triggers the guard before executing.
    assert len(agent.history) == 2


def test_max_steps_guard():
    # Distinct actions each turn (never a Final Answer) -> stop at max_steps.
    turns = [
        'Thought: a.\nAction: search_doctors(specialty="Tim mạch")',
        'Thought: b.\nAction: get_availability(doctor_id="BS01", time_window=["x"])',
        'Thought: c.\nAction: get_availability(doctor_id="BS02", time_window=["x"])',
    ]
    agent = ReActAgent(FakeLLM(turns), TOOLS, max_steps=3)
    answer = agent.run("test")
    assert "chưa thể hoàn tất" in answer
    assert len(agent.history) == 3
