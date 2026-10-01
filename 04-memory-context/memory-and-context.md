# Context Engineering & Memory: Cortex PM Chief-of-Staff Agent

> Module 4 · Context Engineering & Memory
>
> ✅ **What this validates:** the agent reasons on the right, safe inputs, by the end you'll have proven a context budget, per-source retrieve-vs-long-context decisions, and a memory map with risk mitigations.
>
> 🗂️ **How the lab maps to this file:** In **Part A** (before the lecture) you don't edit this file, you rough-draft on scratch, focused on the per-source calls in **section 2** plus a quick remember/forget + "how it rots" sketch. In **Part B** (after the lecture) you complete **all five sections**; the Lab Guide's guided builder writes this file for you to copy in and commit.

> **Part A (sample draft, written by Claude at the learner's request, first-instinct, pre-rubric):** activity, past updates, roadmap, norms, task brief: all *long-context* ("small, just include it"). Remember everything, forget nothing. How it rots: old updates pile up and Cortex copies stale numbers (41% instead of 43%).
> **Part B diff:** activity, past updates, and roadmap **flipped to retrieve**; norms + task stay long-context. Memory gets TTLs and forgetting (§4).

## 1. Context budget

Each iteration receives, in **priority order** (if something has to be cut, it goes from the bottom):

1. **Team norms**: the rules every draft must obey
2. **Task brief**: what is being asked
3. **This project's activity, this week**: the facts every claim must cite
4. **Roadmap slice**: this project only, CONFIDENTIAL items filtered out
5. **Latest 1–2 past updates**: format/precedent only, never a source of current numbers

**Target:** ≈ 8k tokens per iteration.

## 2. Retrieve vs. long-context: per source

For each data source, decide: **retrieve** (narrow a large/changing corpus to the relevant slice) or **long-context** (just include a bounded set you can reason over).

| Source | Size / volatility | Decision | Why |
|---|---|---|---|
| `get_activity` (GitHub/Jira activity) | Grows weekly; changes every run | **Retrieve**: this project, this week | Deciding factor: **citation/audit**. Every figure must trace to an item (#820, 43%); a bounded pull also stops the cross-project wandering seen in M2. |
| `search_past_updates` (past updates + decision log) | Unbounded; +1 entry/week | **Retrieve**: latest 1–2 for this project + related decisions | Deciding factor: **size**. History has no limit; including all of it puts stale 41% next to current 43%. |
| `get_roadmap` | Medium; slow-changing; CONFIDENTIAL flags | **Retrieve**: this project's slice, CONFIDENTIAL items (Orbit, Pulsar) filtered out | Deciding factor: **citation/audit**. Confidential flags must be enforced and traceable. |
| `get_norms` (team norms / playbook) | Bounded (~2 KB); rarely changes but must be current | **Long-context**: whole playbook, read fresh each run | Deciding factor: **size**. Small enough to include whole; a partial pull could miss a rule. |
| `get_task` (this week's task brief) | One static doc | **Long-context** | Deciding factor: **size**. Reason over the whole brief. |

*Decisions taken per Claude's recommendation, accepted by the learner.*

## 3. Retrieval quality plan

_Which of these apply, and how? (This is what separates modern agentic retrieval from naive "embed → top-k → stuff".)_

| Retrieved source | Failure mode | Routing | Doc grading | Reranking | Self-verification | Caching |
|---|---|---|---|---|---|---|
| `get_activity` | Wrong project (the M2 wander), or last week's numbers | ✅ only the task's project ID | ✅ keep only this week's items | | ✅ critic **B**: every figure must cite a pulled item | |
| `search_past_updates` | Stale precedent; its old numbers get copied | ✅ this project only | ✅ drop entries from other projects | ✅ newest first, keep the top 1–2 | ✅ critic **B**: numbers can't come from past updates | |
| `get_roadmap` | A confidential item leaks (Orbit, Pulsar) | ✅ this project's slice | ✅ drop anything marked CONFIDENTIAL before Cortex sees it | | ✅ critic **D**: no confidential item in the output | |

- **Caching:** not used yet. Runs happen once a week, so caching saves almost nothing and adds staleness risk. Revisit if runs become frequent.
- **No naive RAG:** every retrieved source has at least routing + grading + a verification check.
- *Plan decisions per Claude's recommendation, accepted by the learner.*

## 4. Memory map (your PM brain)

| Memory type | What Cortex stores | Scope / TTL | Who can write |
|---|---|---|---|
| **Working** (in-loop) | Task brief, pulled data, drafts, critic verdicts, loop counters | This run only; purged at the end | Cortex |
| **Episodic** (past runs) | **Approved** past updates, approved decisions (#4, #6), dedupe keys. Rejected drafts are never stored. | Per project. Updates: 12 weeks (retrieve latest 1–2). Dedupe keys: 2 weeks. Critic log: 90 days (for M5 evals). | Written **only after PM approval** (M1 line 8a) |
| **Semantic** (durable facts/prefs) | Team norms and roadmap facts are **not copied**: read fresh from the source each run. PM format preferences kept until the PM changes them. | No copy, so no TTL | Source owners / the PM |
| **Shared** (across agents: Cortex ↔ critic) | Source data + the draft for that run. The critic keeps nothing. | This run only | Neither agent persists it |

## 5. Memory risks & mitigations

| Risk | Where it hits Cortex | Mitigation |
|---|---|---|
| **Drift** | Format/tone gradually copies Cortex's own earlier updates | Only PM-approved updates stored; only top 1–2 retrieved; norms always override precedent |
| **Poisoning** | An instruction injected in a brief or notes gets saved as a "fact" | Task text never written to memory; only approved outputs kept; the brief is data, not instructions; a jailbreak attempt escalates (M5) |
| **Staleness** | Old numbers (41%) end up in this week's update | Numbers only from this week's activity (critic **B**); past updates for format only; 12-week TTL |
| **PII / retention / confidential** | Orbit or Pulsar leaks; names or draft history persist | CONFIDENTIAL filtered before Cortex sees it; per-project scope; `run-output/` + critic log gitignored, log TTL 90 days; no personal data or secrets logged |

*TTLs (12 weeks, 2 weeks, 90 days) carry forward as bounds to enforce in M5. Memory map and mitigations per Claude's recommendation, accepted by the learner.*
