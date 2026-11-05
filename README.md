# ❄️ SnowPad

<p align="center">
  <b>The Chat Uncertainty & Scope Radar for Engineering & Product Teams</b><br>
  <i>Powered by DuckDB & Switch AI for the Flip the Switch Hackathon (Nov 2026)</i>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Status-Phase%202%20Active-FF5A36?style=for-the-badge&logoColor=FAF8F5" alt="Status">
  <img src="https://img.shields.io/badge/Database-DuckDB%20Embedded-16171B?style=for-the-badge&logo=duckdb&logoColor=FAF8F5" alt="DuckDB">
  <img src="https://img.shields.io/badge/Integration-Switch%20AI-FF7A45?style=for-the-badge&logoColor=FAF8F5" alt="Switch AI">
  <img src="https://img.shields.io/badge/Python-3.10+-16171B?style=for-the-badge&logo=python&logoColor=FF5A36" alt="Python">
</p>

---

<p align="center">
  <img src="assets/snowpad_radar.svg" alt="SnowPad Scope Radar HUD" width="100%">
</p>

<p align="center">
  👉 <b><a href="snowpad/web/radar.html">Launch Interactive Web Radar HUD</a></b> (Live canvas sweep with clickable blips & uncertainty meters)
</p>

---

## 🌪️ The Problem: "Chat Entropy & Scope Amnesia"

Every single day in Slack, Discord, and Microsoft Teams, dozens of critical discussions unfold in loose threads:
* 💡 **Spontaneous feature proposals:** *"Hey, what if we also added bulk CSV export to this screen?"*
* ⚙️ **Casual architectural pivots:** *"Maybe we should just bypass the auth check with raw Redis keys for now?"*
* 🎨 **Unvalidated whimsical ideas:** *"Thinking of redesigning the admin drawer with neon confetti on checkout."*

### Why this breaks teams:
1. **Uncertainty is never quantified:** Devs build features because of an offhand comment in a Tuesday thread.
2. **Whims masquerade as priorities:** Off-scope ideas distract engineers from core sprint SLAs.
3. **Context vanishes:** When quarterly performance reviews or incident retrospectives arrive, nobody has a record of **why** decisions were made under pressure.

---

## 🎯 The Solution: The "Circle of Scope"

**SnowPad** intercepts and audits uncertain team chat threads via **Switch AI**, scoring their ambiguity and mapping them onto a dynamic **Scope Radar** backed by an embedded **DuckDB** data lake:

| Horizon Zone | Radial Distance | Meaning | Example from Team Chat |
| :--- | :---: | :--- | :--- |
| 🟢 **Inside the Circle** | $r \le 1.0$ | **Confirmed Features & Core SLAs**<br>High certainty, locked into sprint, moving latency/revenue metrics. | *"Batched Settlement Engine cuts p95 API latency by 120ms (Sprint-42)."* |
| 🟡 **Borderline Debate** | $0.6 \le r \le 1.0$ | **Active Chat Debates**<br>High uncertainty ($>50\%$), requires technical or product lead sign-off. | *"SQS vs Kafka audit logs: $1,400/mo AWS saving vs 2-week migration risk."* |
| 🔴 **Outside the Circle** | $r > 1.0$ | **Parked Whims & Noise**<br>Safely quarantined outside the circle to protect developer focus. | *"Lottie confetti animation on checkout (+140kb bundle bloat, zero lift)."* |

---

## ⚡ What Makes SnowPad Stand Out?

- 🦆 **Zero-Markdown, Zero-Server Data Lake:** All chat signals, telemetry observations, and resolution states live in a local, single-file `snowpad.duckdb` database.
- 📡 **Live Channel Chatter Breakdown:** Pinpoints exactly which Slack/Discord channels are producing the highest uncertainty (`#growth-experiments` vs. `#backend-core`).
- 🛡️ **The Developer Sprint Shield:** Keeps track of how many distracting whims were *quarantined*, defending developers during performance reviews:
  > *"Alex didn't just ship 2 critical features; SnowPad records that Alex also contained 3 off-scope whim requests, protecting 34 hours of sprint focus."*
- 📄 **Executive Review Dossiers:** One-command generation of evidence-backed performance review sheets (`snowpad review --actor alex_chen`).

---

## 💻 CLI Quickstart

### 1. Installation
```bash
git clone https://github.com/Viswesh934/SnowPad.git
cd SnowPad

# Install with uv
uv venv
uv pip install -e ".[dev]"
```

### 2. Seed Realistic Chat Signals
```bash
python -m snowpad.cli seed
```

### 3. Check Channel Chatter & Uncertainty Pulse
```bash
# Channel breakdown: where is the uncertainty happening?
python -m snowpad.cli chatter

# Weekly operational pulse across the team
python -m snowpad.cli weekly
```

### 4. Interactive Scope Radar
```bash
# Print ASCII / Rich terminal radar
python -m snowpad.cli radar

# Or open the live animated Web HUD in your browser
start snowpad/web/radar.html
```

### 5. Generate Individual Contributor Dossier
```bash
python -m snowpad.cli review --actor maya_patel --quarter Q4-2026
```

---

## 🗺️ Hackathon Roadmap (Nov 4 – 7, 2026)

- [x] **Phase 1: Foundations & DuckDB Core** (Generic schema, analytical views, rich CLI, 100% test coverage)
- [x] **Phase 2: Circle of Scope & Visual Radar** (Chat signal models, vector SVG HUD, interactive HTML5 canvas radar)
- [ ] **Phase 3: Switch Agent & Chat Bridge** (Live Slack/Discord bot via Switch, `/snowpad` triage slash command)
- [ ] **Phase 4: Video Demo, README Finalization & Submission** (YouTube walkthrough & WeMakeDevs submission)

---

## 📜 License
Apache-2.0 / MIT • Built for the **Flip the Switch Hackathon 2026**
