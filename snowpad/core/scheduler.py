"""Autonomous Scope Scheduler - Background agentic auditor for weekly pulses and scope governance."""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from snowpad.config import BASE_DIR, settings
from snowpad.core.analytics import build_weekly_pulse_digest
from snowpad.db.repository import SnowPadRepository
from snowpad.reports.generator import DeliverableGenerator
from snowpad.reports.wrapped import generate_all_actor_wrapped, generate_team_wrapped

console = Console()

INTERVAL_PRESETS = {
    "weekly": {
        "seconds": 7 * 24 * 3600,
        "label": "Once a week (Monday Standup Pulse)",
        "cron": "0 9 * * 1",
        "description": "Runs every Monday at 9:00 AM before team sprint planning."
    },
    "biweekly": {
        "seconds": 3.5 * 24 * 3600,
        "label": "Twice a week (Monday Kickoff + Thursday Mid-Sprint Audit)",
        "cron": "0 9 * * 1,4",
        "description": "Runs Mondays and Thursdays at 9:00 AM to catch mid-sprint scope creep."
    },
    "daily": {
        "seconds": 24 * 3600,
        "label": "Daily Standup Scope Radar",
        "cron": "0 9 * * 1-5",
        "description": "Runs every weekday at 9:00 AM for daily async standup syncs."
    },
    "demo": {
        "seconds": 15,
        "label": "Demo Pulse Mode (15-second loop)",
        "cron": "* * * * *",
        "description": "High-velocity testing mode for live demos and screen recordings."
    }
}


class ScopeScheduler:
    """Autonomous background agentic scheduler for SnowPad scope radar and deliverables."""

    def __init__(self, repo: Optional[SnowPadRepository] = None):
        self.repo = repo or SnowPadRepository()
        self.generator = DeliverableGenerator(repo=self.repo)
        self.run_history: List[Dict[str, Any]] = []

    def run_audit_cycle(self, quarter: str = "Q4-2026") -> Dict[str, Any]:
        """Executes a single autonomous scope audit cycle:
        1. Analyzes chat uncertainty & scope ledger
        2. Computes weekly pulse digest
        3. Refreshes web radar JSON feed (snowpad/web/signals.json)
        4. Regenerates Sprint Refactor PRD (dist/sprint_refactor_prd.md)
        5. Refreshes all team Reveal.js slide decks (dist/*_q4_review.html)
        6. Updates collective & contributor Wrapped stories (dist/*_wrapped.html)
        """
        start_time = datetime.now()
        timestamp_str = start_time.strftime("%Y-%m-%d %H:%M:%S")

        # 1. Weekly pulse metrics
        digest = build_weekly_pulse_digest(self.repo)

        # 2. Sync web radar feed (snowpad/web/signals.json)
        radar_items = self.repo.get_circle_radar_data()
        web_json_path = BASE_DIR / "snowpad" / "web" / "signals.json"
        try:
            with open(web_json_path, "w", encoding="utf-8") as f:
                json.dump(radar_items, f, indent=2, default=str)
        except Exception:
            pass

        # 3. Generate sprint refactor PRD
        prd_path = self.generator.generate_prd_specification()

        # 4. Refresh executive slide decks for all team members
        slide_paths = self.generator.generate_all_actor_slides(quarter=quarter)

        # 5. Refresh wrapped stories
        team_wrapped = generate_team_wrapped(self.repo, quarter=quarter)
        actor_wrapped = generate_all_actor_wrapped(self.repo, quarter=quarter)

        elapsed_sec = round((datetime.now() - start_time).total_seconds(), 2)

        report = {
            "cycle_id": len(self.run_history) + 1,
            "timestamp": timestamp_str,
            "elapsed_seconds": elapsed_sec,
            "active_contributors": digest["total_active_contributors"],
            "total_signals": digest["total_recorded_signals"],
            "inside_circle_count": digest["inside_circle_count"],
            "borderline_count": digest["borderline_count"],
            "outside_circle_count": digest["outside_circle_count"],
            "pending_debates_count": digest["pending_debates_count"],
            "prd_path": str(prd_path),
            "slide_count": len(slide_paths),
            "wrapped_count": len(actor_wrapped) + 1,
            "standup_summary": (
                f"❄️ SnowPad Scope Pulse ({timestamp_str})\n"
                f"• Active Scope: {digest['inside_circle_count']} confirmed milestones\n"
                f"• Open Debates: {digest['pending_debates_count']} active RFC discussions\n"
                f"• Protected Dev Time: {digest['outside_circle_count']} off-scope whims quarantined\n"
                f"• Updated Artifacts: Sprint PRD, {len(slide_paths)} slide decks, and Wrapped stories."
            )
        }

        self.run_history.append(report)
        return report

    def get_schedule_commands(self, interval_mode: str = "weekly") -> Dict[str, str]:
        """Generates exact crontab, Windows Task Scheduler, and CLI commands for automated runs."""
        preset = INTERVAL_PRESETS.get(interval_mode, INTERVAL_PRESETS["weekly"])
        cron_expr = preset["cron"]
        python_exe = sys.executable
        cli_path = (BASE_DIR / "snowpad" / "cli.py").resolve()

        return {
            "interval_label": preset["label"],
            "cron_expression": cron_expr,
            "description": preset["description"],
            "linux_mac_crontab": f"{cron_expr} cd \"{BASE_DIR}\" && \"{python_exe}\" -m snowpad.cli schedule --once >> \"{BASE_DIR}/snowpad_audit.log\" 2>&1",
            "windows_task_cmd": (
                f'schtasks /create /tn "SnowPad-Pulse-{interval_mode}" '
                f'/tr "\"{python_exe}\" -m snowpad.cli schedule --once" '
                f'/sc {"weekly /d MON" if interval_mode == "weekly" else "daily"} /st 09:00 /f'
            ),
            "background_daemon_cmd": f'python -m snowpad.cli schedule --interval {interval_mode}',
            "agentic_slash_command": f'/schedule CronExpression="{cron_expr}" Prompt="Run SnowPad Scope Audit Cycle and publish weekly pulse"'
        }

    def run_daemon(
        self,
        interval_mode: str = "weekly",
        custom_interval_sec: Optional[float] = None,
        max_cycles: Optional[int] = None,
        on_cycle_complete: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> None:
        """Starts an autonomous continuous agentic daemon loop running at specified intervals."""
        preset = INTERVAL_PRESETS.get(interval_mode, INTERVAL_PRESETS["weekly"])
        sleep_sec = custom_interval_sec if custom_interval_sec is not None else preset["seconds"]

        console.print(Panel(
            f"[bold #10B981]❄️ SnowPad Autonomous Scope Scheduler Active[/]\n\n"
            f"📅 [bold white]Schedule Mode:[/] [bold green]{interval_mode.upper()}[/] ({preset['label']})\n"
            f"⏱️ [bold white]Interval:[/] Every {sleep_sec:,.0f} seconds\n"
            f"🎯 [bold white]Workflow:[/] Auto-audits chat signals, computes weekly pulse, refreshes PRD & slide decks\n"
            f"🛑 [dim]Press Ctrl+C anytime to stop daemon.[/]",
            title="[bold green]SnowPad Background Agent[/]",
            border_style="#10B981"
        ))

        cycle_count = 0
        try:
            while True:
                cycle_count += 1
                console.print(f"\n[bold cyan]▶ [{datetime.now().strftime('%H:%M:%S')}] Triggering Scope Audit Cycle #{cycle_count}...[/]")
                
                report = self.run_audit_cycle()

                # Print cycle outcome
                table = Table(title=f"Cycle #{cycle_count} Scope Telemetry", border_style="#27272A", header_style="bold green")
                table.add_column("Confirmed Scope", justify="center", style="green")
                table.add_column("Open Debates", justify="center", style="yellow")
                table.add_column("Parked Whims", justify="center", style="#A1A1AA")
                table.add_column("Updated Slides", justify="center", style="white")
                table.add_column("Execution Time", justify="right", style="dim")

                table.add_row(
                    f"{report['inside_circle_count']} items",
                    f"{report['pending_debates_count']} RFCs",
                    f"{report['outside_circle_count']} whims",
                    f"{report['slide_count']} decks",
                    f"{report['elapsed_seconds']}s"
                )
                console.print(table)
                console.print(f"[bold green]✔ Standup Brief ready:[/] [dim]{report['standup_summary'].splitlines()[1]}[/]")

                if on_cycle_complete:
                    on_cycle_complete(report)

                if max_cycles and cycle_count >= max_cycles:
                    console.print(f"\n[bold green]✔ Completed requested {max_cycles} scheduled audit cycle(s). Exiting daemon.[/]")
                    break

                console.print(f"[dim]Next scheduled audit in {sleep_sec:,.0f}s. Sleeping in background...[/]")
                time.sleep(sleep_sec)

        except KeyboardInterrupt:
            console.print("\n[bold yellow]Scheduler stopped by user (Ctrl+C). Workspace memory and deliverables preserved.[/]")
