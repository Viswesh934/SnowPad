"""Analytical synthesis engine for weekly operational pulse and quarterly performance reviews."""

from typing import Any, Dict, List, Optional
from snowpad.db.repository import SnowPadRepository


def build_weekly_pulse_digest(repo: SnowPadRepository) -> Dict[str, Any]:
    """Builds the weekly operational brief for standups and team syncs."""
    weekly_rows = repo.get_weekly_pulse()
    actors = repo.get_all_actors()
    radar = repo.get_circle_radar_data()

    inside_circle = [r for r in radar if r["scope_status"] == "INSIDE_CIRCLE"]
    outside_circle = [r for r in radar if r["scope_status"] == "OUTSIDE_CIRCLE"]
    active_debt = repo.get_active_tech_debt()

    return {
        "total_active_contributors": len(actors),
        "total_recorded_events": len(radar),
        "inside_circle_count": len(inside_circle),
        "outside_circle_count": len(outside_circle),
        "active_debt_count": len(active_debt),
        "weekly_breakdown": weekly_rows,
        "recent_hotfixes": [r for r in radar if r["event_type"] == "HOTFIX"][:5],
        "active_debt_items": active_debt,
    }


def build_developer_review_dossier(actor_id: str, repo: SnowPadRepository, quarter: str = "Q4-2026") -> Dict[str, Any]:
    """Generates an evidence-backed performance review dossier for a specific developer."""
    actor = repo.get_actor_by_id(actor_id)
    if not actor:
        raise ValueError(f"Actor with ID '{actor_id}' not found.")

    impact_rows = repo.get_developer_impact(actor_id=actor_id)
    impact = impact_rows[0] if impact_rows else {
        "total_contributions": 0,
        "hotfixes_shipped": 0,
        "perf_optimizations": 0,
        "high_impact_circle_count": 0,
        "low_leverage_churn_count": 0,
        "circle_focus_percentage": 0.0,
        "debt_items_incurred": 0,
        "total_ms_shaved": 0.0,
    }

    actor_radar = repo.get_circle_radar_data(actor_id=actor_id)
    inside_items = [r for r in actor_radar if r["scope_status"] == "INSIDE_CIRCLE"]
    outside_items = [r for r in actor_radar if r["scope_status"] == "OUTSIDE_CIRCLE"]
    debt_items = [r for r in actor_radar if r["tech_debt_flag"]]

    # Synthesize manager assessment and key highlights
    focus_pct = impact.get("circle_focus_percentage") or 0.0
    ms_shaved = impact.get("total_ms_shaved") or 0.0

    if focus_pct >= 80.0:
        verdict = "EXCEEDING EXPECTATIONS (High Strategic Focus)"
        focus_summary = f"{focus_pct}% of contributions targeted core business SLAs inside the Circle of Scope."
    elif focus_pct >= 50.0:
        verdict = "MEETING EXPECTATIONS (Balanced Firefighting & Feature Delivery)"
        focus_summary = f"{focus_pct}% focus within scope; noticeable reactive firefighting effort."
    else:
        verdict = "NEEDS ALIGNMENT (High Churn Outside Circle)"
        focus_summary = f"Only {focus_pct}% within circle; significant effort spent on off-scope or unmanaged patches."

    recommendations = []
    if len(debt_items) > 0:
        recommendations.append(
            f"Schedule {len(debt_items)} tracked tech debt items for backlog burn-down before they cause regressions."
        )
    if ms_shaved > 100.0:
        recommendations.append(
            f"Recognize major latency wins: Contributed {ms_shaved}ms total response time reductions across critical endpoints."
        )
    if len(outside_items) > 0:
        recommendations.append(
            f"Establish clearer scope boundaries to reduce {len(outside_items)} ad-hoc whim changes."
        )

    return {
        "quarter": quarter,
        "actor": actor,
        "impact_metrics": impact,
        "verdict": verdict,
        "focus_summary": focus_summary,
        "recommendations": recommendations,
        "inside_circle_events": inside_items,
        "outside_circle_events": outside_items,
        "debt_items": debt_items,
    }
