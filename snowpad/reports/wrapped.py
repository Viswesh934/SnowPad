"""SnowPad Wrapped - Quarterly Spotify-Wrapped style celebration of focus, achievements, and dodged whims."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from snowpad.config import BASE_DIR
from snowpad.db.repository import SnowPadRepository

DIST_DIR = BASE_DIR / "dist"
DIST_DIR.mkdir(parents=True, exist_ok=True)


def build_wrapped_data(repo: SnowPadRepository, actor_id: Optional[str] = None, quarter: str = "Q4-2026") -> Dict[str, Any]:
    """Computes quarterly Wrapped metrics, personality archetype, dodged bullets, and crown jewels."""
    all_actors = repo.get_all_actors()
    radar = repo.get_circle_radar_data()
    channels = repo.get_channel_chatter()

    if actor_id:
        actor = repo.get_actor_by_id(actor_id)
        if not actor:
            actor = {"id": actor_id, "name": actor_id.replace("_", " ").title(), "role": "Contributor", "team": "Engineering"}
        actor_radar = repo.get_circle_radar_data(actor_id=actor_id)
    else:
        actor = {
            "id": "team_all",
            "name": "The Entire Engineering & Product Team",
            "role": "Collective Workspace",
            "team": "Unified Product Squads",
        }
        actor_radar = radar

    inside_items = [r for r in actor_radar if r["scope_status"] == "INSIDE_CIRCLE"]
    borderline_items = [r for r in actor_radar if r["scope_status"] == "BORDERLINE"]
    outside_items = [r for r in actor_radar if r["scope_status"] == "OUTSIDE_CIRCLE"]

    total_signals = len(actor_radar)
    confirmed_count = len(inside_items)
    whims_count = len(outside_items)
    debates_count = len(borderline_items)

    focus_pct = round((confirmed_count / total_signals * 100.0), 1) if total_signals > 0 else 100.0

    # Total latency shaved
    total_ms_shaved = 0.0
    for item in actor_radar:
        delta = item.get("latency_delta_ms", 0.0) or 0.0
        if delta < 0:
            total_ms_shaved += abs(delta)
    total_ms_shaved = round(total_ms_shaved, 1)

    # Hours of focus shielded: 1 whim = ~17 developer hours saved from unverified churn
    hours_shielded = whims_count * 17 if whims_count > 0 else 0

    # Top channel
    ch_counts: Dict[str, int] = {}
    for item in actor_radar:
        ch = item.get("origin_channel", "#general")
        ch_counts[ch] = ch_counts.get(ch, 0) + 1
    top_channel = max(ch_counts.items(), key=lambda x: x[1])[0] if ch_counts else "#product-ideas"
    top_channel_count = ch_counts.get(top_channel, 0)

    # Crown Jewel (Top feature inside circle)
    if inside_items:
        best_feat = inside_items[0]
        crown_jewel = {
            "title": best_feat.get("title", "Core SLA Delivery"),
            "channel": best_feat.get("origin_channel", "#product-ideas"),
            "impact": best_feat.get("estimated_kpi_impact") or f"Shaved {total_ms_shaved}ms latency",
            "uncertainty_pct": int(best_feat.get("uncertainty_score", 0.15) * 100),
        }
    else:
        crown_jewel = {
            "title": "Clean Backlog Execution",
            "channel": "#product-ideas",
            "impact": "Maintained 100% sprint fidelity",
            "uncertainty_pct": 10,
        }

    # Dodged Bullet (Top whim quarantined outside circle)
    if outside_items:
        top_whim = outside_items[0]
        dodged_bullet = {
            "title": top_whim.get("title", "Spontaneous UI animation"),
            "channel": top_whim.get("origin_channel", "#frontend-chatter"),
            "risk": top_whim.get("estimated_kpi_impact") or "High bundle bloat & zero proven conversion",
            "hours_saved": 34,
        }
    else:
        dodged_bullet = {
            "title": "Random Midnight Rewrites",
            "channel": "#general",
            "risk": "Avoided unapproved architecture rewrites",
            "hours_saved": 24,
        }

    # Determine Scope Personality Archetype
    if total_ms_shaved >= 50.0 and focus_pct >= 70.0:
        archetype = {
            "name": "The Laser Architect",
            "emoji": "🎯",
            "tagline": "Zero Fluff. Precision Execution.",
            "description": "You treat p95 latency like a personal vendetta. When you speak in chat, PRs merge and response times plummet.",
            "aura_color": "#10B981",
            "aura_secondary": "#059669",
            "soundtrack": "Lo-Fi Beats to Refactor Payment Microservices To",
        }
    elif whims_count >= 2:
        archetype = {
            "name": "The Sprint Guardian",
            "emoji": "🛡️",
            "tagline": "The Shield Against Scope Creep.",
            "description": "When spontaneous midnight whims threaten the sprint, you stand your ground. You saved the team over 40 hours of aimless churn.",
            "aura_color": "#10B981",
            "aura_secondary": "#047857",
            "soundtrack": "Epic Orchestral with Noise-Cancelling Headphones",
        }
    elif debates_count >= 1:
        archetype = {
            "name": "The Systems Philosopher",
            "emoji": "🧠",
            "tagline": "The Master of Trade-offs.",
            "description": "Why rush when we can analyze the CAP theorem? You ask the tough questions that prevent 3 AM production fires.",
            "aura_color": "#FFFFFF",
            "aura_secondary": "#A1A1AA",
            "soundtrack": "Ambient Synthwave & Whiteboard Squeaks",
        }
    else:
        archetype = {
            "name": "The Velocity Catalyst",
            "emoji": "⚡",
            "tagline": "Curious, Fast, and Unstoppable.",
            "description": "You spark new ideas and keep discussions moving forward while staying inside the team's circle of scope.",
            "aura_color": "#10B981",
            "aura_secondary": "#34D399",
            "soundtrack": "Upbeat Hyperpop Sprint Velocity",
        }

    return {
        "quarter": quarter,
        "actor": actor,
        "total_signals": total_signals,
        "confirmed_count": confirmed_count,
        "whims_count": whims_count,
        "debates_count": debates_count,
        "focus_pct": focus_pct,
        "total_ms_shaved": total_ms_shaved,
        "hours_shielded": hours_shielded,
        "top_channel": top_channel,
        "top_channel_count": top_channel_count,
        "crown_jewel": crown_jewel,
        "dodged_bullet": dodged_bullet,
        "archetype": archetype,
    }


def generate_wrapped_html(data: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
    """Generates an interactive, mobile/desktop Spotify-Wrapped story deck."""
    actor = data["actor"]
    quarter = data["quarter"]
    arch = data["archetype"]
    cj = data["crown_jewel"]
    db = data["dodged_bullet"]

    if not output_path:
        slug = actor.get("id", "team")
        output_path = DIST_DIR / f"{slug}_{quarter.lower().replace('-', '_')}_wrapped.html"

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>SnowPad Wrapped: {actor['name']} ({quarter})</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700;800&family=Plus+Jakarta+Sans:wght@400;600;700;800;900&display=swap" rel="stylesheet">
  <style>
    body {{
      font-family: 'Plus Jakarta Sans', sans-serif;
      background-color: #0b0c0e;
      color: #FAF8F5;
      overflow: hidden;
      touch-action: manipulation;
    }}
    .mono {{ font-family: 'JetBrains Mono', monospace; }}
    
    /* Radial pulsing glow behind story card */
    .story-card {{
      background: linear-gradient(180deg, rgba(26, 28, 35, 0.95) 0%, rgba(14, 15, 18, 0.98) 100%);
      border: 1px solid rgba(255, 255, 255, 0.1);
      box-shadow: 0 25px 60px -15px rgba(0, 0, 0, 0.8), 0 0 80px -20px {arch['aura_color']}40;
    }}

    .progress-bar {{
      transition: width 0.1s linear;
    }}
    
    .floating-badge {{
      animation: float 4s ease-in-out infinite;
    }}
    @keyframes float {{
      0%, 100% {{ transform: translateY(0px) rotate(0deg); }}
      50% {{ transform: translateY(-8px) rotate(1deg); }}
    }}
  </style>
</head>
<body class="flex items-center justify-center min-h-screen p-0 sm:p-4 bg-gradient-to-br from-[#0c0d10] via-[#121318] to-[#0a0a0d]">

  <!-- Mobile/Desktop Story Container -->
  <div class="relative w-full max-w-[440px] h-[100dvh] sm:h-[840px] sm:max-h-[92vh] sm:rounded-3xl story-card flex flex-col overflow-hidden select-none">
    
    <!-- Top Progress Bars (6 cards) -->
    <div class="absolute top-0 left-0 right-0 p-4 z-30 flex items-center gap-1.5 bg-gradient-to-b from-black/80 via-black/40 to-transparent">
      <div class="flex-1 h-1 bg-white/20 rounded-full overflow-hidden">
        <div id="bar-0" class="h-full bg-white progress-bar w-0"></div>
      </div>
      <div class="flex-1 h-1 bg-white/20 rounded-full overflow-hidden">
        <div id="bar-1" class="h-full bg-white progress-bar w-0"></div>
      </div>
      <div class="flex-1 h-1 bg-white/20 rounded-full overflow-hidden">
        <div id="bar-2" class="h-full bg-white progress-bar w-0"></div>
      </div>
      <div class="flex-1 h-1 bg-white/20 rounded-full overflow-hidden">
        <div id="bar-3" class="h-full bg-white progress-bar w-0"></div>
      </div>
      <div class="flex-1 h-1 bg-white/20 rounded-full overflow-hidden">
        <div id="bar-4" class="h-full bg-white progress-bar w-0"></div>
      </div>
      <div class="flex-1 h-1 bg-white/20 rounded-full overflow-hidden">
        <div id="bar-5" class="h-full bg-white progress-bar w-0"></div>
      </div>
    </div>

    <!-- Top User Badge & Close Button -->
    <div class="absolute top-7 left-0 right-0 px-4 z-30 flex items-center justify-between text-xs font-mono text-white/80">
      <div class="flex items-center gap-2">
        <span class="w-6 h-6 rounded-full bg-[#10B981] text-black flex items-center justify-center font-bold text-[11px]">❄</span>
        <span class="font-bold tracking-tight text-white">{actor['name']}</span>
        <span class="text-white/40">•</span>
        <span class="text-[#10B981]">{quarter}</span>
      </div>
      <div class="flex items-center gap-2">
        <button id="pauseBtn" class="px-2 py-0.5 rounded-full bg-white/10 hover:bg-white/20 text-white/70 transition">Pause</button>
      </div>
    </div>

    <!-- Tap Navigation Zones (Left 35% prev, Right 65% next) -->
    <div class="absolute inset-0 z-20 flex">
      <div id="tapLeft" class="w-[35%] h-full cursor-w-resize"></div>
      <div id="tapRight" class="w-[65%] h-full cursor-e-resize"></div>
    </div>

    <!-- SLIDES CONTAINER -->
    <div class="relative flex-1 flex items-center justify-center p-6 text-center z-10">

      <!-- SLIDE 0: Welcome & Vibe Check -->
      <div id="slide-0" class="slide absolute inset-0 p-8 flex flex-col justify-between opacity-100 transition-opacity duration-300">
        <div class="mt-14 text-left">
          <span class="text-xs font-mono uppercase tracking-widest text-[#10B981] font-bold">SnowPad Presents</span>
          <h1 class="text-4xl font-extrabold tracking-tight mt-1 text-white leading-tight">
            Your {quarter}<br>Scope Wrapped.
          </h1>
          <p class="text-sm text-[#A1A1AA] mt-2">
            90 days of chatting, building, debating, and dodging scope drift.
          </p>
        </div>

        <div class="my-auto flex flex-col items-center">
          <div class="w-32 h-32 rounded-3xl bg-[#121214] border border-[#10B981]/40 flex items-center justify-center text-6xl shadow-2xl shadow-green-500/10 floating-badge">
            ❄️
          </div>
          <div class="mt-6 flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/5 border border-white/10 text-xs font-mono text-[#D4D4D8]">
            <span class="w-2 h-2 rounded-full bg-[#10B981] animate-ping"></span>
            <span>{data['total_signals']} Chat Discussions Audited</span>
          </div>
        </div>

        <div class="mb-4 text-center">
          <p class="text-xs font-mono text-[#71717A]">Tap right to uncover your scope personality &rarr;</p>
        </div>
      </div>

      <!-- SLIDE 1: Top Channel & Chat Habit -->
      <div id="slide-1" class="slide absolute inset-0 p-8 flex flex-col justify-between opacity-0 pointer-events-none transition-opacity duration-300">
        <div class="mt-14 text-left">
          <span class="text-xs font-mono uppercase tracking-widest text-[#EAB308] font-bold">The Daily Hangout</span>
          <h2 class="text-3xl font-extrabold text-white mt-1">Your Favorite Sparring Ground</h2>
        </div>

        <div class="my-auto flex flex-col items-center text-center">
          <div class="text-6xl mb-4">💬</div>
          <span class="text-sm font-mono text-[#A49E94] uppercase tracking-wider">Top Origin Channel</span>
          <h3 class="text-3xl font-black text-[#FAF8F5] mt-1 font-mono">{data['top_channel']}</h3>
          <p class="text-sm text-[#D8D4CB] mt-3 max-w-[280px]">
            Where you dropped <strong class="text-[#FF7A45]">{data['top_channel_count']} proposals</strong> and brainstormed with teammates this quarter.
          </p>
        </div>

        <div class="mb-4 bg-white/5 border border-white/10 rounded-2xl p-4 text-left">
          <span class="text-xs font-mono text-[#A49E94]">Circle Focus Alignment:</span>
          <div class="flex items-center justify-between mt-1">
            <span class="text-2xl font-black font-mono text-[#10B981]">{data['focus_pct']}%</span>
            <span class="text-xs text-[#D8D4CB]">Inside Circle Commitments</span>
          </div>
        </div>
      </div>

      <!-- SLIDE 2: Scope Personality Archetype -->
      <div id="slide-2" class="slide absolute inset-0 p-8 flex flex-col justify-between opacity-0 pointer-events-none transition-opacity duration-300">
        <div class="mt-14 text-left">
          <span class="text-xs font-mono uppercase tracking-widest text-[#FF7A45] font-bold">Scope Identity</span>
          <h2 class="text-3xl font-extrabold text-white mt-1">Your Q4 Archetype</h2>
        </div>

        <div class="my-auto flex flex-col items-center">
          <div class="w-24 h-24 rounded-3xl flex items-center justify-center text-5xl shadow-2xl floating-badge" style="background: radial-gradient(circle, {arch['aura_color']}40 0%, #16171b 100%); border: 2px solid {arch['aura_color']};">
            {arch['emoji']}
          </div>
          <h3 class="text-2xl font-black text-white mt-4 tracking-tight">{arch['name']}</h3>
          <span class="text-xs font-mono font-semibold px-3 py-1 rounded-full mt-1" style="background: {arch['aura_color']}20; color: {arch['aura_color']};">
            {arch['tagline']}
          </span>
          <p class="text-xs text-[#D8D4CB] mt-4 leading-relaxed max-w-[300px]">
            "{arch['description']}"
          </p>
        </div>

        <div class="mb-4 bg-white/5 border border-white/10 rounded-2xl p-3.5 text-left flex items-center gap-3">
          <span class="text-2xl">🎧</span>
          <div>
            <span class="text-[10px] font-mono text-[#A49E94] uppercase">Your Sprint Vibe</span>
            <p class="text-xs font-semibold text-white truncate max-w-[240px]">{arch['soundtrack']}</p>
          </div>
        </div>
      </div>

      <!-- SLIDE 3: The Dodged Bullet (Top Whim Quarantined) -->
      <div id="slide-3" class="slide absolute inset-0 p-8 flex flex-col justify-between opacity-0 pointer-events-none transition-opacity duration-300">
        <div class="mt-14 text-left">
          <span class="text-xs font-mono uppercase tracking-widest text-[#10B981] font-bold">Focus Shield</span>
          <h2 class="text-3xl font-extrabold text-white mt-1">The Bullet You Dodged</h2>
        </div>

        <div class="my-auto flex flex-col items-center">
          <div class="w-20 h-20 rounded-full bg-[#10B981]/10 border border-[#10B981]/40 flex items-center justify-center text-4xl mb-3">
            🛡️
          </div>
          <span class="text-xs font-mono text-[#10B981] uppercase tracking-wider font-bold">Whim Safely Quarantined</span>
          <h3 class="text-lg font-bold text-white mt-2 px-2">"{db['title']}"</h3>
          <p class="text-xs text-[#A49E94] mt-2 max-w-[280px]">
            {db['risk']}
          </p>
        </div>

        <div class="mb-4 bg-gradient-to-r from-[#10B981]/20 to-transparent border border-[#10B981]/30 rounded-2xl p-4 text-left">
          <span class="text-[11px] font-mono text-[#10B981] font-bold">DEV SANITY SAVED:</span>
          <div class="flex items-baseline gap-2 mt-1">
            <span class="text-3xl font-black font-mono text-white">+{data['hours_shielded']} hrs</span>
            <span class="text-xs text-[#D8D4CB]">of unverified sprint churn prevented</span>
          </div>
        </div>
      </div>

      <!-- SLIDE 4: The Crown Jewel (Top SLA Win) -->
      <div id="slide-4" class="slide absolute inset-0 p-8 flex flex-col justify-between opacity-0 pointer-events-none transition-opacity duration-300">
        <div class="mt-14 text-left">
          <span class="text-xs font-mono uppercase tracking-widest text-[#10B981] font-bold">Hall of Fame</span>
          <h2 class="text-3xl font-extrabold text-white mt-1">Your Crown Jewel</h2>
        </div>

        <div class="my-auto flex flex-col items-center">
          <div class="w-20 h-20 rounded-full bg-[#10B981]/10 border border-[#10B981]/40 flex items-center justify-center text-4xl mb-3">
            🏆
          </div>
          <span class="text-xs font-mono text-[#10B981] uppercase tracking-wider font-bold">Inside Circle Delivery</span>
          <h3 class="text-xl font-black text-white mt-2 tracking-tight">"{cj['title']}"</h3>
          <p class="text-xs text-[#A1A1AA] mt-2 max-w-[280px]">
            {cj['impact']}
          </p>
        </div>

        <div class="mb-4 bg-gradient-to-r from-[#10B981]/15 to-transparent border border-[#10B981]/30 rounded-2xl p-4 text-left">
          <span class="text-[11px] font-mono text-[#10B981] font-bold">TOTAL SPEED SHAVED:</span>
          <div class="flex items-baseline gap-2 mt-1">
            <span class="text-3xl font-black font-mono text-[#10B981]">-{data['total_ms_shaved']} ms</span>
            <span class="text-xs text-[#A1A1AA]">p95 response time saved on core endpoints</span>
          </div>
        </div>
      </div>

      <!-- SLIDE 5: Shareable Dossier Card -->
      <div id="slide-5" class="slide absolute inset-0 p-6 flex flex-col justify-between opacity-0 pointer-events-none transition-opacity duration-300">
        <div class="mt-12 text-left">
          <span class="text-xs font-mono uppercase tracking-widest text-[#10B981] font-bold">Q4 Summary Dossier</span>
          <h2 class="text-2xl font-extrabold text-white mt-0.5">SnowPad Wrapped: 2026</h2>
        </div>

        <!-- Shareable Card Box -->
        <div class="my-auto bg-[#121214] border border-[#27272A] rounded-2xl p-5 text-left relative overflow-hidden shadow-2xl">
          <div class="absolute -right-8 -top-8 w-28 h-28 rounded-full bg-[#10B981]/10 blur-xl"></div>
          
          <div class="flex items-center justify-between pb-3 border-b border-[#27272A]">
            <div>
              <h4 class="font-bold text-white text-base leading-snug">{actor['name']}</h4>
              <p class="text-xs text-[#A1A1AA]">{actor['role']} • {actor['team']}</p>
            </div>
            <span class="text-3xl">{arch['emoji']}</span>
          </div>

          <div class="grid grid-cols-2 gap-3 my-3">
            <div class="bg-[#18181B] p-2.5 rounded-xl border border-[#27272A]">
              <span class="text-[10px] font-mono text-[#71717A] uppercase">Scope Focus</span>
              <p class="text-xl font-black font-mono text-[#10B981]">{data['focus_pct']}%</p>
            </div>
            <div class="bg-[#18181B] p-2.5 rounded-xl border border-[#27272A]">
              <span class="text-[10px] font-mono text-[#71717A] uppercase">Latency Saved</span>
              <p class="text-xl font-black font-mono text-[#10B981]">-{data['total_ms_shaved']}ms</p>
            </div>
            <div class="bg-[#18181B] p-2.5 rounded-xl border border-[#27272A]">
              <span class="text-[10px] font-mono text-[#71717A] uppercase">Whims Dodged</span>
              <p class="text-xl font-black font-mono text-white">{data['whims_count']}</p>
            </div>
            <div class="bg-[#18181B] p-2.5 rounded-xl border border-[#27272A]">
              <span class="text-[10px] font-mono text-[#71717A] uppercase">Sanity Shielded</span>
              <p class="text-xl font-black font-mono text-[#10B981]">+{data['hours_shielded']}h</p>
            </div>
          </div>

          <div class="pt-2 border-t border-[#27272A] flex items-center justify-between text-[11px] font-mono text-[#71717A]">
            <span class="text-[#10B981] font-bold">{arch['name']}</span>
            <span>SnowPad Scope OS</span>
          </div>
        </div>

        <div class="mb-3 space-y-2">
          <button id="copySummaryBtn" class="w-full py-3 rounded-xl bg-[#10B981] hover:bg-[#059669] text-black font-bold text-sm shadow-lg shadow-green-500/20 transition flex items-center justify-center gap-2">
            <span>📋 Copy Wrapped Summary</span>
          </button>
          <div class="flex items-center justify-between text-xs text-[#71717A] px-1 font-mono">
            <a href="radar.html" class="hover:text-white transition">&larr; Scope Radar</a>
            <a href="flow.html" class="hover:text-white transition">Scope Board &rarr;</a>
          </div>
        </div>
      </div>

    </div>

  </div>

  <script>
    let currentSlide = 0;
    const totalSlides = 6;
    const slideDuration = 6000; // 6s per slide
    let timer = null;
    let isPaused = false;
    let progressStartTime = 0;
    let elapsedBeforePause = 0;

    const slides = [
      document.getElementById('slide-0'),
      document.getElementById('slide-1'),
      document.getElementById('slide-2'),
      document.getElementById('slide-3'),
      document.getElementById('slide-4'),
      document.getElementById('slide-5')
    ];

    const bars = [
      document.getElementById('bar-0'),
      document.getElementById('bar-1'),
      document.getElementById('bar-2'),
      document.getElementById('bar-3'),
      document.getElementById('bar-4'),
      document.getElementById('bar-5')
    ];

    function showSlide(index) {{
      if (index < 0) index = 0;
      if (index >= totalSlides) index = totalSlides - 1;
      currentSlide = index;

      slides.forEach((s, i) => {{
        if (i === currentSlide) {{
          s.classList.remove('opacity-0', 'pointer-events-none');
          s.classList.add('opacity-100');
        }} else {{
          s.classList.remove('opacity-100');
          s.classList.add('opacity-0', 'pointer-events-none');
        }}
      }});

      bars.forEach((b, i) => {{
        if (i < currentSlide) b.style.width = '100%';
        else if (i === currentSlide) b.style.width = '0%';
        else b.style.width = '0%';
      }});

      startSlideTimer();
    }}

    function startSlideTimer() {{
      if (timer) cancelAnimationFrame(timer);
      progressStartTime = performance.now();
      elapsedBeforePause = 0;

      function step(now) {{
        if (isPaused) {{
          timer = requestAnimationFrame(step);
          return;
        }}
        const elapsed = now - progressStartTime;
        const pct = Math.min(100, (elapsed / slideDuration) * 100);
        bars[currentSlide].style.width = pct + '%';

        if (elapsed < slideDuration) {{
          timer = requestAnimationFrame(step);
        }} else {{
          if (currentSlide < totalSlides - 1) {{
            showSlide(currentSlide + 1);
          }}
        }}
      }}
      timer = requestAnimationFrame(step);
    }}

    document.getElementById('tapLeft').addEventListener('click', () => {{
      if (currentSlide > 0) showSlide(currentSlide - 1);
    }});

    document.getElementById('tapRight').addEventListener('click', () => {{
      if (currentSlide < totalSlides - 1) showSlide(currentSlide + 1);
    }});

    const pauseBtn = document.getElementById('pauseBtn');
    pauseBtn.addEventListener('click', () => {{
      isPaused = !isPaused;
      pauseBtn.textContent = isPaused ? 'Resume' : 'Pause';
      if (!isPaused) progressStartTime = performance.now() - elapsedBeforePause;
    }});

    window.addEventListener('keydown', (e) => {{
      if (e.key === 'ArrowRight' || e.key === ' ') {{
        if (currentSlide < totalSlides - 1) showSlide(currentSlide + 1);
      }} else if (e.key === 'ArrowLeft') {{
        if (currentSlide > 0) showSlide(currentSlide - 1);
      }}
    }});

    document.getElementById('copySummaryBtn').addEventListener('click', () => {{
      const summaryText = `❄️ SnowPad Wrapped Q4 2026: {actor['name']}
🎯 Archetype: {arch['name']} {arch['emoji']}
📊 Circle Focus Ratio: {data['focus_pct']}%
⚡ Latency Shaved: -{data['total_ms_shaved']}ms
🛡️ Sanity Shielded: +{data['hours_shielded']}h
🏆 Crown Jewel: "{cj['title']}"
🚫 Dodged Bullet: "{db['title']}"`;

      navigator.clipboard.writeText(summaryText).then(() => {{
        const btn = document.getElementById('copySummaryBtn');
        btn.innerHTML = '<span>✔ Copied to Clipboard!</span>';
        setTimeout(() => {{
          btn.innerHTML = '<span>📋 Copy Wrapped Summary</span>';
        }}, 2500);
      }});
    }});

    // Start presentation
    showSlide(0);
  </script>
</body>
</html>
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return output_path


def generate_actor_wrapped(repo: SnowPadRepository, actor_id: str, quarter: str = "Q4-2026") -> Path:
    """Generates Wrapped story HTML for an individual contributor."""
    data = build_wrapped_data(repo=repo, actor_id=actor_id, quarter=quarter)
    return generate_wrapped_html(data)


def generate_team_wrapped(repo: SnowPadRepository, quarter: str = "Q4-2026") -> Path:
    """Generates Wrapped story HTML for the collective team."""
    data = build_wrapped_data(repo=repo, actor_id=None, quarter=quarter)
    output_path = DIST_DIR / f"team_{quarter.lower().replace('-', '_')}_wrapped.html"
    return generate_wrapped_html(data, output_path=output_path)

