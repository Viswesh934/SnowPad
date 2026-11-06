"""Unit tests for the autonomous background scope scheduler."""

from pathlib import Path
import pytest
from snowpad.core.scheduler import ScopeScheduler, INTERVAL_PRESETS
from snowpad.db.connection import init_db
from snowpad.db.repository import SnowPadRepository
from snowpad.db.seeder import seed_demo_data


@pytest.fixture
def repo(tmp_path: Path) -> SnowPadRepository:
    """Fixture providing clean temp DuckDB repository."""
    db_file = tmp_path / "test_sched.duckdb"
    r = SnowPadRepository(db_path=str(db_file))
    init_db(db_path=db_file)
    seed_demo_data(r)
    return r


def test_scheduler_audit_cycle(repo: SnowPadRepository) -> None:
    """Verify single audit cycle refreshes metrics, PRD, slides, and wrapped stories."""
    scheduler = ScopeScheduler(repo=repo)
    report = scheduler.run_audit_cycle(quarter="Q4-2026")

    assert report["cycle_id"] == 1
    assert report["inside_circle_count"] >= 1
    assert report["slide_count"] >= 4
    assert report["wrapped_count"] >= 4
    assert Path(report["prd_path"]).exists()
    assert "SnowPad Scope Pulse" in report["standup_summary"]


def test_scheduler_commands_generation(repo: SnowPadRepository) -> None:
    """Verify crontab and Windows task scheduler specs generation."""
    scheduler = ScopeScheduler(repo=repo)
    
    # Weekly test
    weekly_cmd = scheduler.get_schedule_commands("weekly")
    assert weekly_cmd["cron_expression"] == "0 9 * * 1"
    assert "snowpad.cli schedule --once" in weekly_cmd["linux_mac_crontab"]
    assert "schtasks" in weekly_cmd["windows_task_cmd"]

    # Biweekly test
    biweekly_cmd = scheduler.get_schedule_commands("biweekly")
    assert biweekly_cmd["cron_expression"] == "0 9 * * 1,4"


def test_scheduler_daemon_loop(repo: SnowPadRepository) -> None:
    """Verify daemon executes specified cycles and triggers callback."""
    scheduler = ScopeScheduler(repo=repo)
    recorded = []

    scheduler.run_daemon(
        interval_mode="demo",
        custom_interval_sec=0.01,
        max_cycles=2,
        on_cycle_complete=lambda r: recorded.append(r)
    )

    assert len(recorded) == 2
    assert recorded[0]["cycle_id"] == 1
    assert recorded[1]["cycle_id"] == 2
