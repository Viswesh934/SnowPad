"""SnowPad Command Line Interface for chat uncertainty radar and performance reviews."""

import argparse
import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from snowpad.config import settings
from snowpad.core.analytics import build_developer_review_dossier, build_weekly_pulse_digest
from snowpad.db.repository import SnowPadRepository
from snowpad.db.seeder import seed_demo_data

console = Console()


def cmd_seed(args: argparse.Namespace) -> None:
    """Initialize schema and seed realistic chat signals."""
    repo = SnowPadRepository()
    console.print(f"[bold cyan]❄️ Initializing DuckDB at:[/] {settings.db_path}")
    seed_demo_data(repo)
    console.print("[bold green]✔ Successfully seeded DuckDB with actors, chat signals, and telemetry metrics![/]")


def cmd_weekly(args: argparse.Namespace) -> None:
    """Print weekly operational pulse for team standups and manager syncs."""
    repo = SnowPadRepository()
    digest = build_weekly_pulse_digest(repo)

    console.print(Panel(
        f"[bold yellow]🎯 Active Contributors:[/] {digest['total_active_contributors']}  |  "
        f"[bold green]Inside Circle (Confirmed):[/] {digest['inside_circle_count']}  |  "
        f"[bold yellow]Borderline (In Debate):[/] {digest['borderline_count']}  |  "
        f"[bold red]Outside Circle (Parked Whims):[/] {digest['outside_circle_count']}",
        title="[bold cyan]❄️ SnowPad: Weekly Chat Uncertainty & Scope Pulse[/]",
        border_style="cyan"
    ))

    # Weekly team table
    table = Table(title="Weekly Breakdown by Contributor", header_style="bold magenta")
    table.add_column("Week", style="dim")
    table.add_column("Contributor", style="bold white")
    table.add_column("Role", style="cyan")
    table.add_column("Total Signals", justify="right")
    table.add_column("Features", justify="right", style="green")
    table.add_column("Whims", justify="right", style="red")
    table.add_column("Inside Circle", justify="right", style="green")
    table.add_column("Outside Circle", justify="right", style="red")
    table.add_column("Avg Uncertainty", justify="right", style="yellow")

    for row in digest["weekly_breakdown"]:
        unc = row.get("avg_uncertainty") or 0.0
        table.add_row(
            str(row["pulse_week"])[:10],
            row["actor_name"],
            row["actor_role"],
            str(row["total_signals"]),
            str(row["features_count"]),
            str(row["whims_count"]),
            str(row["inside_circle_count"]),
            str(row["outside_circle_count"]),
            f"{int(unc * 100)}%",
        )

    console.print(table)


def cmd_review(args: argparse.Namespace) -> None:
    """Generate and display an individual contributor performance review dossier."""
    repo = SnowPadRepository()
    actor_id = args.actor

    try:
        dossier = build_developer_review_dossier(actor_id=actor_id, repo=repo, quarter=args.quarter)
    except ValueError as e:
        console.print(f"[bold red]Error:[/] {e}")
        actors = repo.get_all_actors()
        console.print(f"Available actors: {[a['id'] for a in actors]}")
        sys.exit(1)

    actor = dossier["actor"]
    metrics = dossier["impact_metrics"]

    console.print(Panel(
        f"[bold white]{actor['name']}[/] ({actor['role']}) - [dim]{actor['team']}[/]\n"
        f"[bold yellow]Quarter:[/] {dossier['quarter']}\n"
        f"[bold cyan]Verdict:[/] [bold green]{dossier['verdict']}[/]\n"
        f"[bold]Scope Alignment:[/] {dossier['focus_summary']}",
        title="[bold cyan]❄️ SnowPad: Contributor Impact & Performance Dossier[/]",
        border_style="green"
    ))

    # Metrics Summary Table
    m_table = Table(title="Quantified Impact Ledger (DuckDB)", header_style="bold cyan")
    m_table.add_column("Metric", style="white")
    m_table.add_column("Value", style="bold yellow", justify="right")

    m_table.add_row("Total Signals Logged", str(metrics.get("total_contributions", 0)))
    m_table.add_row("Confirmed Features Delivered", str(metrics.get("confirmed_features", 0)))
    m_table.add_row("Off-Scope Whims Quarantined", str(metrics.get("whims_quarantined", 0)))
    m_table.add_row("Inside Circle (Strategic Focus)", str(metrics.get("high_impact_circle_count", 0)))
    m_table.add_row("Outside Circle (Parked Chatter)", str(metrics.get("low_leverage_churn_count", 0)))
    m_table.add_row("Circle Focus Ratio", f"{metrics.get('circle_focus_percentage', 0)}%")
    m_table.add_row("Average Uncertainty Score", f"{int((metrics.get('avg_uncertainty') or 0.0) * 100)}%")
    m_table.add_row("Total Latency Shaved", f"[green]-{metrics.get('total_ms_shaved', 0)} ms[/]")

    console.print(m_table)

    # Recommendations Panel
    if dossier["recommendations"]:
        rec_text = "\n".join([f"• {rec}" for rec in dossier["recommendations"]])
        console.print(Panel(rec_text, title="[bold yellow]Manager Action Items & Recommendations[/]", border_style="yellow"))


def cmd_radar(args: argparse.Namespace) -> None:
    """Print the Circle of Scope Radar view with items inside vs outside."""
    repo = SnowPadRepository()
    items = repo.get_circle_radar_data()

    table = Table(title="❄️ SnowPad: Circle of Scope Radar (Chat Signals)", header_style="bold cyan")
    table.add_column("Scope Distance", justify="right", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Type", style="magenta")
    table.add_column("Channel", style="dim")
    table.add_column("Title", style="white")
    table.add_column("Author", style="cyan")
    table.add_column("Uncertainty", justify="center")
    table.add_column("Resolution", style="yellow")

    for item in items:
        status = item["scope_status"]
        status_color = "green" if status == "INSIDE_CIRCLE" else "yellow" if status == "BORDERLINE" else "red"
        status_str = f"[{status_color}]{status}[/]"
        unc = int(item["uncertainty_score"] * 100)
        unc_str = f"[green]{unc}%[/]" if unc < 40 else f"[yellow]{unc}%[/]" if unc < 70 else f"[red]{unc}%[/]"

        table.add_row(
            f"{item['scope_distance']:.2f}",
            status_str,
            item["signal_type"],
            item["origin_channel"],
            item["title"][:40] + ("..." if len(item["title"]) > 40 else ""),
            item["actor_name"],
            unc_str,
            item["resolution"],
        )

    console.print(table)


def cmd_chatter(args: argparse.Namespace) -> None:
    """Print chat channel chatter breakdown."""
    repo = SnowPadRepository()
    channels = repo.get_channel_chatter()

    table = Table(title="❄️ SnowPad: Channel Chatter Breakdown", header_style="bold cyan")
    table.add_column("Channel", style="bold white")
    table.add_column("Total Signals", justify="right")
    table.add_column("Avg Uncertainty", justify="right", style="yellow")
    table.add_column("Inside Circle", justify="right", style="green")
    table.add_column("Outside Circle", justify="right", style="red")
    table.add_column("Pending Debates", justify="right", style="cyan")

    for ch in channels:
        table.add_row(
            ch["origin_channel"],
            str(ch["total_signals"]),
            f"{int(ch['avg_uncertainty'] * 100)}%",
            str(ch["inside_circle_count"]),
            str(ch["outside_circle_count"]),
            str(ch["pending_debates"]),
        )

    console.print(table)


def app() -> None:
    """Main CLI entrypoint."""
    parser = argparse.ArgumentParser(
        prog="snowpad",
        description="SnowPad - Developer Impact & Chat Uncertainty OS with Circle-of-Scope Intelligence"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    subparsers.add_parser("seed", help="Initialize schema and seed realistic chat signals")
    subparsers.add_parser("weekly", help="Display weekly chat uncertainty pulse")

    review_p = subparsers.add_parser("review", help="Display contributor performance review dossier")
    review_p.add_argument("--actor", required=True, help="Actor ID (e.g. alex_chen, maya_patel)")
    review_p.add_argument("--quarter", default="Q4-2026", help="Reporting quarter (default: Q4-2026)")

    subparsers.add_parser("radar", help="Display Circle of Scope radar")
    subparsers.add_parser("chatter", help="Display channel chatter breakdown")

    args = parser.parse_args()

    if args.command == "seed":
        cmd_seed(args)
    elif args.command == "weekly":
        cmd_weekly(args)
    elif args.command == "review":
        cmd_review(args)
    elif args.command == "radar":
        cmd_radar(args)
    elif args.command == "chatter":
        cmd_chatter(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    app()
