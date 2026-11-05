"""Repository for DuckDB domain operations and analytical queries in SnowPad."""

from datetime import datetime
from typing import Any, Dict, List, Optional
import duckdb

from snowpad.core.models import Actor, ChatSignal, MetricObservation
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

    def save_chat_signal(self, signal: ChatSignal) -> None:
        """Record an uncertain chat signal, proposal, pivot, or whim."""
        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO chat_signals (
                    id, actor_id, signal_type, title, summary,
                    origin_channel, thread_url, uncertainty_score,
                    scope_status, scope_distance, estimated_kpi_impact,
                    resolution, target_sprint, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    signal.id,
                    signal.actor_id,
                    signal.signal_type.value if hasattr(signal.signal_type, "value") else str(signal.signal_type),
                    signal.title,
                    signal.summary,
                    signal.origin_channel,
                    signal.thread_url,
                    signal.uncertainty_score,
                    signal.scope_status.value if hasattr(signal.scope_status, "value") else str(signal.scope_status),
                    signal.scope_distance,
                    signal.estimated_kpi_impact,
                    signal.resolution.value if hasattr(signal.resolution, "value") else str(signal.resolution),
                    signal.target_sprint,
                    signal.created_at,
                ]
            )

    def save_metric_observation(self, metric: MetricObservation) -> None:
        """Record a performance metric observation correlated to a signal."""
        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO metric_observations (
                    id, signal_id, metric_name, service_name, endpoint,
                    baseline_value, observed_value, delta_value, unit, measured_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    metric.id,
                    metric.signal_id,
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
            rel = conn.execute("SELECT * FROM v_weekly_pulse ORDER BY pulse_week DESC, total_signals DESC")
            return _fetch_all_dicts(rel)

    def get_developer_impact(self, actor_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Query quarterly contributor impact (perf review / brag sheet data)."""
        with get_connection(self.db_path) as conn:
            if actor_id:
                query = "SELECT * FROM v_developer_impact WHERE actor_id = ?"
                rel = conn.execute(query, [actor_id])
            else:
                query = "SELECT * FROM v_developer_impact ORDER BY high_impact_circle_count DESC"
                rel = conn.execute(query)
            return _fetch_all_dicts(rel)

    def get_circle_radar_data(self, actor_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve signals positioned for the Circle of Scope visual radar."""
        with get_connection(self.db_path) as conn:
            if actor_id:
                query = """
                SELECT r.* FROM v_circle_radar r
                JOIN chat_signals s ON r.signal_id = s.id
                WHERE s.actor_id = ?
                ORDER BY r.scope_distance ASC
                """
                rel = conn.execute(query, [actor_id])
            else:
                query = "SELECT * FROM v_circle_radar ORDER BY scope_distance ASC"
                rel = conn.execute(query)
            return _fetch_all_dicts(rel)

    def get_channel_chatter(self) -> List[Dict[str, Any]]:
        """Retrieve breakdown of chatter and uncertainty per channel."""
        with get_connection(self.db_path) as conn:
            rel = conn.execute("SELECT * FROM v_channel_chatter")
            return _fetch_all_dicts(rel)

    def get_pending_debates(self) -> List[Dict[str, Any]]:
        """Query chat signals that are currently borderline and under active debate."""
        with get_connection(self.db_path) as conn:
            query = """
            SELECT 
                s.id AS signal_id,
                s.title,
                s.summary,
                s.origin_channel,
                a.name AS author_name,
                s.uncertainty_score,
                s.estimated_kpi_impact,
                s.created_at
            FROM chat_signals s
            JOIN actors a ON s.actor_id = a.id
            WHERE s.resolution = 'UNDER_DEBATE'
            ORDER BY s.uncertainty_score DESC
            """
            rel = conn.execute(query)
            return _fetch_all_dicts(rel)
