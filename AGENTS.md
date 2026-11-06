# SnowPad Scope Radar & Tech Debt Agent (Switch AI Specification)

> **Agent Identity:** `SnowPad`  
> **Role:** Autonomous Scope Governor & Chat Uncertainty Radar  
> **Orchestrator:** Switch Console (`switchagents.ai`) / Switch Bridge  
> **Integration Targets:** Discord, Slack, Microsoft Teams, and Switch Rooms

---

## 🎯 Purpose & Scope Boundary

SnowPad is an autonomous agent orchestrated via **Switch** to govern chat scope, eliminate tech debt drift, and protect developer sanity across shared team channels.

### Core Behaviors in Switch Rooms:
1. **Chat Uncertainty Auditing:**
   - Intercepts speculative proposals (`"what if"`, `"maybe we should"`, `"could we add"`).
   - Classifies uncertainty on a 0–100% scale.
   - Evaluates proposals against the **Circle of Scope** (core latency SLAs, uptime, sprint deliverables).

2. **Whim Quarantine:**
   - Discussions that do not contribute to core metrics (e.g. confetti animations, non-standard re-themes) are classified as **OUTSIDE_CIRCLE (Parked Whims)** to protect dev focus.

3. **Autonomous Slash Commands:**
   - `/snowpad radar` - Returns current Circle of Scope radar status and active blips.
   - `/snowpad review @actor` - Returns evidence-backed performance review dossier.
   - `/snowpad weekly` - Returns weekly operational pulse for team standups.
   - `/snowpad lock "Feature"` - Commits a discussed feature into the active sprint scope.

4. **Deliverable Exports:**
   - Refreshes Sprint PRDs (`dist/sprint_refactor_prd.md`).
   - Refreshes Reveal.js executive presentations (`dist/*_q4_review.html`).
   - Generates quarterly Spotify-Wrapped stories (`dist/*_wrapped.html`).

---

## 🛠️ CLI & Stdio Invocation for Switch Console

Switch Console invokes SnowPad using standard command-line pipes:

```bash
# Analyze a message piped from Switch Room
python -m snowpad.cli msg --text "What if we added Kafka for event streaming?" --user "Alex Chen" --channel "#backend-core"

# Launch interactive stdio Switch bridge
python -m snowpad.cli bridge

# Run autonomous scheduled scope audit
python -m snowpad.cli schedule --once
```
