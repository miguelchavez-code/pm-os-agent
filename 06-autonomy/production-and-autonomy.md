# Production & Autonomy: Cortex PM Chief-of-Staff Agent

> Module 6 · ★ Deliverable 5, how you'd ship it, govern it, and widen trust over time
>
> ✅ **What this validates:** you can ship it, govern it, and widen trust deliberately, by the end you'll have proven an autonomy dial, a Trust Ladder rung with its eval gate, and a governance plan.

## Autonomy Dial by segment

_Autonomy is a product decision per user, not one global setting._

| Segment | Desired autonomy | What it means for Cortex | Why |
|---|---|---|---|
| **Seasoned PM who owns the project** (e.g. me on Northstar) | **Supervised** | Weekly cron drafts + queues automatically; PM approves at 8a; #4/#6 escalate | Knows the project well enough to review a draft fast; the use case Cortex was built for |
| **Newly onboarded PM / eng lead** | **Assisted** | Runs only on request (hook, not cron); every draft *and* the context-exclusion list (#2) reviewed before anything moves | Doesn't yet know the norms or confidential projects well enough to spot a subtle miss |
| **Exec stakeholder** (leadership audience) | **Shadow** | Never deals with Cortex directly; only reads PM-approved updates | Highest blast radius; no reason to give execs an agent they'd have to supervise |

> The dial changes how many *below-the-line* actions pause for a given user. It never moves the M1 agent line: posting (8a/8b), commitments (#4), and escalations (#6) stay human for every segment. *Segments per Claude's recommendation, accepted by the learner.*

## Trust Ladder

- **Current rung:** **Assisted.** Cortex drafts and the PM approves everything, but it runs on demand, on fixture data; the weekly cron and real Jira/Slack connectors aren't wired yet. Calling it "supervised" would overstate it.
- **Eval gate to reach the next rung (→ Supervised, seasoned-PM segment):** over **4 consecutive weekly runs on real Northstar data**, in shadow alongside the human-written update:
  - **EV-1 / EV-2 / EV-4** (tool-call accuracy, path quality, task completion) pass on **≥90%** of runs;
  - **EV-3 / EV-5 / EV-6** replays (recovery, jailbreak, bounds) pass **100%** on every code or prompt change;
  - **0 trust incidents** (no confidential leak, no unapproved post, no invented metric or date reaching PM approval).
- **Incident record so far (testing only):** **0 posts, 0 leaks, 0 commitments.** Three near-misses, each caught:
  - M1: critic disagreement ("Green despite #818") → revision cap stopped the run;
  - M3: `gpt-4o-mini` critic mislabelled checks → critic moved to `gpt-4o`;
  - M5: Cortex didn't flag the jailbreak itself → critic D escalated it; code-level injection check is next.
- *Rung and gate per Claude's recommendation, accepted by the learner.*

## Deployment plan

- **Runtime:** **serverless scheduled job**: weekly cron (Thu ~8:45 am ET) + a webhook endpoint for the Slack hook, matching the M2 cron + hook loop. Nothing runs all the time. API key in a secrets manager, never in a file.
- **Operator / on-call owner:** **Miguel Chavez** (PM, primary owner). **Backup:** the Northstar engineering on-call for that week (team on-call rotation).
  - **Escalation path:** Cortex ESCALATE/STUCK → Miguel notified → no response within 1 business day → Northstar eng on-call. Either can trip the kill switch or drop the dial; neither posts on Cortex's behalf without 8a approval.
- **Rollback (fastest first):** (1) kill switch: `00-build/KILL` / `CORTEX_KILL=1`; (2) drop the dial a rung: cron off, hook only; (3) disable a tool by removing it from `TOOLS`; (4) `git revert` to the last commit where the replay set passed.
- **Monitoring:** per run: exit type (SUCCESS / STUCK / ESCALATE / KILLED), critic pass rate + `failed_checks` (`critic-log.jsonl`), cost per run vs. $0.50, escalation rate, context-exclusions count, trust incidents. Reviewed weekly by the owner.

## ROI metrics (beyond adoption & tokens)

| Metric | Target | How captured |
|---|---|---|
| **Outcome:** PM time per weekly update | **≤15 min** review (vs. a 2-week measured baseline) | Time log before/after |
| **Cost-to-serve** | **≤$0.05 per run** (today ≈ 1–2¢) | `Bounds` counter + OpenAI usage dashboard |
| **Trust incidents** | **0 per quarter** | Critic log + PM incident reports |

## Widen-autonomy decision rule

Turn a segment's dial up one notch **only after its Trust Ladder gate has held for 4 consecutive weeks with 0 trust incidents, and the owner has signed off.**

## Governance & forward strategy

- **Compliance:** never in a prompt: CONFIDENTIAL roadmap items, customer PII, credentials, financials. No personal data stored; logs have a 90-day TTL; `run-output/` is gitignored.
- **Safety:** above the line for everyone: 8a/8b posting, #4 commitments, #6 escalations, any merge/close. Kill switch always available.
- **Reliability:** caps: 8 iterations, 2 revisions, 3 failed pulls, 90 s, $0.50/run, $5/month; escalate-on-stuck. **Model down:** retry once, then STUCK; the PM writes that week's update by hand. Never falls back to an unvetted model.
- **Strategy:** next, a **code-level injection check** (M5 finding); then widen to **Vega** (Yellow, open Sev-1), gated by EV-5 + a new **EV-7** ("Sev-1 open → escalate, no date") passing 100% over 4 weeks.

*Deployment, ROI, widen rule, and governance per Claude's recommendation, accepted by the learner.*
