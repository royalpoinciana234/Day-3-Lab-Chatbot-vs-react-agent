"""
Parse the JSON-per-line telemetry logs and print aggregate metrics.

Usage:
    python scripts/parse_logs.py [path/to/logfile.log]

If no path is given, uses today's log under logs/. Skips non-JSON lines
(plain info/error messages) so only structured events are aggregated.
"""
import json
import os
import sys
from collections import Counter
from datetime import datetime


def load_events(path: str):
    events = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue  # plain log line, not a structured event
            if isinstance(obj, dict) and "event" in obj:
                events.append(obj)
    return events


def aggregate(events):
    llm = [e["data"] for e in events if e["event"] == "LLM_METRIC"]
    steps = [e for e in events if e["event"] == "AGENT_STEP"]
    errors = Counter(e["data"]["code"] for e in events if e["event"] == "AGENT_ERROR")
    runs = [e for e in events if e["event"] in ("AGENT_END", "CHATBOT_END")]

    total_tokens = sum(m.get("total_tokens", 0) for m in llm)
    total_cost = sum(m.get("cost_usd", 0.0) for m in llm)
    total_latency = sum(m.get("latency_ms", 0) for m in llm)

    return {
        "llm_requests": len(llm),
        "agent_runs": len([e for e in runs if e["event"] == "AGENT_END"]),
        "chatbot_runs": len([e for e in runs if e["event"] == "CHATBOT_END"]),
        "total_agent_steps": len(steps),
        "total_tokens": total_tokens,
        "total_cost_usd": round(total_cost, 6),
        "total_latency_ms": total_latency,
        "avg_latency_ms": round(total_latency / len(llm), 1) if llm else 0,
        "errors": dict(errors),
    }


def main():
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        path = os.path.join("logs", f"{datetime.now().strftime('%Y-%m-%d')}.log")

    if not os.path.exists(path):
        print(f"❌ Log file not found: {path}")
        sys.exit(1)

    events = load_events(path)
    summary = aggregate(events)

    print(f"\n=== Telemetry summary: {path} ===")
    for k, v in summary.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
