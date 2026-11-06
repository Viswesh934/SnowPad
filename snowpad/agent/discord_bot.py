"""Live Discord Bot client for SnowPad with JIT dependency provisioning."""

import os
import sys
import subprocess
from typing import Optional

from snowpad.agent.sync import sync_workspace_members
from snowpad.db.repository import SnowPadRepository


def ensure_discord_dependency() -> None:
    """Dynamically installs discord.py on demand if not present (Zero-Bloat Core)."""
    try:
        import discord
    except ImportError:
        print("\n⬇️ [SnowPad JIT] Dynamically provisioning discord.py dependency on-demand...")
        import shutil
        if shutil.which("uv"):
            cmd = ["uv", "pip", "install", "discord.py>=2.3.0"]
        else:
            cmd = [sys.executable, "-m", "pip", "install", "discord.py>=2.3.0"]
        subprocess.check_call(cmd)
        print("✔ [SnowPad JIT] discord.py successfully provisioned!\n")


def start_discord_bot(token: Optional[str] = None, guild_id: Optional[str] = None) -> None:
    """Initializes and runs the live Discord bot listener."""
    ensure_discord_dependency()
    import discord

    bot_token = token or os.getenv("DISCORD_BOT_TOKEN")
    target_guild_id = guild_id or os.getenv("DISCORD_GUILD_ID")

    if not bot_token:
        print("[SnowPad Error] DISCORD_BOT_TOKEN is not set.")
        print("Please add your token to a .env file or pass it via: python -m snowpad.cli listen --platform discord --token <TOKEN>")
        sys.exit(1)

    repo = SnowPadRepository()
    from snowpad.agent.bot import SnowPadSwitchAgent
    agent = SnowPadSwitchAgent(repo=repo)

    intents = discord.Intents.default()
    intents.members = True
    intents.message_content = True

    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f"\n❄️ SnowPad Discord Agent logged in as: {client.user} (ID: {client.user.id})")
        print(f"Connected to {len(client.guilds)} server(s).")

        # Automatically sync members and designations into DuckDB on boot
        if target_guild_id:
            try:
                members = sync_workspace_members(
                    platform="discord",
                    repo=repo,
                    token=bot_token,
                    guild_id=target_guild_id,
                )
                print(f"✔ Auto-synced {len(members)} Discord members and designations into DuckDB.")
            except Exception as e:
                print(f"[Warning] Member auto-sync encountered an issue: {e}")

        print("Listening for chat proposals, whimsical ideas, and commands (!snowpad radar, !snowpad review)...\n")

    @client.event
    async def on_message(message: discord.Message):
        if message.author.bot:
            return

        content = message.content.strip()
        channel_name = f"#{message.channel.name}" if hasattr(message.channel, "name") else "#direct-message"
        author_id = str(message.author.id)

        # 1. Handle Slash / Prefix Commands
        if content.startswith("!snowpad") or content.startswith("/snowpad"):
            cmd = content.replace("!", "/").strip()
            res = agent.handle_command(cmd, user_id=author_id, channel=channel_name)

            embed = discord.Embed(
                title="❄️ SnowPad Scope Assistant",
                color=0xFF5A36,  # Warm Coral
            )

            if res["type"] == "radar_summary":
                embed.description = f"**Total Signals:** {res['total']} tracked in DuckDB"
                embed.add_field(name="🟢 Inside Circle (Core)", value=str(res["inside_count"]), inline=True)
                embed.add_field(name="🟡 In Debate", value=str(res["debates_count"]), inline=True)
                embed.add_field(name="🔴 Parked Whims", value=str(res["whims_count"]), inline=True)
                embed.set_footer(text="Open radar.html for the live animated 360° sweep")

            elif res["type"] == "sync_result":
                embed.description = res["message"]
                member_list = "\n".join([f"• **{m['name']}** — *{m['role']}*" for m in res["members"][:8]])
                embed.add_field(name="Synced Designations", value=member_list, inline=False)

            elif res["type"] == "review_dossier":
                embed.title = f"❄️ Performance Dossier: {res['actor_name']}"
                embed.description = f"**Designation:** {res['role']}\n**Verdict:** {res['verdict']}\n\n{res['focus_summary']}"
                m = res["metrics"]
                embed.add_field(name="Confirmed Features", value=str(m.get("confirmed_features", 0)), inline=True)
                embed.add_field(name="Whims Quarantined", value=str(m.get("whims_quarantined", 0)), inline=True)
                embed.add_field(name="Scope Focus Ratio", value=f"{m.get('circle_focus_percentage', 0)}%", inline=True)
            else:
                embed.description = res.get("message", "Ready to assist.")

            await message.reply(embed=embed)
            return

        # 2. Analyze spontaneous chat messages for proposals & whims
        analysis = agent.analyze_chat_message(
            text=content,
            user_id=author_id,
            channel=channel_name,
        )

        if analysis:
            # Look up member's designation from DuckDB
            actor = repo.get_actor_by_id(author_id)
            actor_name = actor["name"] if actor else message.author.display_name
            designation = actor["role"] if actor else "Contributor"

            status = analysis["scope_status"]
            color = 0xFF5A36 if status == "INSIDE_CIRCLE" else 0xEAB308 if status == "BORDERLINE" else 0x848995

            embed = discord.Embed(
                title=f"❄️ SnowPad: {analysis['signal_type'].replace('_', ' ').title()} Detected",
                description=f"*{content}*",
                color=color,
            )
            embed.add_field(name="Contributor", value=f"**{actor_name}** ({designation})", inline=True)
            embed.add_field(name="Uncertainty Rating", value=f"**{analysis['uncertainty_pct']}%**", inline=True)
            embed.add_field(name="Scope Horizon", value=f"`{status}`", inline=True)
            embed.add_field(name="Action Taken", value=f"Logged to DuckDB as `{analysis['resolution']}`", inline=False)

            if status == "OUTSIDE_CIRCLE":
                embed.set_footer(text="Quarantined outside circle to protect sprint focus.")
            elif status == "INSIDE_CIRCLE":
                embed.set_footer(text="Approved inside circle moving core SLAs.")
            else:
                embed.set_footer(text="Under debate: leadership decision required.")

            await message.reply(embed=embed)

    try:
        client.run(bot_token)
    except Exception as e:
        print(f"[SnowPad Discord Error] Could not connect: {e}")
