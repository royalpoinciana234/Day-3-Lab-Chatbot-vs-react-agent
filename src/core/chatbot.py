"""
Chatbot baseline — a plain single-shot LLM call with no tools and no loop.
Used as the control to compare against the ReAct agent.
"""
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger
from src.telemetry.metrics import tracker

_SYSTEM_PROMPT = (
    "Bạn là trợ lý y tế. Trả lời ngắn gọn, gợi ý chuyên khoa/bác sĩ phù hợp với "
    "triệu chứng của bệnh nhân. Lưu ý đây là gợi ý sơ bộ, không phải chẩn đoán."
)


def run_chatbot(llm: LLMProvider, user_input: str) -> str:
    """Single LLM call, no tools. Returns the answer text."""
    logger.log_event("CHATBOT_START", {"input": user_input, "model": llm.model_name})
    result = llm.generate(user_input, system_prompt=_SYSTEM_PROMPT)
    tracker.track_request(
        provider=result.get("provider", "unknown"),
        model=llm.model_name,
        usage=result.get("usage", {}),
        latency_ms=result.get("latency_ms", 0),
    )
    logger.log_event("CHATBOT_END", {"latency_ms": result.get("latency_ms", 0)})
    return result["content"]
