"""Unit tests for member synchronization and Switch chat agent analysis."""

from pathlib import Path
import pytest
from snowpad.agent.bot import SnowPadSwitchAgent
from snowpad.agent.sync import SlackMemberSyncer, DiscordMemberSyncer, sync_workspace_members
from snowpad.db.connection import init_db
from snowpad.db.repository import SnowPadRepository
from snowpad.db.seeder import seed_demo_data


@pytest.fixture
def repo(tmp_path: Path) -> SnowPadRepository:
    """Fixture providing clean temp DuckDB repository."""
    db_file = tmp_path / "test_agent.duckdb"
    r = SnowPadRepository(db_path=str(db_file))
    init_db(db_path=db_file)
    seed_demo_data(r)
    return r


def test_slack_member_sync(repo: SnowPadRepository) -> None:
    """Verify Slack member fetching extracts designations and saves to DuckDB."""
    members = sync_workspace_members(platform="slack", repo=repo)
    assert len(members) >= 4

    roles = [m.role for m in members]
    assert "Staff Backend Engineer" in roles
    assert "Principal Product Architect" in roles

    # Verify saved in DuckDB
    actors = repo.get_all_actors()
    actor_ids = [a["id"] for a in actors]
    assert "U_ALEX_SLACK" in actor_ids


def test_discord_member_sync(repo: SnowPadRepository) -> None:
    """Verify Discord member fetching maps guild roles into designations."""
    members = sync_workspace_members(platform="discord", repo=repo)
    assert len(members) >= 4

    roles = [m.role for m in members]
    assert "Lead SRE / DevOps" in roles
    assert "Core Maintainer" in roles

    actors = repo.get_all_actors()
    actor_ids = [a["id"] for a in actors]
    assert "D_ALEX_DISCORD" in actor_ids


def test_agent_analyze_chat_message(repo: SnowPadRepository) -> None:
    """Verify Switch agent parses uncertainty, classifies signals, and persists to DuckDB."""
    agent = SnowPadSwitchAgent(repo=repo)

    # 1. High-uncertainty casual whim
    whim = agent.analyze_chat_message(
        text="What if we add confetti animations and neon badges to the checkout screen?",
        user_id="U_JORDAN_SLACK",
        channel="#frontend-chatter",
    )
    assert whim is not None
    assert whim["signal_type"] == "CASUAL_WHIM"
    assert whim["uncertainty_pct"] >= 70
    assert whim["scope_status"] == "OUTSIDE_CIRCLE"

    # 2. Low-uncertainty verified proposal
    prop = agent.analyze_chat_message(
        text="Proposing batch settlement query optimization: benchmarked p95 latency reduction of 120ms, PR #42 ready",
        user_id="U_MAYA_SLACK",
        channel="#product-ideas",
    )
    assert prop is not None
    assert prop["uncertainty_pct"] <= 35
    assert prop["scope_status"] == "INSIDE_CIRCLE"

    # 3. Normal chatter (ignored)
    ignore = agent.analyze_chat_message(
        text="Good morning team, let me know when standup starts.",
        user_id="U_ALEX_SLACK",
        channel="#general",
    )
    assert ignore is None


def test_agent_handle_slash_commands(repo: SnowPadRepository) -> None:
    """Verify agent handles slash commands correctly."""
    agent = SnowPadSwitchAgent(repo=repo)

    radar_res = agent.handle_command("/snowpad radar", user_id="U_ALEX_SLACK")
    assert radar_res["type"] == "radar_summary"
    assert radar_res["total"] >= 7

    sync_res = agent.handle_command("/snowpad sync slack", user_id="U_ALEX_SLACK")
    assert sync_res["type"] == "sync_result"
    assert len(sync_res["members"]) >= 4
