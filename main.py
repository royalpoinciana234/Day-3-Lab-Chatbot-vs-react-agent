"""
CLI entry point — run the chatbot baseline or the ReAct agent on a query.

Usage:
    python main.py --mode agent   -q "Tôi đau ngực, khó thở. Rảnh chiều T5."
    python main.py --mode chatbot -q "Tôi đau ngực, khó thở."
    python main.py --mode agent   -q "..." --provider google
    python main.py --chat                       # hội thoại nhiều lượt (không thoát)
"""
import argparse

from src.core.provider_factory import get_provider
from src.core.chatbot import run_chatbot
from src.agent.agent import ReActAgent
from src.tools import TOOLS
from src.telemetry.metrics import tracker

_DEFAULT_QUERY = (
    "Tôi bị đau ngực, khó thở và hồi hộp tim đập nhanh mấy hôm nay. "
    "Tôi chỉ rảnh chiều thứ 5 và sáng thứ 7 tuần này. Tìm bác sĩ phù hợp."
)
_EXIT_WORDS = {"exit", "quit", "thoat", "thoát", "q"}


def run_chat(llm):
    """Multi-turn conversation: agent asks back and keeps going until user exits."""
    agent = ReActAgent(llm, TOOLS)
    print("Chế độ hội thoại (gõ 'exit' để thoát).\n")

    first = True
    while True:
        try:
            user_msg = input("Bạn: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nKết thúc.")
            break
        if not user_msg or user_msg.lower() in _EXIT_WORDS:
            print("Kết thúc.")
            break

        # reset only on the first turn; later turns keep prior tool observations
        # (real doctor_id/slot) so a booking confirmation is grounded, not guessed.
        answer = agent.run(user_msg, reset=first)
        first = False
        print(f"Trợ lý: {answer}\n")

    print("=== Session metrics ===")
    print(tracker.session_summary())


def main():
    parser = argparse.ArgumentParser(description="Chatbot vs ReAct Agent")
    parser.add_argument("--mode", choices=["chatbot", "agent"], default="agent")
    parser.add_argument("-q", "--query", default=_DEFAULT_QUERY)
    parser.add_argument("--provider", default=None, help="openai | google | local")
    parser.add_argument("--model", default=None)
    parser.add_argument("--chat", action="store_true", help="hội thoại nhiều lượt")
    args = parser.parse_args()

    llm = get_provider(args.provider, args.model)
    print(f"\n[Mode: {'chat' if args.chat else args.mode} | Provider: {llm.model_name}]")

    if args.chat:
        run_chat(llm)
        return

    print(f"User: {args.query}\n")
    if args.mode == "chatbot":
        answer = run_chatbot(llm, args.query)
    else:
        answer = ReActAgent(llm, TOOLS).run(args.query)

    print("\n=== Answer ===")
    print(answer)
    print("\n=== Session metrics ===")
    print(tracker.session_summary())


if __name__ == "__main__":
    main()
