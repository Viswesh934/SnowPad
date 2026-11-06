"""Unit tests for the live sandbox replay and one-click deliverable exports."""

from pathlib import Path
import pytest
from snowpad.agent.sandbox import DiscordSandbox
from snowpad.db.connection import init_db
from snowpad.db.repository import SnowPadRepository
from snowpad.db.seeder import seed_demo_data
from snowpad.reports.generator import DeliverableGenerator


@pytest.fixture
def repo(tmp_path: Path) -> SnowPadRepository:
    """Fixture providing clean temp DuckDB repository."""
    db_file = tmp_path / "test_deliv.duckdb"
    r = SnowPadRepository(db_path=str(db_file))
    init_db(db_path=db_file)
    seed_demo_data(r)
    return r


def test_sandbox_setup_and_audit(repo: SnowPadRepository) -> None:
    """Verify sandbox sets up members and audits incoming chatter."""
    sandbox = DiscordSandbox(repo=repo)
    sandbox.setup_sandbox_environment()

    # Verify actors are synced
    actors = repo.get_all_actors()
    assert len(actors) >= 4

    # Process a whim message
    sandbox.process_simulated_message(
        user_name="Jordan Lee",
        designation="Frontend Dev",
        channel="#frontend-chatter",
        text="Wouldn't it be cute if confetti burst on checkout?",
    )

    # Verify DuckDB recorded it as outside circle / parked
    signals = repo.get_circle_radar_data()
    whim = next((s for s in signals if "confetti" in s["title"].lower()), None)
    assert whim is not None
    assert whim["scope_status"] == "OUTSIDE_CIRCLE"


def test_generate_presentation_slides(repo: SnowPadRepository, tmp_path: Path) -> None:
    """Verify on-demand Reveal.js presentation generation."""
    gen = DeliverableGenerator(repo=repo)
    slide_file = gen.generate_presentation_slides(actor_id="maya_patel", quarter="Q4-2026")

    assert slide_file.exists()
    content = slide_file.read_text(encoding="utf-8")
    assert "Maya Patel" in content
    assert "Circle of Scope Alignment" in content
    assert "Reveal.initialize" in content


def test_generate_prd_specification(repo: SnowPadRepository) -> None:
    """Verify on-demand Sprint Refactor PRD generation from DuckDB debates."""
    gen = DeliverableGenerator(repo=repo)
    prd_file = gen.generate_prd_specification()

    assert prd_file.exists()
    content = prd_file.read_text(encoding="utf-8")
    assert "# SnowPad Sprint Refactor PRD" in content


def test_generate_all_actor_slides(repo: SnowPadRepository) -> None:
    """Verify batch generation of executive slide decks for all team members."""
    gen = DeliverableGenerator(repo=repo)
    slide_files = gen.generate_all_actor_slides(quarter="Q4-2026")

    assert len(slide_files) >= 4
    for sf in slide_files:
        assert sf.exists()
        content = sf.read_text(encoding="utf-8")
        assert "Reveal.initialize" in content


def test_generate_all_actor_wrapped(repo: SnowPadRepository) -> None:
    """Verify batch generation of Spotify-Wrapped stories for all team members."""
    from snowpad.reports.wrapped import generate_all_actor_wrapped

    wrapped_files = generate_all_actor_wrapped(repo, quarter="Q4-2026")
    assert len(wrapped_files) >= 4
    for wf in wrapped_files:
        assert wf.exists()
        content = wf.read_text(encoding="utf-8")
        assert "SnowPad Wrapped" in content
        assert "max-w-[860px]" in content

