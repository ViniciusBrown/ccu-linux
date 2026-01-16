"""Generate status file for tray app by calling claude-monitor internals."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from claude_monitor.core.plans import Plans
from claude_monitor.data.analysis import analyze_usage

logger = logging.getLogger(__name__)

STATUS_FILE = Path.home() / ".claude-monitor" / "tray_status.json"


def generate_status(plan: str = "max20") -> Dict[str, Any]:
    """Generate status data using claude-monitor internals."""
    try:
        data = analyze_usage(hours_back=192, use_cache=False)

        if not data:
            return {"error": "No data available", "timestamp": datetime.now().isoformat()}

        blocks = data.get("blocks", [])

        # Find active or most recent block
        current_block = None
        for block in blocks:
            if block.get("isActive"):
                current_block = block
                break
        if not current_block and blocks:
            current_block = blocks[0]

        # Get token limit for plan
        token_limit = Plans.get_token_limit(plan, blocks)

        # Calculate session usage
        session_tokens = 0
        session_cost = 0.0
        session_messages = 0
        reset_time = ""

        if current_block:
            # Use camelCase keys as returned by analyze_usage
            # Only count input + output tokens (not cache) for limit calculation
            tc = current_block.get("tokenCounts", {})
            session_tokens = tc.get("inputTokens", 0) + tc.get("outputTokens", 0)
            session_cost = current_block.get("costUSD", 0.0)
            session_messages = current_block.get("sentMessagesCount", 0)
            reset_time = current_block.get("endTime", "")

        # Percentage
        session_pct = int((session_tokens / token_limit * 100)) if token_limit > 0 else 0

        # Plan config
        plan_config = Plans.get_plan_by_name(plan)
        cost_limit = plan_config.cost_limit if plan_config else 140.0
        message_limit = plan_config.message_limit if plan_config else 2000

        cost_pct = int((session_cost / cost_limit * 100)) if cost_limit > 0 else 0
        message_pct = int((session_messages / message_limit * 100)) if message_limit > 0 else 0

        return {
            "timestamp": datetime.now().isoformat(),
            "plan": plan,
            "token_limit": token_limit,
            "cost_limit": cost_limit,
            "message_limit": message_limit,
            "session": {
                "tokens": session_tokens,
                "tokens_pct": min(100, session_pct),
                "cost": session_cost,
                "cost_pct": min(100, cost_pct),
                "messages": session_messages,
                "messages_pct": min(100, message_pct),
                "reset_time": reset_time,
                "is_active": current_block.get("isActive", False) if current_block else False,
            },
            "totals": {
                "entries": data.get("entries_count", 0),
                "blocks": len(blocks),
                "total_tokens": data.get("total_tokens", 0),
                "total_cost": data.get("total_cost", 0.0),
            }
        }

    except Exception as e:
        logger.exception(f"Error generating status: {e}")
        return {"error": str(e), "timestamp": datetime.now().isoformat()}


def write_status_file(plan: str = "max20") -> bool:
    """Generate and write status to file."""
    try:
        status = generate_status(plan)
        STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
        temp_file = STATUS_FILE.with_suffix(".tmp")
        with open(temp_file, "w") as f:
            json.dump(status, f, indent=2)
        temp_file.replace(STATUS_FILE)
        return True
    except Exception as e:
        logger.exception(f"Error writing status file: {e}")
        return False


def read_status_file() -> Optional[Dict[str, Any]]:
    """Read status from file."""
    if not STATUS_FILE.exists():
        return None
    try:
        with open(STATUS_FILE) as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Error reading status file: {e}")
        return None


if __name__ == "__main__":
    import sys
    plan = sys.argv[1] if len(sys.argv) > 1 else "max20"
    if write_status_file(plan):
        print(f"Status written to {STATUS_FILE}")
        status = read_status_file()
        if status:
            print(json.dumps(status, indent=2))
    else:
        print("Failed", file=sys.stderr)
        sys.exit(1)
