from typing import Dict, Any
from src.telemetry.logger import logger

# Price per 1K tokens in USD (input, output). Approximate public pricing.
# Local models run on-device, so their cost is zero.
_PRICING = {
    "gpt-4o": (0.0025, 0.01),
    "gpt-4o-mini": (0.00015, 0.0006),
    "gemini-1.5-flash": (0.000075, 0.0003),
    "gemini-1.5-pro": (0.00125, 0.005),
}
# Tier fallbacks matched by substring when the exact model isn't listed
# (covers newer names like gemini-3.1-flash-lite).
_TIER_PRICING = [
    ("flash-lite", (0.00005, 0.0002)),
    ("flash", (0.000075, 0.0003)),
    ("pro", (0.00125, 0.005)),
    ("mini", (0.00015, 0.0006)),
]
_DEFAULT_PRICE = (0.0, 0.0)  # local / unknown models


def _price_for(model: str):
    if model in _PRICING:
        return _PRICING[model]
    for needle, price in _TIER_PRICING:
        if needle in model:
            return price
    return _DEFAULT_PRICE


class PerformanceTracker:
    """
    Tracking industry-standard metrics for LLMs.
    Aggregates per-session totals so the UI/eval can report cost, latency, tokens.
    """
    def __init__(self):
        self.session_metrics = []

    def track_request(self, provider: str, model: str, usage: Dict[str, int], latency_ms: int):
        """Logs a single request metric to our telemetry."""
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        metric = {
            "provider": provider,
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": usage.get("total_tokens", prompt_tokens + completion_tokens),
            "token_ratio": round(completion_tokens / prompt_tokens, 3) if prompt_tokens else 0.0,
            "latency_ms": latency_ms,
            "cost_usd": self._calculate_cost(model, usage, provider),
        }
        self.session_metrics.append(metric)
        logger.log_event("LLM_METRIC", metric)

    def _calculate_cost(self, model: str, usage: Dict[str, int], provider: str = "") -> float:
        """Cost in USD based on per-1K-token pricing. Local models are free."""
        if provider == "local" or model.endswith(".gguf"):
            return 0.0
        in_price, out_price = _price_for(model)
        cost = (usage.get("prompt_tokens", 0) / 1000) * in_price \
            + (usage.get("completion_tokens", 0) / 1000) * out_price
        return round(cost, 6)

    def session_summary(self) -> Dict[str, Any]:
        """Aggregate totals for the current session (Extra Monitoring)."""
        return {
            "requests": len(self.session_metrics),
            "total_tokens": sum(m["total_tokens"] for m in self.session_metrics),
            "total_cost_usd": round(sum(m["cost_usd"] for m in self.session_metrics), 6),
            "total_latency_ms": sum(m["latency_ms"] for m in self.session_metrics),
        }

    def reset(self):
        """Clear metrics — useful between UI runs."""
        self.session_metrics = []


# Global tracker instance
tracker = PerformanceTracker()
