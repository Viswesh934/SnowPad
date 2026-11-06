"""Interactive Discord Sandbox and Live Replay Engine for SnowPad demonstrations."""

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from snowpad.agent.bot import SnowPadSwitchAgent
from snowpad.agent.sync import sync_workspace_members
from snowpad.config import BASE_DIR, settings
from snowpad.db.repository import SnowPadRepository

console = Console()
SIGNALS_JSON_PATH = BASE_DIR / "snowpad" / "web" / "signals.json"


def update_web_signals_json(repo: SnowPadRepository) -> None:
    """Exports current radar signals to JSON so radar.html can live-sync."""
    items = repo.get_circle_radar_data()
    SIGNALS_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SIGNALS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(items, f, default=str, indent=2)


class DiscordSandbox:
    """Simulates a live Discord server with channels and realistic team discussions."""

    def __init__(self, repo: Optional[SnowPadRepository] = None):
        self.repo = repo or SnowPadRepository()
        self.agent = SnowPadSwitchAgent(repo=self.repo)

    def setup_sandbox_environment(self) -> None:
        """Pre-populates simulated Discord guild members and designations."""
        sync_workspace_members(platform="discord", repo=self.repo)
        update_web_signals_json(self.repo)

    def process_simulated_message(self, user_name: str, designation: str, channel: str, text: str) -> None:
        """Simulates an incoming message from a member and triggers SnowPad audit."""
        # Print simulated Discord message header
        console.print(f"\n[dim]{channel}[/] [bold white]{user_name}[/] [dim]({designation}):[/]")
        console.print(f"  [italic #FAF8F5]\"{text}\"[/]")

        # Run SnowPad analysis
        analysis = self.agent.analyze_chat_message(text=text, user_id=user_name.lower().replace(" ", "_"), channel=channel)

        if analysis:
            status = analysis["scope_status"]
            color = "#FF5A36" if status == "INSIDE_CIRCLE" else "#EAB308" if status == "BORDERLINE" else "#848995"
            unc = analysis["uncertainty_pct"]

            panel_content = (
                f"[bold white]{analysis['title']}[/]\n"
                f"[dim]Type:[/] [magenta]{analysis['signal_type']}[/]  |  "
                f"[dim]Uncertainty:[/] [{color}]{unc}%[/{color}]  |  "
                f"[dim]Scope Horizon:[/] [{color}]{status}[/{color}]\n"
                f"[bold cyan]Action:[/] Tracked on Radar as [bold]{analysis['resolution']}[/]"
            )

            console.print(Panel(
                panel_content,
                title=f"[bold {color}]❄️ SnowPad Scope Audit[/]",
                border_style=color,
                padding=(0, 2)
            ))
            update_web_signals_json(self.repo)
        else:
            console.print("  [dim]• SnowPad: Standard banter, no scope signal detected.[/]")

    def run_live_replay(self, speed_delay: float = 1.8) -> None:
        """Plays a realistic, scripted sequence of team discussions across Discord channels."""
        self.setup_sandbox_environment()

        console.print(Panel(
            "[bold #FF5A36]SnowPad Live Discord Replay Simulator[/]\n"
            "[dim]Simulating real-time chatter across #product-ideas, #backend-core, and #frontend-chatter...[/]\n"
            "[dim]Open snowpad/web/radar.html in your browser to watch live radar blips appear![/]",
            border_style="#FF5A36"
        ))

        timeline = [
            {
                "user": "Maya Patel",
                "role": "Principal Product Architect",
                "channel": "#product-ideas",
                "text": "Proposing Batched Settlement Engine: benchmarked p95 latency drops by 120ms on Stripe batching, PR ready.",
            },
            {
                "user": "Alex Chen",
                "role": "Staff Backend Engineer",
                "channel": "#backend-core",
                "text": "Proposing Redis Redlock on /checkout: row-level PostgreSQL locks were causing 504 timeouts in peak tests.",
            },
            {
                "user": "Sam Torres",
                "role": "Product Lead",
                "channel": "#growth-experiments",
                "text": "What if we deprecate multi-step onboarding wizard for 1-click social sign-in? Might boost conversion by 18%.",
            },
            {
                "user": "Jordan Lee",
                "role": "Frontend Dev",
                "channel": "#frontend-chatter",
                "text": "Wouldn't it be cute if confetti burst on checkout? Thinking of adding a quick Lottie animation this afternoon.",
            },
            {
                "user": "Alex Chen",
                "role": "Staff Backend Engineer",
                "channel": "#backend-core",
                "text": "Good morning team, standup at 10 AM.",
            },
            {
                "user": "Jordan Lee",
                "role": "Frontend Dev",
                "channel": "#frontend-chatter",
                "text": "Thinking of redesigning the internal admin drawer with a custom neon dark theme.",
            },
        ]

        for step in timeline:
            time.sleep(speed_delay)
            self.process_simulated_message(
                user_name=step["user"],
                designation=step["role"],
                channel=step["channel"],
                text=step["text"],
            )

        console.print(f"\n[bold green]✔ Replay sequence complete![/] All signals, uncertainty scores, and radar positions recorded.")
        console.print(f"[dim]Run 'python -m snowpad.cli radar' or inspect snowpad/web/radar.html to view the updated scope horizon.[/]\n")

    def run_interactive_shell(self) -> None:
        """Interactive shell allowing user to send messages as any team member."""
        self.setup_sandbox_environment()

        console.print(Panel(
            "[bold #FF5A36]❄️ SnowPad Interactive Discord Sandbox[/]\n"
            "Type messages as any team member and watch SnowPad audit scope and uncertainty live.\n"
            "Commands: type [bold yellow]'exit'[/] to quit, or [bold yellow]'/snowpad radar'[/] to view current radar stats.",
            border_style="#FF5A36"
        ))

        channels = ["#product-ideas", "#backend-core", "#growth-experiments", "#frontend-chatter"]
        users = [
            ("Maya Patel", "Product Architect"),
            ("Alex Chen", "Staff Backend Engineer"),
            ("Sam Torres", "Product Lead"),
            ("Jordan Lee", "Frontend Dev"),
        ]

        current_channel = channels[0]
        current_user, current_role = users[0]

        while True:
            try:
                prompt_str = f"[{current_channel}] {current_user} > "
                user_input = input(prompt_str).strip()

                if not user_input:
                    continue

                if user_input.lower() in ["exit", "quit", "q"]:
                    console.print("[dim]Exiting sandbox.[/]")
                    break

                if user_input.startswith("/channel"):
                    parts = user_input.split()
                    if len(parts) > 1 and parts[1] in channels:
                        current_channel = parts[1]
                        console.print(f"[dim]Switched to channel: {current_channel}[/]")
                    else:
                        console.print(f"[yellow]Available channels: {channels}[/]")
                    continue

                if user_input.startswith("/user"):
                    parts = user_input.split()
                    if len(parts) > 1:
                        target = parts[1].lower()
                        match = next((u for u in users if target in u[0].lower()), None)
                        if match:
                            current_user, current_role = match
                            console.print(f"[dim]Switched user to: {current_user} ({current_role})[/]")
                        else:
                            console.print(f"[yellow]Available users: {[u[0] for u in users]}[/]")
                    continue

                # Process command or message
                if user_input.startswith("/snowpad"):
                    res = self.agent.handle_command(user_input, user_id=current_user.lower().replace(" ", "_"), channel=current_channel)
                    console.print(Panel(str(res), title="[bold green]SnowPad Command Result[/]", border_style="green"))
                else:
                    self.process_simulated_message(current_user, current_role, current_channel, user_input)

            except (KeyboardInterrupt, EOFError):
                break

