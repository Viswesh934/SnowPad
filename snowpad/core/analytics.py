"""Analytical synthesis engine for weekly operational pulse and quarterly performance reviews."""

from typing import Any, Dict, List, Optional
from snowpad.db.repository import SnowPadRepository


def build_weekly_pulse_digest(repo: SnowPadRepository) -> Dict[str, Any]:
    """Builds the weekly operational brief for standups and team syncs."""
    weekly_rows = repo.get_weekly_pulse()
    actors = repo.get_all_actors()
    radar = repo.get_circle_radar_data()
    channels = repo.get_channel_chatter()

    inside_circle = [r for r in radar if r["scope_status"] == "INSIDE_CIRCLE"]
    borderline = [r for r in radar if r["scope_status"] == "BORDERLINE"]
    outside_circle = [r for r in radar if r["scope_status"] == "OUTSIDE_CIRCLE"]
    pending_debates = repo.get_pending_debates()

    return {
        "total_active_contributors": len(actors),
        "total_recorded_signals": len(radar),
        "inside_circle_count": len(inside_circle),
        "borderline_count": len(borderline),
        "outside_circle_count": len(outside_circle),
        "pending_debates_count": len(pending_debates),
        "weekly_breakdown": weekly_rows,
        "channel_chatter": channels,
        "pending_debates": pending_debates,
    }


def build_developer_review_dossier(actor_id: str, repo: SnowPadRepository, quarter: str = "Q4-2026") -> Dict[str, Any]:
    """Generates an evidence-backed performance review dossier for a specific contributor."""
    actor = repo.get_actor_by_id(actor_id)
    if not actor:
        raise ValueError(f"Actor with ID '{actor_id}' not found.")

    impact_rows = repo.get_developer_impact(actor_id=actor_id)
    impact = impact_rows[0] if impact_rows else {
        "total_contributions": 0,
        "confirmed_features": 0,
        "whims_quarantined": 0,
        "high_impact_circle_count": 0,
        "low_leverage_churn_count": 0,
        "circle_focus_percentage": 0.0,
        "avg_uncertainty": 0.5,
        "total_ms_shaved": 0.0,
    }

    actor_radar = repo.get_circle_radar_data(actor_id=actor_id)
    inside_items = [r for r in actor_radar if r["scope_status"] == "INSIDE_CIRCLE"]
    borderline_items = [r for r in actor_radar if r["scope_status"] == "BORDERLINE"]
    outside_items = [r for r in actor_radar if r["scope_status"] == "OUTSIDE_CIRCLE"]

    focus_pct = impact.get("circle_focus_percentage") or 0.0
    ms_shaved = impact.get("total_ms_shaved") or 0.0
    quarantined = impact.get("whims_quarantined") or 0

    if focus_pct >= 75.0:
        verdict = "EXCEEDING EXPECTATIONS (High Strategic Alignment)"
        focus_summary = f"{focus_pct}% of proposals & contributions locked into core business milestones."
    elif focus_pct >= 40.0:
        verdict = "MEETING EXPECTATIONS (Balanced Exploration & Delivery)"
        focus_summary = f"{focus_pct}% focus within scope; actively engaged in architectural debates."
    else:
        verdict = "NEEDS ALIGNMENT (High Churn Outside Circle)"
        focus_summary = f"Only {focus_pct}% within core circle; significant chat time spent on parked whims."

    recommendations = []
    if quarantined > 0:
        recommendations.append(
            f"Successfully filtered: {quarantined} off-scope whim discussions parked outside the circle, protecting sprint focus."
        )
    if ms_shaved > 50.0:
        recommendations.append(
            f"Quantified engineering impact: Contributed {ms_shaved}ms total response time reductions on critical endpoints."
        )
    if len(borderline_items) > 0:
        recommendations.append(
            f"Action item: {len(borderline_items)} active chat debates require product leadership sign-off."
        )

    return {
        "quarter": quarter,
        "actor": actor,
        "impact_metrics": impact,
        "verdict": verdict,
        "focus_summary": focus_summary,
        "recommendations": recommendations,
        "inside_circle_events": inside_items,
        "borderline_events": borderline_items,
        "outside_circle_events": outside_items,
    }
