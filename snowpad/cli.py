"""SnowPad Command Line Interface for chat uncertainty radar and performance reviews."""

import argparse
import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from snowpad.config import settings
from snowpad.core.analytics import build_developer_review_dossier, build_weekly_pulse_digest
from snowpad.core.flow import build_feature_flows, get_signal_journey
from snowpad.db.repository import SnowPadRepository
from snowpad.db.seeder import seed_demo_data
from snowpad.reports.wrapped import build_wrapped_data, generate_actor_wrapped, generate_team_wrapped, generate_all_actor_wrapped

console = Console()


def cmd_seed(args: argparse.Namespace) -> None:
    """Initialize schema and seed realistic chat signals."""
    repo = SnowPadRepository()
    console.print(f"[bold cyan]❄️ Initializing SnowPad Scope Memory at:[/] {settings.db_path}")
    seed_demo_data(repo)
    generate_team_wrapped(repo)
    generate_all_actor_wrapped(repo)
    from snowpad.reports.generator import DeliverableGenerator
    DeliverableGenerator().generate_all_actor_slides()
    console.print("[bold green]✔ Successfully loaded workspace data with team members, chat signals, and scope metrics![/]")


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
    m_table = Table(title="Team Impact & Focus Ledger", header_style="bold cyan")
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


def cmd_sync(args: argparse.Namespace) -> None:
    """Fetch and sync members & designations from Slack or Discord into SnowPad."""
    from snowpad.agent.sync import sync_workspace_members

    repo = SnowPadRepository()
    platform = args.platform
    console.print(f"[bold cyan]❄️ Fetching members & designations from {platform.title()}...[/]")

    members = sync_workspace_members(platform=platform, repo=repo)

    table = Table(title=f"Connected {platform.title()} Team Members", header_style="bold magenta")
    table.add_column("ID", style="dim")
    table.add_column("Name", style="bold white")
    table.add_column("Designation / Role", style="green")
    table.add_column("Team / Server", style="cyan")

    for m in members:
        table.add_row(m.id, m.name, m.role, m.team)

    console.print(table)
    console.print(f"[bold green]✔ Successfully connected {len(members)} team members with designations into SnowPad![/]")


def cmd_msg(args: argparse.Namespace) -> None:
    """Simulate or process an incoming chat message from Slack/Discord."""
    from snowpad.agent.bot import SnowPadSwitchAgent

    agent = SnowPadSwitchAgent()
    text = args.text
    user = args.user
    channel = args.channel

    console.print(f"[bold cyan]Incoming Message in {channel}:[/] [white]'{text}'[/] from [magenta]{user}[/]")

    if text.startswith("/snowpad"):
        res = agent.handle_command(text, user_id=user, channel=channel)
        console.print(Panel(str(res), title="[bold green]SnowPad Scope Assistant[/]", border_style="green"))
    else:
        res = agent.analyze_chat_message(text, user_id=user, channel=channel)
        if res:
            color = "green" if res["scope_status"] == "INSIDE_CIRCLE" else "yellow" if res["scope_status"] == "BORDERLINE" else "red"
            console.print(Panel(
                f"[bold white]Title:[/] {res['title']}\n"
                f"[bold]Type:[/] [magenta]{res['signal_type']}[/]\n"
                f"[bold]Uncertainty Rating:[/] [{color}]{res['uncertainty_pct']}%[/{color}]\n"
                f"[bold]Scope Status:[/] [{color}]{res['scope_status']}[/{color}]\n"
                f"[bold]Resolution Action:[/] [cyan]{res['resolution']}[/]",
                title="[bold cyan]❄️ SnowPad Chat Signal Intercepted & Scoped[/]",
                border_style="cyan"
            ))
        else:
            console.print("[dim]Message ignored (no proposal or whim detected).[/]")


def cmd_listen(args: argparse.Namespace) -> None:
    """Start live bot listener for Discord or Slack."""
    platform = args.platform.lower()
    if platform == "discord":
        from snowpad.agent.discord_bot import start_discord_bot
        console.print("[bold cyan]❄️ Starting SnowPad Discord Bot Listener...[/]")
        start_discord_bot(token=args.token, guild_id=args.guild)
    else:
        console.print(f"[bold yellow]Platform '{platform}' is coming soon. Use '--platform discord' for live bot.[/]")


def cmd_demo(args: argparse.Namespace) -> None:
    """Run simulated Discord sandbox or live automated replay for demo videos."""
    from snowpad.agent.sandbox import DiscordSandbox

    sandbox = DiscordSandbox()
    if args.interactive:
        sandbox.run_interactive_shell()
    else:
        sandbox.run_live_replay(speed_delay=args.delay)


def cmd_export(args: argparse.Namespace) -> None:
    """Generate executive Reveal.js slide decks or PRD specifications on-demand."""
    from snowpad.reports.generator import DeliverableGenerator

    gen = DeliverableGenerator()
    actor_id = args.actor
    quarter = args.quarter
    export_all = getattr(args, "all", False)

    if args.prd:
        console.print("[bold cyan]❄️ Generating Sprint Refactor PRD from active scope debates...[/]")
        prd_file = gen.generate_prd_specification()
        console.print(f"[bold green]✔ Generated Sprint PRD:[/] {prd_file}")

    if export_all:
        console.print("[bold cyan]❄️ Generating Reveal.js Executive Slide Decks for all contributors...[/]")
        paths = gen.generate_all_actor_slides(quarter=quarter)
        for p in paths:
            console.print(f"[bold green]✔ Generated Slide Deck:[/] {p}")

    elif actor_id:
        console.print(f"[bold cyan]❄️ Generating Reveal.js Executive Slide Deck for:[/] {actor_id}...")
        slide_file = gen.generate_presentation_slides(actor_id=actor_id, quarter=quarter)
        console.print(f"[bold green]✔ Generated Slide Deck:[/] {slide_file}")
        console.print(f"[dim]Run: start {slide_file} to present in your browser.[/]")

    if not args.prd and not actor_id and not export_all:
        console.print("[yellow]Please specify '--actor <id>', '--all', or '--prd' for sprint specification.[/]")


def cmd_flow(args: argparse.Namespace) -> None:
    """Display feature lifecycle flow charts showing where signals originated and landed."""
    repo = SnowPadRepository()
    signal_filter = getattr(args, "signal", None)
    actor_filter = getattr(args, "actor", None)
    channel_filter = getattr(args, "channel", None)

    if signal_filter:
        journey = get_signal_journey(repo, signal_filter)
        if not journey:
            console.print(f"[bold red]Signal '{signal_filter}' not found.[/]")
            return
        flows = [journey]
    else:
        flows = build_feature_flows(repo, actor_id=actor_filter, channel=channel_filter)

    tree = Tree("[bold cyan]❄️ SnowPad: Feature Lifecycle Journey & Scope Traceability[/]")

    for f in flows:
        status = f["scope_status"]
        color = "green" if status == "INSIDE_CIRCLE" else "yellow" if status == "BORDERLINE" else "red"

        f_node = tree.add(f"[{color}]● {f['title']}[/] [dim]({f['signal_id']})[/]")
        stages = f["stages"]
        f_node.add(f"[dim]1. Origin Channel:[/] [magenta]{stages[0]['channel']}[/] by [bold white]{stages[0]['author']}[/] ({stages[0]['signal_type']})")
        f_node.add(f"[dim]2. Ray Audit:[/] [{color}]{stages[1]['uncertainty_pct']}% Uncertainty[/] [dim]({stages[1]['confidence_label']} • {stages[1]['sla_check']})[/]")
        f_node.add(f"[dim]3. Circle Horizon:[/] [{color}]{stages[2]['scope_status']}[/] [dim]({stages[2]['zone_label']} • Distance: {f['scope_distance']:.2f})[/]")
        f_node.add(f"[dim]4. Resolution:[/] [cyan]{stages[3]['resolution_label']}[/] [dim]➔ Destination: {stages[3]['destination']}[/]")
        f_node.add(f"[dim]5. Business Impact:[/] [bold {color}]{stages[4]['impact_summary']}[/]")

    console.print(tree)
    console.print("\n[dim]Interactive visual flowchart available at:[/] [bold #FF5A36]snowpad/web/flow.html[/]")
    console.print("[dim]Run: 'start snowpad/web/flow.html' to inspect animated pipeline paths.[/]\n")


def cmd_wrapped(args: argparse.Namespace) -> None:
    """Generate and display Spotify-Wrapped style quarterly celebration."""
    repo = SnowPadRepository()
    actor_id = getattr(args, "actor", None)
    quarter = getattr(args, "quarter", "Q4-2026")

    wrapped = build_wrapped_data(repo, actor_id=actor_id, quarter=quarter)
    actor = wrapped["actor"]
    arch = wrapped["archetype"]
    cj = wrapped["crown_jewel"]
    db = wrapped["dodged_bullet"]

    # Generate HTML file
    if actor_id:
        out_html = generate_actor_wrapped(repo, actor_id=actor_id, quarter=quarter)
    else:
        out_html = generate_team_wrapped(repo, quarter=quarter)

    # Print Spotify Wrapped terminal experience
    console.print(Panel(
        f"[bold #10B981]❄️ SNOWPAD WRAPPED: {quarter.upper()}[/]\n"
        f"[bold white]{actor['name']}[/] [dim]({actor['role']} • {actor['team']})[/]\n\n"
        f"🎯 [bold]Scope Archetype:[/] [bold {arch['aura_color']}]{arch['name']} {arch['emoji']}[/]\n"
        f"   [italic #FAFAFA]\"{arch['description']}\"[/]\n\n"
        f"📊 [bold]Circle Focus Ratio:[/] [bold green]{wrapped['focus_pct']}%[/]\n"
        f"⚡ [bold]Latency Shaved:[/] [bold green]-{wrapped['total_ms_shaved']} ms[/] on core endpoints\n"
        f"🛡️ [bold]Sanity Shielded:[/] [bold green]+{wrapped['hours_shielded']} hours[/] preserved from unverified churn\n"
        f"💬 [bold]Top Sparring Arena:[/] [bold cyan]{wrapped['top_channel']}[/] ({wrapped['top_channel_count']} proposals)\n\n"
        f"🏆 [bold]Crown Jewel Victory:[/] [bold white]{cj['title']}[/]\n"
        f"   [dim]{cj['impact']}[/]\n\n"
        f"🚫 [bold]The Dodged Bullet:[/] [bold red]{db['title']}[/]\n"
        f"   [dim]{db['risk']} (+{db['hours_saved']}h dev sanity saved)[/]\n\n"
        f"🎧 [bold]Sprint Soundtrack:[/] [dim]{arch['soundtrack']}[/]",
        title=f"[bold #10B981]🎁 SnowPad Wrapped {quarter}[/]",
        border_style="#10B981",
        padding=(1, 2)
    ))

    console.print(f"[bold green]✔ Interactive Spotify Wrapped Story Generated:[/] {out_html}")
    console.print(f"[dim]Run: start {out_html} to experience your full-screen animated story deck![/]\n")


def cmd_schedule(args: argparse.Namespace) -> None:
    """Run autonomous background schedule for scope audits and deliverable generation."""
    from snowpad.core.scheduler import ScopeScheduler

    scheduler = ScopeScheduler()
    interval = args.interval
    quarter = args.quarter

    if args.cron:
        cmds = scheduler.get_schedule_commands(interval_mode=interval)
        console.print(Panel(
            f"[bold #10B981]📅 SnowPad Scheduled Automation Helper[/]\n\n"
            f"[bold white]Schedule:[/] {cmds['interval_label']}\n"
            f"[dim]{cmds['description']}[/]\n\n"
            f"⏱️ [bold white]Standard Cron:[/] [bold cyan]{cmds['cron_expression']}[/]\n\n"
            f"🐧 [bold #10B981]Linux / macOS Crontab Entry:[/] \n[dim]{cmds['linux_mac_crontab']}[/]\n\n"
            f"🪟 [bold #10B981]Windows Task Scheduler Command:[/] \n[dim]{cmds['windows_task_cmd']}[/]\n\n"
            f"🤖 [bold #10B981]Agentic Slash Command:[/] \n[cyan]{cmds['agentic_slash_command']}[/]\n\n"
            f"⚡ [bold #10B981]Background Daemon CLI:[/] \n[green]{cmds['background_daemon_cmd']}[/]",
            title="[bold green]❄️ SnowPad Automation Spec[/]",
            border_style="#10B981"
        ))
        return

    if args.once:
        console.print("[bold cyan]❄️ Executing on-demand Scope Audit cycle...[/]")
        report = scheduler.run_audit_cycle(quarter=quarter)
        console.print(Panel(
            f"[bold green]✔ Scope Audit Completed in {report['elapsed_seconds']}s[/]\n\n"
            f"• [bold]Confirmed Milestones:[/] [green]{report['inside_circle_count']}[/]\n"
            f"• [bold]Pending Debates:[/] [yellow]{report['pending_debates_count']}[/]\n"
            f"• [bold]Parked Whims:[/] [dim]{report['outside_circle_count']}[/]\n"
            f"• [bold]Updated Slide Decks:[/] {report['slide_count']} files in dist/\n"
            f"• [bold]Updated Sprint PRD:[/] {report['prd_path']}\n"
            f"• [bold]Updated Wrapped Stories:[/] {report['wrapped_count']} files in dist/\n\n"
            f"[dim]{report['standup_summary']}[/]",
            title="[bold green]❄️ SnowPad Scheduled Audit Report[/]",
            border_style="#10B981"
        ))
        return

    # Run daemon loop
    custom_sec = args.seconds if args.seconds else None
    scheduler.run_daemon(interval_mode=interval, custom_interval_sec=custom_sec, max_cycles=args.max_cycles)


def cmd_bridge(args: argparse.Namespace) -> None:
    """Run standard stdio listener for Switch Console and Switch Room message streaming."""
    from snowpad.agent.switch_bridge import SwitchBridge
    bridge = SwitchBridge()
    bridge.run_stdio_loop()


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

    # Sync members command
    sync_p = subparsers.add_parser("sync", help="Sync members and designations from Slack or Discord")
    sync_p.add_argument("--platform", default="slack", choices=["slack", "discord"], help="Chat platform (slack or discord)")

    # Message analysis command
    msg_p = subparsers.add_parser("msg", help="Analyze a chat message for scope & uncertainty")
    msg_p.add_argument("--text", required=True, help="Chat message text")
    msg_p.add_argument("--user", default="U_MAYA_SLACK", help="User ID or handle")
    msg_p.add_argument("--channel", default="#product-ideas", help="Origin channel")

    # Live listen command
    listen_p = subparsers.add_parser("listen", help="Start live chat listener on Discord or Slack")
    listen_p.add_argument("--platform", default="discord", choices=["discord", "slack"], help="Platform (default: discord)")
    listen_p.add_argument("--token", default=None, help="Bot Token override")
    listen_p.add_argument("--guild", default=None, help="Discord Guild/Server ID override")

    # Demo & Sandbox command
    demo_p = subparsers.add_parser("demo", help="Run simulated Discord sandbox or live replay for screen recording")
    demo_p.add_argument("--interactive", action="store_true", help="Launch interactive shell where you can type messages")
    demo_p.add_argument("--delay", type=float, default=1.5, help="Delay between replayed messages in seconds (default: 1.5s)")

    # Export command
    export_p = subparsers.add_parser("export", help="Export Reveal.js executive slides or sprint refactor PRD")
    export_p.add_argument("--actor", default=None, help="Actor ID to generate review slides for (e.g. maya_patel, alex_chen)")
    export_p.add_argument("--all", action="store_true", help="Generate executive slide decks for all team members")
    export_p.add_argument("--quarter", default="Q4-2026", help="Reporting quarter (default: Q4-2026)")
    export_p.add_argument("--prd", action="store_true", help="Generate Sprint Refactor PRD specification")

    # Flow command
    flow_p = subparsers.add_parser("flow", help="Display feature lifecycle flow charts and traceability")
    flow_p.add_argument("--signal", default=None, help="Filter by Signal ID (e.g. sig_feat_001)")
    flow_p.add_argument("--actor", default=None, help="Filter by Actor ID (e.g. maya_patel)")
    flow_p.add_argument("--channel", default=None, help="Filter by Channel (e.g. #product-ideas)")

    # Wrapped command
    wrapped_p = subparsers.add_parser("wrapped", help="Generate Spotify-Wrapped style quarterly celebration")
    wrapped_p.add_argument("--actor", default=None, help="Actor ID (leave empty for collective team wrapped)")
    wrapped_p.add_argument("--quarter", default="Q4-2026", help="Reporting quarter (default: Q4-2026)")

    # Schedule command (Autonomous Background Pulse & Deliverables)
    schedule_p = subparsers.add_parser("schedule", help="Autonomous background scheduler for weekly/biweekly scope audits")
    schedule_p.add_argument("--interval", default="weekly", choices=["weekly", "biweekly", "daily", "demo"], help="Audit frequency (default: weekly)")
    schedule_p.add_argument("--once", action="store_true", help="Run a single audit cycle immediately and exit")
    schedule_p.add_argument("--cron", action="store_true", help="Print OS Crontab / Task Scheduler / Slash Command strings")
    schedule_p.add_argument("--seconds", type=float, default=None, help="Custom sleep interval in seconds (for testing)")
    schedule_p.add_argument("--max-cycles", type=int, default=None, help="Maximum daemon cycles before stopping (optional)")
    schedule_p.add_argument("--quarter", default="Q4-2026", help="Reporting quarter (default: Q4-2026)")

    # Switch Bridge command (for Switch Console / stdio orchestration)
    subparsers.add_parser("bridge", help="Run Switch Console stdio/JSON stream bridge")

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
    elif args.command == "sync":
        cmd_sync(args)
    elif args.command == "msg":
        cmd_msg(args)
    elif args.command == "listen":
        cmd_listen(args)
    elif args.command == "demo":
        cmd_demo(args)
    elif args.command == "export":
        cmd_export(args)
    elif args.command == "flow":
        cmd_flow(args)
    elif args.command == "wrapped":
        cmd_wrapped(args)
    elif args.command == "schedule":
        cmd_schedule(args)
    elif args.command == "bridge":
        cmd_bridge(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    app()
