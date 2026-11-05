"""SnowPad Command Line Interface for developer performance reviews and scope radar."""

import argparse
import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from snowpad.config import settings
from snowpad.core.analytics import build_developer_review_dossier, build_weekly_pulse_digest
from snowpad.db.connection import init_db
from snowpad.db.repository import SnowPadRepository
from snowpad.db.seeder import seed_demo_data

console = Console()


def cmd_seed(args: argparse.Namespace) -> None:
    """Initialize schema and seed realistic demo events."""
    repo = SnowPadRepository()
    console.print(f"[bold cyan]❄️ Initializing DuckDB at:[/] {settings.db_path}")
    seed_demo_data(repo)
    console.print("[bold green]✔ Successfully seeded DuckDB with actors, hotfixes, and telemetry metrics![/]")


def cmd_weekly(args: argparse.Namespace) -> None:
    """Print weekly operational pulse for team standups and manager syncs."""
    repo = SnowPadRepository()
    digest = build_weekly_pulse_digest(repo)

    console.print(Panel(
        f"[bold yellow]🎯 Total Contributors:[/] {digest['total_active_contributors']}  |  "
        f"[bold green]Inside Circle (High-Leverage):[/] {digest['inside_circle_count']}  |  "
        f"[bold red]Outside Circle (Churn):[/] {digest['outside_circle_count']}  |  "
        f"[bold magenta]Tracked Tech Debt:[/] {digest['active_debt_count']}",
        title="[bold cyan]❄️ SnowPad: Weekly Operational Pulse[/]",
        border_style="cyan"
    ))

    # Weekly team table
    table = Table(title="Weekly Breakdown by Developer", header_style="bold magenta")
    table.add_column("Week", style="dim")
    table.add_column("Developer", style="bold white")
    table.add_column("Role", style="cyan")
    table.add_column("Total Events", justify="right")
    table.add_column("Hotfixes", justify="right", style="yellow")
    table.add_column("Inside Circle", justify="right", style="green")
    table.add_column("Outside Circle", justify="right", style="red")
    table.add_column("Tech Debt Logged", justify="right", style="magenta")
    table.add_column("Avg Latency Delta", justify="right")

    for row in digest["weekly_breakdown"]:
        delta = row.get("avg_latency_delta_ms") or 0.0
        delta_str = f"[green]{delta} ms[/]" if delta < 0 else f"[red]+{delta} ms[/]" if delta > 0 else "0.0 ms"
        table.add_row(
            str(row["pulse_week"])[:10],
            row["actor_name"],
            row["actor_role"],
            str(row["total_events"]),
            str(row["hotfixes_count"]),
            str(row["inside_circle_count"]),
            str(row["outside_circle_count"]),
            str(row["tech_debt_logged"]),
            delta_str,
        )

    console.print(table)


def cmd_review(args: argparse.Namespace) -> None:
    """Generate and display an individual developer performance review dossier."""
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
        f"[bold]Circle of Scope Alignment:[/] {dossier['focus_summary']}",
        title="[bold cyan]❄️ SnowPad: Developer Performance Review Dossier[/]",
        border_style="green"
    ))

    # Metrics Summary Table
    m_table = Table(title="Quantified Impact Ledger (DuckDB)", header_style="bold cyan")
    m_table.add_column("Metric", style="white")
    m_table.add_column("Value", style="bold yellow", justify="right")

    m_table.add_row("Total Contributions Logged", str(metrics.get("total_contributions", 0)))
    m_table.add_row("Hotfixes Shipped (Under Fire)", str(metrics.get("hotfixes_shipped", 0)))
    m_table.add_row("Proactive Performance Optimizations", str(metrics.get("perf_optimizations", 0)))
    m_table.add_row("Inside Circle (Strategic Focus)", str(metrics.get("high_impact_circle_count", 0)))
    m_table.add_row("Outside Circle (Ad-Hoc Churn)", str(metrics.get("low_leverage_churn_count", 0)))
    m_table.add_row("Circle Focus Ratio", f"{metrics.get('circle_focus_percentage', 0)}%")
    m_table.add_row("Total Latency Shaved", f"[green]-{metrics.get('total_ms_shaved', 0)} ms[/]")
    m_table.add_row("Tracked Tech Debt Items", f"[magenta]{metrics.get('debt_items_incurred', 0)}[/]")

    console.print(m_table)

    # Recommendations Panel
    if dossier["recommendations"]:
        rec_text = "\n".join([f"• {rec}" for rec in dossier["recommendations"]])
        console.print(Panel(rec_text, title="[bold yellow]Manager Action Items & Recommendations[/]", border_style="yellow"))


def cmd_radar(args: argparse.Namespace) -> None:
    """Print the Circle of Scope Radar view with items inside vs outside."""
    repo = SnowPadRepository()
    items = repo.get_circle_radar_data()

    table = Table(title="❄️ SnowPad: Circle of Scope Radar", header_style="bold cyan")
    table.add_column("Scope Distance", justify="right", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Service", style="white")
    table.add_column("Title", style="white")
    table.add_column("Author", style="magenta")
    table.add_column("Tech Debt", justify="center")
    table.add_column("Latency Impact", justify="right")

    for item in items:
        status_color = "green" if item["scope_status"] == "INSIDE_CIRCLE" else "red"
        status_str = f"[{status_color}]{item['scope_status']}[/]"
        debt_str = f"[bold magenta]{item['tech_debt_severity']}[/]" if item["tech_debt_flag"] else "[dim]NONE[/]"
        lat = item.get("latency_delta_ms", 0.0)
        lat_str = f"[green]{lat} ms[/]" if lat < 0 else f"[red]+{lat} ms[/]" if lat > 0 else "0 ms"

        table.add_row(
            f"{item['scope_distance']:.2f}",
            status_str,
            item["service_name"],
            item["title"],
            item["actor_name"],
            debt_str,
            lat_str,
        )

    console.print(table)


def app() -> None:
    """Main CLI entrypoint."""
    parser = argparse.ArgumentParser(
        prog="snowpad",
        description="SnowPad - Developer Impact & Tech Debt OS with Circle-of-Scope Intelligence"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Seed
    subparsers.add_parser("seed", help="Initialize schema and seed realistic demo data")

    # Weekly
    subparsers.add_parser("weekly", help="Display weekly operational pulse")

    # Review
    review_p = subparsers.add_parser("review", help="Display developer performance review dossier")
    review_p.add_argument("--actor", required=True, help="Actor ID (e.g. alex_chen, maya_patel)")
    review_p.add_argument("--quarter", default="Q4-2026", help="Reporting quarter (default: Q4-2026)")

    # Radar
    subparsers.add_parser("radar", help="Display Circle of Scope radar")

    args = parser.parse_args()

    if args.command == "seed":
        cmd_seed(args)
    elif args.command == "weekly":
        cmd_weekly(args)
    elif args.command == "review":
        cmd_review(args)
    elif args.command == "radar":
        cmd_radar(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    app()
