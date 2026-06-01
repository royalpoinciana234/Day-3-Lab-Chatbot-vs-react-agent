import logging
import json
import os
from datetime import datetime
from typing import Any, Dict

class IndustryLogger:
    """
    Structured logger that simulates industry practices.
    Logs to both console and a file in JSON format.
    """
    def __init__(self, name: str = "AI-Lab-Agent", log_dir: str = "logs"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # File Handler (JSON)
        log_file = os.path.join(log_dir, f"{datetime.now().strftime('%Y-%m-%d')}.log")
        file_handler = logging.FileHandler(log_file)
        
        # Console Handler
        console_handler = logging.StreamHandler()
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def log_event(self, event_type: str, data: Dict[str, Any]):
        """Logs a structured event as one JSON object per line (parseable)."""
        payload = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": event_type,
            "data": data
        }
        self.logger.info(json.dumps(payload, ensure_ascii=False))

    def log_step(self, step: int, thought: str, action: str, tool: str, observation: str):
        """Log one ReAct step (Thought/Action/Observation) for trace analysis."""
        self.log_event("AGENT_STEP", {
            "step": step,
            "thought": thought,
            "action": action,
            "tool": tool,
            "observation": observation,
        })

    def log_error(self, code: str, detail: str):
        """Log a classified agent error (see ERROR_* codes)."""
        self.log_event("AGENT_ERROR", {"code": code, "detail": detail})

    def info(self, msg: str):
        self.logger.info(msg)

    def error(self, msg: str, exc_info=True):
        self.logger.error(msg, exc_info=exc_info)


# Error-code taxonomy for failure analysis (M4/M5).
ERROR_PARSE = "PARSE_ERROR"
ERROR_HALLUCINATED_TOOL = "HALLUCINATED_TOOL"
ERROR_TOOL_TIMEOUT = "TOOL_TIMEOUT"
ERROR_MAX_STEPS = "MAX_STEPS_EXCEEDED"
ERROR_REPEATED_ACTION = "REPEATED_ACTION_LOOP"

# Global logger instance
logger = IndustryLogger()
