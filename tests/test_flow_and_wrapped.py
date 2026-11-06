"""Unit tests for the Feature Lifecycle Flow Engine and SnowPad Wrapped."""

from pathlib import Path
import pytest
from snowpad.core.flow import build_feature_flows, get_signal_journey
from snowpad.db.connection import init_db
from snowpad.db.repository import SnowPadRepository
from snowpad.db.seeder import seed_demo_data
from snowpad.reports.wrapped import build_wrapped_data, generate_actor_wrapped, generate_team_wrapped


@pytest.fixture
def repo(tmp_path: Path) -> SnowPadRepository:
    """Fixture providing clean temp repository with demo data."""
    db_file = tmp_path / "test_flow.duckdb"
    r = SnowPadRepository(db_path=str(db_file))
    init_db(db_path=db_file)
    seed_demo_data(r)
    return r


def test_build_feature_flows(repo: SnowPadRepository) -> None:
    """Verify end-to-end feature lifecycle stages are built correctly."""
    flows = build_feature_flows(repo)
    assert len(flows) >= 4

    # Test Maya's flow (Inside Circle)
    maya_flow = next((f for f in flows if "sig_feat_001" == f["signal_id"]), None)
    assert maya_flow is not None
    assert maya_flow["author"] == "Maya Patel"
    assert maya_flow["channel"] == "#product-ideas"
    assert maya_flow["scope_status"] == "INSIDE_CIRCLE"
    assert maya_flow["uncertainty_pct"] == 15

    stages = maya_flow["stages"]
    assert len(stages) == 5
    assert stages[0]["stage_name"] == "Chat Spark"
    assert stages[1]["stage_name"] == "Ray-Tracing Audit"
    assert stages[2]["stage_name"] == "Circle Horizon"
    assert stages[3]["stage_name"] == "Resolution Action"
    assert stages[4]["stage_name"] == "Verified Impact"
    assert "122.0ms" in stages[4]["impact_summary"]

    # Test Jordan's flow (Outside Circle Whim)
    jordan_flow = next((f for f in flows if "sig_whim_005" == f["signal_id"]), None)
    assert jordan_flow is not None
    assert jordan_flow["scope_status"] == "OUTSIDE_CIRCLE"
    assert jordan_flow["uncertainty_pct"] >= 80
    assert "Shielded" in jordan_flow["stages"][4]["impact_summary"]


def test_get_signal_journey(repo: SnowPadRepository) -> None:
    """Verify single signal lookup returns complete journey."""
    journey = get_signal_journey(repo, "sig_arch_002")
    assert journey is not None
    assert journey["author"] == "Alex Chen"
    assert "Redis Redlock" in journey["title"]
    assert journey["scope_status"] == "INSIDE_CIRCLE"


def test_build_wrapped_data(repo: SnowPadRepository) -> None:
    """Verify quarterly Wrapped metrics, archetype, and dodged bullets."""
    wrapped = build_wrapped_data(repo, actor_id="maya_patel", quarter="Q4-2026")
    assert wrapped["quarter"] == "Q4-2026"
    assert wrapped["actor"]["name"] == "Maya Patel"
    assert wrapped["focus_pct"] == 100.0
    assert wrapped["total_ms_shaved"] == 122.0

    # Archetype check
    arch = wrapped["archetype"]
    assert arch["name"] == "The Laser Architect"
    assert arch["emoji"] == "🎯"
    assert "Lo-Fi Beats" in arch["soundtrack"]

    # Crown jewel check
    assert "Batched" in wrapped["crown_jewel"]["title"]


def test_generate_wrapped_html(repo: SnowPadRepository, tmp_path: Path) -> None:
    """Verify Spotify-Wrapped interactive HTML generation."""
    actor_file = generate_actor_wrapped(repo, actor_id="maya_patel", quarter="Q4-2026")
    assert actor_file.exists()
    content = actor_file.read_text(encoding="utf-8")
    assert "SnowPad Wrapped" in content
    assert "Maya Patel" in content
    assert "The Laser Architect" in content
    assert "Lo-Fi Beats" in content

    team_file = generate_team_wrapped(repo, quarter="Q4-2026")
    assert team_file.exists()
    team_content = team_file.read_text(encoding="utf-8")
    assert "The Entire Engineering & Product Team" in team_content
