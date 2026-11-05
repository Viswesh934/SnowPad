# ❄️ SnowPad

> **Developer Impact & Tech Debt OS with Circle-of-Scope Intelligence**  
> *Powered by DuckDB & Switch AI for the Flip the Switch Hackathon (Nov 2026)*

---

## 🎯 Overview

Software engineers and teams make dozens of critical, spontaneous engineering choices every week:
- **Hotfixes deployed on a whim** to patch emergency bugs.
- **Latency regressions & response-time optimizations** under fire.
- **Pragmatic technical debt compromises** made to meet release deadlines.

When performance reviews, 1-on-1s, or quarterly planning arrive, **this unwritten work is lost in Slack threads and Git history**. 

**SnowPad** is a tireless engineering guardian and impact ledger. It continuously maps developer actions, tracks response-time deltas, and uses an algorithmic **"Circle of Scope"** to separate high-leverage business movers from distracting firefighting noise—storing everything in a high-performance, embedded **DuckDB** database.

```
                           ┌──────────────────────────┐
                           │      DUCKDB LEDGER       │
                           │  Every Dev Mapped:       │
                           │  • Commits & Hotfixes    │
                           │  • Latency & KPI deltas  │
                           │  • Inside/Outside Circle │
                           └─────────────┬────────────┘
                                         │
              ┌──────────────────────────┴──────────────────────────┐
              ▼                                                     ▼
    [ Manager's Lens ]                                    [ Developer's Lens ]
    • Team-wide mapping & health                          • Personal "Brag Sheet"
    • Who is firefighting vs building?                    • Quantified impact on latency & uptime
    • Tech debt accumulation per service                  • Defends decisions made under pressure
    • Instant 1-on-1 & Perf Review generation             • One-click PRD/presentation generator
```

---

## 💡 Key Features

- **🎯 The "Circle of Scope" Filter:** Categorizes work as *Inside the Circle* (high-leverage, direct SLA/KPI mover) vs. *Outside the Circle* (reactive churn, unindexed hacks, off-scope noise).
- **🦆 Embedded DuckDB Data Lake:** Fast, zero-config analytical SQL engine replacing endless messy markdown files.
- **⏱️ Cadence Intelligence:**
  - **Weekly Standup Pulse (1–2x/week):** Quick 2-minute synthesis of what devs moved and what debt was logged.
  - **Quarterly Performance Reviews:** Instant, evidence-backed dossiers with real metrics (p95 latency shaved, incidents contained).
- **📄 One-Click Deliverables:** Export executive-ready presentation slide decks and refactor PRDs.
- **🔌 Switch AI Integration:** Operates directly inside team collaboration channels (Slack, Discord, MS Teams).

---

## 🏗️ Architecture & Project Structure

```
SnowPad/
├── pyproject.toml              # Dependencies managed by uv (duckdb, rich, pydantic, jinja2)
├── snowpad/
│   ├── config.py              # Configuration & database file paths
│   ├── db/
│   │   ├── schema.py          # Generic DuckDB schema DDL
│   │   ├── connection.py      # DuckDB session & connection manager
│   │   ├── repository.py      # Domain CRUD & analytical query layer
│   │   └── seeder.py          # Realistic demo dataset generator
│   ├── core/
│   │   ├── models.py          # Pydantic domain models (Actor, Event, Metric, Circle)
│   │   └── analytics.py       # Weekly pulse & quarterly review aggregators
│   ├── agent/                 # Switch AI agent integration (Phase 3)
│   ├── reports/               # Presentation & PRD generators (Phase 3)
│   └── cli.py                 # SnowPad CLI utility
└── tests/
    └── test_db.py             # DuckDB schema & query test suite
```

---

## 🚀 Quick Start

### 1. Prerequisites
- Python >= 3.10
- `uv` package manager (`pip install uv`)

### 2. Installation
```bash
git clone https://github.com/Viswesh934/SnowPad.git
cd SnowPad

# Set up virtual environment and install dependencies
uv venv
uv pip install -e ".[dev]"
```

### 3. Initialize & Seed Database
```bash
# Seed realistic demo data into DuckDB
python -m snowpad.cli seed
```

### 4. Run Analytical Reports
```bash
# Weekly team pulse
python -m snowpad.cli weekly

# Individual developer performance review for Q4
python -m snowpad.cli review --actor alex --quarter Q4
```

---

## 📜 License
Apache-2.0 / MIT
