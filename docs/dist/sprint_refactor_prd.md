# SnowPad Sprint Refactor PRD

> **Autonomous Scope Decision Ledger**  
> Active discussions and architectural tradeoffs requiring sprint backlog resolution.

---

## 1. Active Scope Debates Requiring Alignment

### 📌 Migrate audit log streaming from SQS to Apache Kafka
- **Origin Channel:** `#eng-war-room`
- **Proposed by:** **Alex Chen**
- **Uncertainty Rating:** `60%`
- **Estimated KPI Impact:** Estimated $1,400/mo AWS cost reduction; requires 2-week migration effort.
- **Discussion Summary:** Discussed in #eng-war-room: SQS costs spiking on 10k req/sec peak. Proposed Kafka sidecar.

#### Decision Needed:
- [ ] **Approve into next sprint:** Lock into the Circle of Scope.
- [ ] **Park as Whim:** Reject or defer to avoid sprint distraction.

---

### 📌 Deprecate Multi-step Onboarding Wizard in favor of 1-Click Social Sign-in
- **Origin Channel:** `#growth-experiments`
- **Proposed by:** **Sam Torres**
- **Uncertainty Rating:** `55%`
- **Estimated KPI Impact:** +18% signup conversion, but unknown fraud risk impact.
- **Discussion Summary:** Discussed in #growth-experiments: Drop phone verification step to boost conversion rate.

#### Decision Needed:
- [ ] **Approve into next sprint:** Lock into the Circle of Scope.
- [ ] **Park as Whim:** Reject or defer to avoid sprint distraction.

---
