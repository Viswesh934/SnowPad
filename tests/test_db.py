"""Unit tests for SnowPad's DuckDB schema, repository, and analytical views."""

import pytest
from pathlib import Path
from snowpad.core.analytics import build_developer_review_dossier, build_weekly_pulse_digest
from snowpad.core.models import Actor, EventType, PulseEvent, ScopeStatus
from snowpad.db.connection import init_db
from snowpad.db.repository import SnowPadRepository
from snowpad.db.seeder import seed_demo_data


@pytest.fixture
def temp_repo(tmp_path: Path) -> SnowPadRepository:
    """Fixture providing a clean temporary DuckDB repository."""
    db_file = tmp_path / "test_snowpad.duckdb"
    repo = SnowPadRepository(db_path=str(db_file))
    init_db(db_path=db_file)
    return repo


def test_schema_initialization(temp_repo: SnowPadRepository) -> None:
    """Verify all tables and analytical views are initialized."""
    actors = temp_repo.get_all_actors()
    assert isinstance(actors, list)
    assert len(actors) == 0


def test_seed_demo_data(temp_repo: SnowPadRepository) -> None:
    """Verify demo dataset seeds accurately into DuckDB."""
    seed_demo_data(temp_repo)

    actors = temp_repo.get_all_actors()
    assert len(actors) == 4

    actor_ids = [a["id"] for a in actors]
    assert "alex_chen" in actor_ids
    assert "maya_patel" in actor_ids

    radar = temp_repo.get_circle_radar_data()
    assert len(radar) >= 7

    active_debt = temp_repo.get_active_tech_debt()
    assert len(active_debt) >= 3


def test_weekly_pulse_digest(temp_repo: SnowPadRepository) -> None:
    """Verify weekly operational pulse correctly aggregates events and metrics."""
    seed_demo_data(temp_repo)
    digest = build_weekly_pulse_digest(temp_repo)

    assert digest["total_active_contributors"] == 4
    assert digest["inside_circle_count"] > 0
    assert digest["outside_circle_count"] > 0
    assert len(digest["weekly_breakdown"]) > 0


def test_developer_review_dossier(temp_repo: SnowPadRepository) -> None:
    """Verify individual developer performance review dossier calculations."""
    seed_demo_data(temp_repo)

    # Test Alex Chen (the firefighter with debt)
    alex_review = build_developer_review_dossier("alex_chen", temp_repo)
    assert alex_review["actor"]["name"] == "Alex Chen"
    metrics = alex_review["impact_metrics"]
    assert metrics["hotfixes_shipped"] >= 2
    assert metrics["total_ms_shaved"] > 0
    assert len(alex_review["debt_items"]) >= 2
    assert len(alex_review["recommendations"]) > 0

    # Test Maya Patel (high focus builder)
    maya_review = build_developer_review_dossier("maya_patel", temp_repo)
    assert maya_review["actor"]["name"] == "Maya Patel"
    maya_metrics = maya_review["impact_metrics"]
    assert maya_metrics["circle_focus_percentage"] == 100.0
    assert "EXCEEDING EXPECTATIONS" in maya_review["verdict"]
