"""Unit tests for SnowPad's DuckDB schema, chat signal repository, and analytical views."""

import pytest
from pathlib import Path
from snowpad.core.analytics import build_developer_review_dossier, build_weekly_pulse_digest
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
    assert "sam_torres" in actor_ids

    radar = temp_repo.get_circle_radar_data()
    assert len(radar) >= 7

    channels = temp_repo.get_channel_chatter()
    assert len(channels) >= 3

    pending_debates = temp_repo.get_pending_debates()
    assert len(pending_debates) >= 2


def test_weekly_pulse_digest(temp_repo: SnowPadRepository) -> None:
    """Verify weekly operational pulse correctly aggregates signals, features, and whims."""
    seed_demo_data(temp_repo)
    digest = build_weekly_pulse_digest(temp_repo)

    assert digest["total_active_contributors"] == 4
    assert digest["inside_circle_count"] >= 3
    assert digest["borderline_count"] >= 2
    assert digest["outside_circle_count"] >= 2
    assert len(digest["weekly_breakdown"]) > 0


def test_developer_review_dossier(temp_repo: SnowPadRepository) -> None:
    """Verify individual contributor performance review dossier calculations."""
    seed_demo_data(temp_repo)

    # Test Maya Patel (high strategic focus, confirmed features)
    maya_review = build_developer_review_dossier("maya_patel", temp_repo)
    assert maya_review["actor"]["name"] == "Maya Patel"
    metrics = maya_review["impact_metrics"]
    assert metrics["confirmed_features"] >= 1
    assert metrics["circle_focus_percentage"] == 100.0
    assert "EXCEEDING EXPECTATIONS" in maya_review["verdict"]

    # Test Jordan Lee (parked whims, protected team focus)
    jordan_review = build_developer_review_dossier("jordan_lee", temp_repo)
    assert jordan_review["actor"]["name"] == "Jordan Lee"
    j_metrics = jordan_review["impact_metrics"]
    assert j_metrics["whims_quarantined"] >= 2
    assert len(jordan_review["recommendations"]) > 0
