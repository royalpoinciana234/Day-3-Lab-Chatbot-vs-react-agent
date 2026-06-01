"""
Run the comparison experiment: same query set through Chatbot vs ReAct Agent.
Telemetry is written to logs/ — analyse it with scripts/parse_logs.py.

Usage:
    python scripts/run_experiments.py [--provider openai|google|local]

Requires a configured provider (.env). The query set covers happy path,
vague symptoms (unclear_symptoms), and a specialty with no doctors.
"""
import argparse
import os
import sys

# Allow running as `python scripts/run_experiments.py` from project root.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.provider_factory import get_provider
from src.core.chatbot import run_chatbot
from src.agent.agent import ReActAgent
from src.tools import TOOLS
from src.telemetry.metrics import tracker

QUERY_SET = [
    "Tôi bị đau ngực, khó thở và hồi hộp tim đập nhanh. Rảnh chiều thứ 5 và sáng thứ 7.",
    "Mấy hôm nay tôi thấy mệt mệt trong người.",          # vague -> unclear_symptoms
    "Tôi bị đau đầu, chóng mặt, mất ngủ. Tìm bác sĩ giúp.",  # specialty without doctors
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", default=None)
    args = parser.parse_args()

    llm = get_provider(args.provider)

    for i, query in enumerate(QUERY_SET, 1):
        print(f"\n############ Query {i}: {query}")
        for mode in ("chatbot", "agent"):
            tracker.reset()
            print(f"\n--- {mode} ---")
            if mode == "chatbot":
                answer = run_chatbot(llm, query)
            else:
                answer = ReActAgent(llm, TOOLS).run(query)
            print("Answer:", answer)
            print("Metrics:", tracker.session_summary())


if __name__ == "__main__":
    main()
