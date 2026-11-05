"""SnowPad Switch Agent - Connects to Slack/Discord to audit uncertain chats and sync members."""

import re
from typing import Any, Dict, Optional
from snowpad.agent.sync import sync_workspace_members
from snowpad.core.analytics import build_developer_review_dossier, build_weekly_pulse_digest
from snowpad.core.models import (
    Actor,
    ChatSignal,
    MetricObservation,
    ScopeStatus,
    SignalResolution,
    SignalType,
)
from snowpad.db.repository import SnowPadRepository


class SnowPadSwitchAgent:
    """The conversational agent living in Slack/Discord via Switch to govern scope & chat entropy."""

    def __init__(self, repo: Optional[SnowPadRepository] = None):
        self.repo = repo or SnowPadRepository()

    def handle_command(self, text: str, user_id: str, channel: str = "#product-ideas") -> Dict[str, Any]:
        """Processes slash commands like /snowpad radar, /snowpad review, or /snowpad sync."""
        text_clean = text.strip()

        # 1. /snowpad sync [slack|discord]
        if "/snowpad sync" in text_clean:
            platform = "discord" if "discord" in text_clean else "slack"
            members = sync_workspace_members(platform=platform, repo=self.repo)
            return {
                "type": "sync_result",
                "message": f"Synced {len(members)} members and their designations from {platform.title()} into DuckDB!",
                "members": [{"name": m.name, "role": m.role} for m in members],
            }

        # 2. /snowpad review [@actor]
        if "/snowpad review" in text_clean:
            # Extract actor id if specified
            parts = text_clean.split()
            actor_id = parts[2].replace("@", "") if len(parts) > 2 else "maya_patel"
            try:
                dossier = build_developer_review_dossier(actor_id=actor_id, repo=self.repo)
                return {
                    "type": "review_dossier",
                    "actor_name": dossier["actor"]["name"],
                    "role": dossier["actor"]["role"],
                    "verdict": dossier["verdict"],
                    "focus_summary": dossier["focus_summary"],
                    "metrics": dossier["impact_metrics"],
                    "recommendations": dossier["recommendations"],
                }
            except Exception as e:
                return {"type": "error", "message": f"Could not find contributor '{actor_id}': {e}"}

        # 3. /snowpad radar
        if "/snowpad radar" in text_clean:
            items = self.repo.get_circle_radar_data()
            inside = [i for i in items if i["scope_status"] == "INSIDE_CIRCLE"]
            debates = [i for i in items if i["scope_status"] == "BORDERLINE"]
            whims = [i for i in items if i["scope_status"] == "OUTSIDE_CIRCLE"]
            return {
                "type": "radar_summary",
                "total": len(items),
                "inside_count": len(inside),
                "debates_count": len(debates),
                "whims_count": len(whims),
                "items": items[:5],
            }

        # 4. /snowpad weekly
        if "/snowpad weekly" in text_clean:
            digest = build_weekly_pulse_digest(self.repo)
            return {
                "type": "weekly_pulse",
                "contributors": digest["total_active_contributors"],
                "inside": digest["inside_circle_count"],
                "debates": digest["pending_debates_count"],
                "whims": digest["outside_circle_count"],
            }

        return {
            "type": "help",
            "message": "Available commands: `/snowpad radar`, `/snowpad review @actor`, `/snowpad sync slack`, `/snowpad weekly`",
        }

    def analyze_chat_message(self, text: str, user_id: str, channel: str = "#product-ideas") -> Optional[Dict[str, Any]]:
        """Analyzes loose chat messages, scores uncertainty, and determines circle scope."""
        text_lower = text.lower()

        # Check for proposal or whim trigger patterns
        is_proposal = bool(re.search(r"(what if|maybe we|could we|how about|thinking of|proposing|can we)", text_lower))
        if not is_proposal:
            return None  # Standard banter, ignore

        # 1. Determine Signal Type
        if "latency" in text_lower or "lock" in text_lower or "db" in text_lower or "kafka" in text_lower:
            signal_type = SignalType.ARCH_DEBATE
        elif "confetti" in text_lower or "animation" in text_lower or "color" in text_lower or "theme" in text_lower:
            signal_type = SignalType.CASUAL_WHIM
        elif "pivot" in text_lower or "redesign" in text_lower or "switch" in text_lower:
            signal_type = SignalType.SCOPE_PIVOT
        else:
            signal_type = SignalType.FEATURE_PROPOSAL

        # 2. Compute Uncertainty Score (0.0 to 1.0)
        uncertainty = 0.5  # Baseline
        if "what if" in text_lower or "thinking of" in text_lower or "maybe" in text_lower:
            uncertainty += 0.25
        if "benchmarked" in text_lower or "measured" in text_lower or "pr" in text_lower:
            uncertainty -= 0.35
        if signal_type == SignalType.CASUAL_WHIM:
            uncertainty = max(uncertainty, 0.85)

        uncertainty = max(0.1, min(0.95, uncertainty))

        # 3. Calculate Scope Distance and Status
        if uncertainty <= 0.35:
            scope_status = ScopeStatus.INSIDE_CIRCLE
            distance = 0.35
            resolution = SignalResolution.APPROVED_FOR_SPRINT
        elif uncertainty >= 0.70:
            scope_status = ScopeStatus.OUTSIDE_CIRCLE
            distance = 1.65
            resolution = SignalResolution.PARKED_AS_WHIM
        else:
            scope_status = ScopeStatus.BORDERLINE_DEBATE
            distance = 0.85
            resolution = SignalResolution.UNDER_DEBATE

        # 4. Check if Actor exists in DuckDB; if not, register
        actor = self.repo.get_actor_by_id(user_id)
        if not actor:
            actor = Actor(
                id=user_id,
                name=f"User {user_id}",
                role="Engineer / Contributor",
                email=f"{user_id}@chat.internal",
                team=channel,
            )
            self.repo.save_actor(actor)

        # 5. Persist to DuckDB
        import uuid
        signal_id = f"sig_{uuid.uuid4().hex[:8]}"
        title = text.strip()[:60] + ("..." if len(text.strip()) > 60 else "")

        signal = ChatSignal(
            id=signal_id,
            actor_id=user_id,
            signal_type=signal_type,
            title=title,
            summary=text.strip(),
            origin_channel=channel,
            uncertainty_score=uncertainty,
            scope_status=scope_status,
            scope_distance=distance,
            resolution=resolution,
        )
        self.repo.save_chat_signal(signal)

        return {
            "signal_id": signal_id,
            "title": title,
            "signal_type": signal_type.value,
            "uncertainty_pct": int(uncertainty * 100),
            "scope_status": scope_status.value,
            "resolution": resolution.value,
            "author_id": user_id,
            "channel": channel,
        }
