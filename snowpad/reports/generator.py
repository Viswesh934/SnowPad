"""Deliverable Generator - Creates executive presentation slides and PRDs from DuckDB data."""

from pathlib import Path
from typing import Any, Dict, Optional
from snowpad.config import BASE_DIR, settings
from snowpad.core.analytics import build_developer_review_dossier
from snowpad.db.repository import SnowPadRepository

DIST_DIR = BASE_DIR / "dist"
DIST_DIR.mkdir(parents=True, exist_ok=True)


class DeliverableGenerator:
    """Generates Reveal.js presentation slide decks and PRD specifications on-demand."""

    def __init__(self, repo: Optional[SnowPadRepository] = None):
        self.repo = repo or SnowPadRepository()

    def generate_presentation_slides(self, actor_id: str, quarter: str = "Q4-2026") -> Path:
        """Generates an executive Reveal.js slide deck for performance review in the warm coral theme."""
        dossier = build_developer_review_dossier(actor_id=actor_id, repo=self.repo, quarter=quarter)
        actor = dossier["actor"]
        metrics = dossier["impact_metrics"]
        recs = dossier["recommendations"]

        output_path = DIST_DIR / f"{actor_id}_q4_review.html"

        html_content = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>SnowPad Review: {actor['name']}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.css">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/theme/black.css">
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap" rel="stylesheet">
  <style>
    :root {{
      --r-background-color: #121316;
      --r-main-font: 'Plus Jakarta Sans', sans-serif;
      --r-heading-font: 'Plus Jakarta Sans', sans-serif;
      --r-main-color: #FAF8F5;
      --r-heading-color: #FAF8F5;
      --r-link-color: #FF5A36;
    }}
    .reveal h1, .reveal h2, .reveal h3 {{
      font-weight: 800;
      letter-spacing: -0.02em;
    }}
    .mono {{ font-family: 'JetBrains Mono', monospace; }}
    .coral {{ color: #FF5A36; }}
    .amber {{ color: #EAB308; }}
    .cream {{ color: #FAF8F5; }}
    .card {{
      background: #1A1C22;
      border: 1px solid #262830;
      border-radius: 14px;
      padding: 24px;
      margin: 16px 0;
      text-align: left;
    }}
    .stat-box {{
      background: #15161B;
      border: 1px solid #262830;
      border-radius: 10px;
      padding: 16px;
      text-align: center;
    }}
    .badge {{
      display: inline-block;
      padding: 4px 12px;
      border-radius: 20px;
      font-size: 14px;
      font-family: 'JetBrains Mono', monospace;
      font-weight: 600;
      background: rgba(255, 90, 54, 0.15);
      color: #FF7A45;
      border: 1px solid rgba(255, 90, 54, 0.4);
    }}
  </style>
</head>
<body>
  <div class="reveal">
    <div class="slides">

      <!-- Slide 1: Title -->
      <section>
        <div style="text-align: center;">
          <span class="badge">SNOWPAD IMPACT DOSSIER • {quarter}</span>
          <h1 style="margin-top: 24px; font-size: 2.4em;">{actor['name']}</h1>
          <p class="coral" style="font-size: 1.1em; font-weight: 600;">{actor['role']}</p>
          <p style="color: #A49E94; font-size: 0.85em;">Team: {actor['team']}</p>
          <div style="margin-top: 36px;">
            <p style="color: #6E685F; font-size: 0.75em;" class="mono">VERDICT: <span style="color: #10B981; font-weight: 700;">{dossier['verdict']}</span></p>
          </div>
        </div>
      </section>

      <!-- Slide 2: Scope Horizon & Circle Alignment -->
      <section>
        <h3 class="coral">Circle of Scope Alignment</h3>
        <p style="font-size: 0.85em; color: #A49E94;">{dossier['focus_summary']}</p>

        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; margin-top: 30px;">
          <div class="stat-box">
            <span style="font-size: 0.8em; color: #A49E94;">Focus Ratio</span>
            <p class="mono coral" style="font-size: 1.8em; font-weight: 800; margin: 8px 0;">{metrics.get('circle_focus_percentage', 0)}%</p>
            <span style="font-size: 0.75em; color: #716B61;">Inside Core SLAs</span>
          </div>
          <div class="stat-box">
            <span style="font-size: 0.8em; color: #A49E94;">Confirmed Features</span>
            <p class="mono" style="font-size: 1.8em; font-weight: 800; margin: 8px 0; color: #10B981;">{metrics.get('confirmed_features', 0)}</p>
            <span style="font-size: 0.75em; color: #716B61;">Locked in Sprint</span>
          </div>
          <div class="stat-box">
            <span style="font-size: 0.8em; color: #A49E94;">Whims Quarantined</span>
            <p class="mono" style="font-size: 1.8em; font-weight: 800; margin: 8px 0; color: #D8D4CB;">{metrics.get('whims_quarantined', 0)}</p>
            <span style="font-size: 0.75em; color: #716B61;">Parked Distractions</span>
          </div>
        </div>
      </section>

      <!-- Slide 3: Key SLA & KPI Movers -->
      <section>
        <h3>Quantified Telemetry Impact</h3>
        <div class="card">
          <p style="color: #A49E94; font-size: 0.8em; margin-bottom: 8px;" class="mono">CORE PERFORMANCE VICTORIES</p>
          <ul style="font-size: 0.8em; line-height: 1.8; color: #D8D4CB;">
            <li><strong class="coral">Response Time Shaved:</strong> <span class="mono" style="color: #10B981;">-{metrics.get('total_ms_shaved', 0)} ms</span> across critical payment & checkout endpoints.</li>
            <li><strong class="coral">Total Contributions:</strong> <span class="mono">{metrics.get('total_contributions', 0)}</span> tracked chat signals audited in DuckDB.</li>
            <li><strong class="coral">Average Uncertainty:</strong> <span class="mono">{int((metrics.get('avg_uncertainty') or 0.5) * 100)}%</span> across proposed discussions.</li>
          </ul>
        </div>
      </section>

      <!-- Slide 4: Recommendations & Next Steps -->
      <section>
        <h3 class="coral">Manager Action Items &amp; PRDs</h3>
        <div class="card">
          <p style="color: #A49E94; font-size: 0.8em; margin-bottom: 12px;" class="mono">BACKLOG RECOMMENDATIONS</p>
          <ul style="font-size: 0.8em; line-height: 1.8; color: #FAF8F5;">
            {''.join([f"<li>{r}</li>" for r in recs]) if recs else "<li>Continue high-focus feature execution within core scope.</li>"}
          </ul>
        </div>
        <p style="font-size: 0.75em; color: #716B61; margin-top: 24px;" class="mono">Generated on-demand by SnowPad OS</p>
      </section>

    </div>
  </div>

  <script src="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.js"></script>
  <script>
    Reveal.initialize({{
      hash: true,
      slideNumber: true,
      transition: 'fade',
      controls: true,
      progress: true
    }});
  </script>
</body>
</html>
"""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return output_path

    def generate_prd_specification(self) -> Path:
        """Generates a Refactor PRD Markdown document from active DuckDB debates and debt items."""
        debates = self.repo.get_pending_debates()
        output_path = DIST_DIR / "sprint_refactor_prd.md"

        lines = [
            "# SnowPad Sprint Refactor PRD",
            "",
            "> **Generated on-demand from DuckDB chat ledger**  ",
            "> Active discussions and architectural tradeoffs requiring sprint backlog resolution.",
            "",
            "---",
            "",
            "## 1. Active Scope Debates Requiring Alignment",
            "",
        ]

        if not debates:
            lines.append("*No pending debates in current ledger.*")
        else:
            for d in debates:
                lines.extend([
                    f"### 📌 {d['title']}",
                    f"- **Origin Channel:** `{d['origin_channel']}`",
                    f"- **Proposed by:** **{d['author_name']}**",
                    f"- **Uncertainty Rating:** `{int(d['uncertainty_score'] * 100)}%`",
                    f"- **Estimated KPI Impact:** {d.get('estimated_kpi_impact') or 'Pending benchmarking'}",
                    f"- **Discussion Summary:** {d['summary']}",
                    "",
                    "#### Decision Needed:",
                    "- [ ] **Approve into next sprint:** Lock into the Circle of Scope.",
                    "- [ ] **Park as Whim:** Reject or defer to avoid sprint distraction.",
                    "",
                    "---",
                    "",
                ])

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return output_path

