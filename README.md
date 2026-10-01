# Cortex - My first agentic loop

> Cortex drafts a PM's weekly leadership status update in minutes instead of an hour. It pulls one project's latest activity, drafts a grounded update, proposes next-sprint stories, and stops for the PM's approval. An independent critic checks every claim against the source data. Cortex has read-only access, no posting tool, and hard limits on cost and runtime, so it can't leak confidential projects or post anything on its own. It's at the assisted stage today, with a clear 4-week test to earn more autonomy.

_Miguel Chavez · Agentic Loops for PMs Cohort · September 2026_

Repo: https://github.com/miguelchavez-code/pm-os-agent

This repo is my final project for the Agentic Loops for PMs Certification, **Cortex - My first agentic loop**. Each module’s artifact lives in its own folder; this README is the dashboard and the pitch.

---

## Module artifacts

### M1 · The Agent Line
- **Agent-line map**: [`01-agent-line/agent-line-map.md`](01-agent-line/agent-line-map.md)

### M2 · Loop Engineering
- **Loop spec**: [`02-loop-design/loop-spec.md`](02-loop-design/loop-spec.md)

### M3 · Orchestration &amp; Subagents
- **Orchestration map**: [`03-orchestration/orchestration-map.md`](03-orchestration/orchestration-map.md)

### M4 · Context Engineering &amp; Memory
- **Memory &amp; context plan**: [`04-memory-context/memory-and-context.md`](04-memory-context/memory-and-context.md)

### M5 · Bounds &amp; Evals
- **Bounds &amp; evals**: [`05-bounds-evals/bounds-and-evals.md`](05-bounds-evals/bounds-and-evals.md)

### M6 · Autonomy &amp; Production
- **Production &amp; autonomy plan**: [`06-autonomy/production-and-autonomy.md`](06-autonomy/production-and-autonomy.md)
- **Prototype write-up**: [`06-autonomy/prototype.md`](06-autonomy/prototype.md)
- **Build insights**: [`06-autonomy/build-insights.md`](06-autonomy/build-insights.md)
- **Pitch deck**: [`06-autonomy/pitch.html`](06-autonomy/pitch.html)

---

## Ship plan

### Autonomy dial (per segment)
- Seasoned PM (project owner) → Supervised: weekly cron drafts + queues; PM approves at 8a; #4/#6 escalate.
- New PM / eng lead → Assisted: runs on request only; every draft and the context-exclusion list reviewed.
- Exec stakeholder → Shadow: never deals with Cortex; reads only PM-approved updates.

The dial never moves the agent line: posting, commitments, and escalations stay human for everyone.

### Trust Ladder rung + eval gate
- Current rung: Assisted (runs on demand on fixture data; weekly cron and real Jira/Slack not wired yet).
- Eval gate to Supervised: over 4 consecutive weekly runs on real Northstar data (shadow), EV-1/EV-2/EV-4 pass ≥90%, EV-3/EV-5/EV-6 replays pass 100% on every change, 0 trust incidents.
- Incident record (testing): 0 posts, 0 leaks, 0 commitments; 3 near-misses, each caught by a bound or the critic.

### Deployment plan
- Runtime: serverless weekly cron (Thu ~8:45 am ET) + Slack webhook, matching the M2 cron + hook loop.
- Owner: Miguel Chavez; backup: Northstar eng on-call after 1 business day.
- Rollback: kill switch (KILL / CORTEX_KILL=1) → drop the dial a rung → disable a tool → git revert to last green replay.
- Monitoring: exit type, critic pass rate, cost per run vs $0.50, escalation rate, context exclusions, trust incidents.

### ROI metrics + widen-autonomy rule
- Outcome: ≤15 min PM time per weekly update (vs a 2-week measured baseline).
- Cost-to-serve: ≤$0.05 per run (today ≈ 1–2¢).
- Trust incidents: 0 per quarter.

**Widen rule:** a segment's dial goes up one notch only after its Trust Ladder gate holds for 4 consecutive weeks with 0 trust incidents and owner sign-off.

### Governance &amp; strategy
- Compliance: confidential roadmap items, customer PII, credentials, and financials never enter a prompt; logs have a 90-day TTL.
- Safety: posting (8a/8b), commitments, escalations, and merges stay human for everyone; no posting tool; kill switch.
- Reliability: 8 iterations, 2 revisions, 3 failed pulls, 90 s, $0.50/run, $5/month; escalate-on-stuck; model down → retry once, then STUCK and the PM writes the update by hand.
- Strategy: next, a code-level injection check; then widen to Vega (open Sev-1), gated by EV-5 + EV-7 ("Sev-1 open → escalate, no date") at 100% over 4 weeks.

---

## Build insights

- **Friction point.** The critic model fought me most. The cheap one mislabelled checks and invented problems, so I had to move the critic to a stronger model.
- **Key learning.** A bound only counts if code enforces it; a sentence in a prompt is a wish.
- **Aha moment.** Drawing the agent line first made every later decision easier. Not giving Cortex a posting tool did more for safety than any prompt.

---

_Certification submission, Agentic Loops for PMs Certification._
