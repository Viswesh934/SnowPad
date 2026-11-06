"""Switch Bridge Adapter - Standard Stdio & JSON-RPC interface for Switch Console and Switch Rooms."""

import json
import sys
from typing import Any, Dict, Optional
from snowpad.agent.bot import SnowPadSwitchAgent
from snowpad.db.repository import SnowPadRepository


class SwitchBridge:
    """Bridges Switch Console process execution and chat streams with SnowPad."""

    def __init__(self, repo: Optional[SnowPadRepository] = None):
        self.repo = repo or SnowPadRepository()
        self.agent = SnowPadSwitchAgent(repo=self.repo)

    def process_payload(self, raw_input: str) -> Dict[str, Any]:
        """Processes either JSON payload from Switch or plain text chat message."""
        raw_clean = raw_input.strip()
        if not raw_clean:
            return {"status": "ignored", "reason": "empty input"}

        # Attempt JSON parse (standard Switch room payload)
        if raw_clean.startswith("{") and raw_clean.endswith("}"):
            try:
                data = json.loads(raw_clean)
                text = data.get("text") or data.get("message") or data.get("content") or ""
                user = data.get("user") or data.get("author") or data.get("sender") or "SwitchUser"
                channel = data.get("channel") or data.get("room") or "#switch-room"
            except Exception:
                text = raw_clean
                user = "SwitchUser"
                channel = "#switch-room"
        else:
            text = raw_clean
            user = "SwitchUser"
            channel = "#switch-room"

        # Check for slash command
        if text.startswith("/snowpad"):
            res = self.agent.handle_command(text, user_id=user, channel=channel)
            return {"status": "command_executed", "result": res}

        # Analyze chat proposal
        audit = self.agent.analyze_chat_message(text, user_id=user, channel=channel)
        if audit:
            return {"status": "audited", "data": audit}

        return {"status": "ignored", "reason": "no proposal or whim detected"}

    def run_stdio_loop(self) -> None:
        """Runs continuous stdio listener for Switch Console orchestration."""
        sys.stderr.write("❄️ SnowPad Switch Bridge ready. Awaiting Switch Console stream...\n")
        sys.stderr.flush()

        for line in sys.stdin:
            if not line.strip():
                continue
            response = self.process_payload(line)
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
