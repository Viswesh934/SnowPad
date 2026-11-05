# ❄️ SnowPad

<p align="center">
  <b>The Chat Uncertainty &amp; Scope Radar for Engineering and Product Teams</b><br>
  <i>Powered by DuckDB &amp; Switch AI for the Flip the Switch Hackathon</i>
</p>

---

<p align="center">
  <img src="assets/snowpad_architecture.svg" alt="SnowPad Architecture (Excalidraw Style)" width="100%">
</p>

<p align="center">
  👉 <b><a href="snowpad/web/radar.html">Open the Interactive Web Radar</a></b> (Live canvas sweep with blip inspection and uncertainty meters)
</p>

---

## 🎯 How Ray Tracing Works in SnowPad

In computer graphics, ray tracing calculates how light travels through a scene—testing whether a ray intersects with a solid surface, casts a shadow, or dissipates into the dark.

SnowPad applies this exact mathematical principle to team communications in Slack and Discord:

1. **The Focal Point (Origin):** The center of the radar represents your team's core commitments: response time SLAs, uptime, and active sprint deliverables.
2. **Casting the Ray:** Whenever team members discuss an ad-hoc idea, a proposed feature, or a quick architectural pivot in chat, SnowPad casts an analytical ray from that conversation toward the focal point.
3. **Intersection vs. Scatter:**
   * 🟢 **Intersection (Inside the Circle):** If the ray hits a verified KPI (such as reducing p95 latency or unblocking an enterprise customer) with high clarity, it penetrates the perimeter and lands inside the circle.
   * 🔴 **Scatter &amp; Shadow (Outside the Circle):** If the proposal is vague, lacks ownership, or has no measurable impact on active goals, the ray scatters into the outer shadow—quarantined as a parked whim so it does not derail developer focus.
4. **Visual Ray Sweep:** The radar HUD uses an active radial ray-marcher sweeping 360 degrees across all active channels, rendering the distance and uncertainty of every conversation in real time.

---

## 💬 The Problem: Loose Chats &amp; Scope Drift

Every day in team chat, dozens of micro-decisions unfold in threads:
* 💡 **Spontaneous feature suggestions:** *"What if we also added bulk CSV export to this screen?"*
* ⚙️ **Casual architectural tweaks:** *"Maybe we should just bypass the auth check with raw Redis keys for now?"*
* 🎨 **Well-intentioned whims:** *"Thinking of redesigning the admin drawer with confetti animations this afternoon."*

Because these conversations happen casually in chat:
1. **Uncertainty is never measured:** Developers often begin building things based on an offhand remark in a Tuesday thread, without anyone confirming whether it is actually a priority.
2. **Whims masquerade as urgent work:** Fleeting ideas pull engineers away from critical stability and performance work.
3. **Context vanishes:** When quarterly reviews arrive, there is no shared ledger showing why decisions were made or which distractions were avoided.

---

## ⭕ The Solution: The Circle of Scope

SnowPad listens to incoming threads through **Switch AI**, evaluates the ambiguity of each proposal, and maps it onto an embedded **DuckDB** ledger:

| Zone | Radial Distance | Meaning | Real Team Example |
| :--- | :---: | :--- | :--- |
| 🟢 **Inside the Circle** | $r \le 1.0$ | **Confirmed Features &amp; Core SLAs**<br>High certainty, locked into sprint, moving latency or revenue. | *"Batched Settlement Engine cuts p95 API latency by 120ms (Sprint-42)."* |
| 🟡 **Borderline Debate** | $0.6 \le r \le 1.0$ | **Active Chat Debates**<br>High uncertainty ($>50\%$), requiring technical lead or PM sign-off. | *"SQS vs Kafka audit logs: $1,400/mo AWS saving vs 2-week migration risk."* |
| 🔴 **Outside the Circle** | $r > 1.0$ | **Parked Whims**<br>Safely quarantined outside the circle to protect developer focus. | *"Lottie confetti animation on checkout (+140kb bundle bloat, zero lift)."* |

---

## 🚀 Key Capabilities

* 🦆 **Zero-Markdown, Single-File Data Lake:** All chat signals, telemetry observations, and resolution states are stored in a local, embedded `snowpad.duckdb` database. No external servers or configuration needed.
* 📡 **Channel Chatter Breakdown:** Identifies which chat channels generate the highest ambiguity (`#growth-experiments` vs. `#backend-core`), helping managers keep discussions focused.
* 🛡️ **The Developer Sprint Shield:** Tracks how many off-scope whims were successfully quarantined, giving developers concrete proof of their focus during performance reviews:
  > *"Alex didn't just ship 2 critical features; SnowPad records that Alex also contained 3 off-scope whim requests, protecting 34 hours of sprint focus."*
* 📄 **Instant Performance Review Dossiers:** Generates evidence-backed contribution summaries with a single command (`snowpad review --actor alex_chen`).

---

## ⚡ Quickstart

### 1. Installation

```bash
git clone https://github.com/Viswesh934/SnowPad.git
cd SnowPad

# Set up virtual environment and install dependencies
uv venv
uv pip install -e ".[dev]"
```

### 2. Seed Realistic Chat Signals

```bash
python -m snowpad.cli seed
```

### 3. Review Channel Chatter

```bash
# View breakdown of uncertainty across channels
python -m snowpad.cli chatter

# View the weekly operational pulse across all contributors
python -m snowpad.cli weekly
```

### 4. Open the Scope Radar

```bash
# Terminal table view
python -m snowpad.cli radar

# Interactive Web HUD
start snowpad/web/radar.html
```

### 5. Generate a Contributor Review

```bash
python -m snowpad.cli review --actor maya_patel --quarter Q4-2026
```

---

## 📜 License

Apache-2.0 / MIT • Built for the **Flip the Switch Hackathon 2026**
