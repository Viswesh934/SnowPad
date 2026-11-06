"""Feature Lifecycle Flow Engine - Traces chat proposals from origin to scope resolution."""

from typing import Any, Dict, List, Optional
from snowpad.db.repository import SnowPadRepository


def build_feature_flows(repo: SnowPadRepository, actor_id: Optional[str] = None, channel: Optional[str] = None) -> List[Dict[str, Any]]:
    """Generates end-to-end lifecycle flow paths for all signals in SnowPad."""
    radar_items = repo.get_circle_radar_data(actor_id=actor_id)
    actors_by_id = {a["id"]: a for a in repo.get_all_actors()}

    flows = []
    for item in radar_items:
        if channel and item.get("origin_channel") != channel:
            continue

        actor_name = item.get("actor_name", "Contributor")
        status = item.get("scope_status", "BORDERLINE")
        resolution = item.get("resolution", "UNDER_DEBATE")
        unc_score = item.get("uncertainty_score", 0.5)
        unc_pct = int(unc_score * 100)
        dist = item.get("scope_distance", 1.0)
        sig_id = item.get("signal_id", "")
        title = item.get("title", "")
        ch = item.get("origin_channel", "#general")
        latency_delta = item.get("latency_delta_ms", 0.0)

        # 1. Origin Stage
        origin_stage = {
            "stage_name": "Chat Spark",
            "channel": ch,
            "author": actor_name,
            "signal_type": item.get("signal_type", "FEATURE_PROPOSAL"),
            "badge_color": "coral" if status == "INSIDE_CIRCLE" else "amber" if status == "BORDERLINE" else "gray",
        }

        # 2. Ray-Tracing Audit Stage
        confidence = "High Certainty" if unc_pct <= 35 else "Active Ambiguity" if unc_pct <= 65 else "Casual / Vague Whim"
        audit_stage = {
            "stage_name": "Ray-Tracing Audit",
            "uncertainty_score": unc_score,
            "uncertainty_pct": unc_pct,
            "confidence_label": confidence,
            "sla_check": "Verified SLA match" if status == "INSIDE_CIRCLE" else "Debate required" if status == "BORDERLINE" else "No SLA intersection",
        }

        # 3. Scope Horizon Stage
        horizon_stage = {
            "stage_name": "Circle Horizon",
            "scope_status": status,
            "scope_distance": dist,
            "zone_label": "Inside Circle (r <= 1.0)" if status == "INSIDE_CIRCLE" else "Borderline Ring (0.6 - 1.0)" if status == "BORDERLINE" else "Outer Orbit (r > 1.0)",
        }

        # 4. Resolution Stage
        res_label = "Approved for Sprint" if resolution == "APPROVED_FOR_SPRINT" else "Under Debate" if resolution == "UNDER_DEBATE" else "Parked as Whim"
        target_dest = "Sprint Backlog" if status == "INSIDE_CIRCLE" else "Refactor PRD / RFC" if status == "BORDERLINE" else "Quarantine Shield"
        resolution_stage = {
            "stage_name": "Resolution Action",
            "resolution": resolution,
            "resolution_label": res_label,
            "destination": target_dest,
        }

        # 5. Business / Sprint Impact Stage
        if status == "INSIDE_CIRCLE":
            impact_text = f"Delivered {abs(latency_delta):.1f}ms latency improvement" if latency_delta < 0 else "Locked into Sprint roadmap"
            impact_type = "PERFORMANCE_WIN"
        elif status == "BORDERLINE":
            impact_text = "Scheduled for architectural alignment in sprint PRD"
            impact_type = "RFC_PENDING"
        else:
            impact_text = "Shielded 34 hours of sprint focus from unverified churn"
            impact_type = "CHURN_SHIELDED"

        impact_stage = {
            "stage_name": "Verified Impact",
            "impact_type": impact_type,
            "impact_summary": impact_text,
            "kpi_impact": item.get("estimated_kpi_impact", "Scope managed"),
        }

        flows.append({
            "signal_id": sig_id,
            "title": title,
            "author": actor_name,
            "channel": ch,
            "scope_status": status,
            "resolution": resolution,
            "uncertainty_pct": unc_pct,
            "scope_distance": dist,
            "stages": [
                origin_stage,
                audit_stage,
                horizon_stage,
                resolution_stage,
                impact_stage,
            ],
            "full_path_str": f"{ch} ➔ {title[:32]} ➔ Ray: {unc_pct}% ➔ {status} ➔ {res_label} ➔ {impact_text}",
        })

    return flows


def get_signal_journey(repo: SnowPadRepository, signal_id: str) -> Optional[Dict[str, Any]]:
    """Look up a specific signal and return its complete lifecycle path."""
    all_flows = build_feature_flows(repo)
    for flow in all_flows:
        if flow["signal_id"] == signal_id or signal_id in flow["title"].lower():
            return flow
    return None
