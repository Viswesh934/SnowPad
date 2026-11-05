"""Repository for DuckDB domain operations and analytical queries in SnowPad."""

from datetime import datetime
from typing import Any, Dict, List, Optional
import duckdb

from snowpad.core.models import Actor, DecisionRecord, MetricObservation, PulseEvent
from snowpad.db.connection import get_connection


def _fetch_all_dicts(rel: duckdb.DuckDBPyConnection) -> List[Dict[str, Any]]:
    """Helper to convert DuckDB cursor/relation output into a list of dicts without pandas."""
    if not rel.description:
        return []
    cols = [d[0] for d in rel.description]
    return [dict(zip(cols, row)) for row in rel.fetchall()]


class SnowPadRepository:
    """Encapsulates all DuckDB storage operations and analytical reporting queries."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    # --- Write Operations ---

    def save_actor(self, actor: Actor) -> None:
        """Insert or update an Actor."""
        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO actors (id, name, role, email, team, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [actor.id, actor.name, actor.role, actor.email, actor.team, actor.created_at]
            )

    def save_pulse_event(self, event: PulseEvent) -> None:
        """Record an operational event / hotfix."""
        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO pulse_events (
                    id, actor_id, event_type, title, description,
                    commit_hash, service_name, scope_status, scope_distance,
                    tech_debt_flag, tech_debt_severity, rationale, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    event.id,
                    event.actor_id,
                    event.event_type.value if hasattr(event.event_type, "value") else str(event.event_type),
                    event.title,
                    event.description,
                    event.commit_hash,
                    event.service_name,
                    event.scope_status.value if hasattr(event.scope_status, "value") else str(event.scope_status),
                    event.scope_distance,
                    event.tech_debt_flag,
                    event.tech_debt_severity.value if hasattr(event.tech_debt_severity, "value") else str(event.tech_debt_severity),
                    event.rationale,
                    event.created_at,
                ]
            )

    def save_metric_observation(self, metric: MetricObservation) -> None:
        """Record a performance metric observation correlated to an event."""
        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO metric_observations (
                    id, event_id, metric_name, service_name, endpoint,
                    baseline_value, observed_value, delta_value, unit, measured_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    metric.id,
                    metric.event_id,
                    metric.metric_name,
                    metric.service_name,
                    metric.endpoint,
                    metric.baseline_value,
                    metric.observed_value,
                    metric.delta_value,
                    metric.unit,
                    metric.measured_at,
                ]
            )

    def save_decision(self, decision: DecisionRecord) -> None:
        """Record a triage decision outcome from chat."""
        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO decision_records (
                    id, event_id, author_id, discussion_summary,
                    resolution, target_sprint, ttl_days, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    decision.id,
                    decision.event_id,
                    decision.author_id,
                    decision.discussion_summary,
                    decision.resolution,
                    decision.target_sprint,
                    decision.ttl_days,
                    decision.created_at,
                ]
            )

    # --- Read & Analytical Queries ---

    def get_all_actors(self) -> List[Dict[str, Any]]:
        """List all registered actors in the team."""
        with get_connection(self.db_path) as conn:
            rel = conn.execute("SELECT * FROM actors ORDER BY name ASC")
            return _fetch_all_dicts(rel)

    def get_actor_by_id(self, actor_id: str) -> Optional[Dict[str, Any]]:
        """Lookup an actor by ID."""
        with get_connection(self.db_path) as conn:
            rel = conn.execute("SELECT * FROM actors WHERE id = ?", [actor_id])
            res = _fetch_all_dicts(rel)
            return res[0] if res else None

    def get_weekly_pulse(self) -> List[Dict[str, Any]]:
        """Query the weekly operational pulse aggregated across the team."""
        with get_connection(self.db_path) as conn:
            rel = conn.execute("SELECT * FROM v_weekly_pulse ORDER BY pulse_week DESC, total_events DESC")
            return _fetch_all_dicts(rel)

    def get_developer_impact(self, actor_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Query quarterly developer impact (perf review / brag sheet data)."""
        with get_connection(self.db_path) as conn:
            if actor_id:
                query = "SELECT * FROM v_developer_impact WHERE actor_id = ?"
                rel = conn.execute(query, [actor_id])
            else:
                query = "SELECT * FROM v_developer_impact ORDER BY high_impact_circle_count DESC"
                rel = conn.execute(query)
            return _fetch_all_dicts(rel)

    def get_circle_radar_data(self, actor_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve events positioned for the Circle of Scope visual radar."""
        with get_connection(self.db_path) as conn:
            if actor_id:
                query = """
                SELECT r.* FROM v_circle_radar r
                JOIN pulse_events e ON r.event_id = e.id
                WHERE e.actor_id = ?
                ORDER BY r.scope_distance ASC
                """
                rel = conn.execute(query, [actor_id])
            else:
                query = "SELECT * FROM v_circle_radar ORDER BY scope_distance ASC"
                rel = conn.execute(query)
            return _fetch_all_dicts(rel)

    def get_active_tech_debt(self) -> List[Dict[str, Any]]:
        """Query hotfixes flagged with tech debt that need PRD refactor planning."""
        with get_connection(self.db_path) as conn:
            query = """
            SELECT 
                e.id AS event_id,
                e.title,
                e.service_name,
                a.name AS author_name,
                e.tech_debt_severity,
                e.rationale,
                e.created_at,
                d.resolution,
                d.target_sprint
            FROM pulse_events e
            JOIN actors a ON e.actor_id = a.id
            LEFT JOIN decision_records d ON e.id = d.event_id
            WHERE e.tech_debt_flag = TRUE
            ORDER BY e.created_at DESC
            """
            rel = conn.execute(query)
            return _fetch_all_dicts(rel)
