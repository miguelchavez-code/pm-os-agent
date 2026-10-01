# Orchestration Map: Cortex PM Chief-of-Staff Agent

> Module 3 · Orchestration & Subagents, ★ Deliverable 3
>
> ✅ **What this validates:** nothing advances unchecked, by the end you'll have proven a justified topology, a roster, and a validator with a defined fail action.
>
> Builds on your M2 Loop Spec. Only split one agent into a team when there's a real reason, coordination has a cost.

## 1. Why split? (or why not)

**Current design:** Cortex is a single agent on a weekly cron (+ hook for ad-hoc requests): it pulls one project's data, drafts the status update, queues ≤10 stories, and an independent critic checks the draft before it stops at my review. Nothing is posted.

| Reason | Applies? | Why / why not |
|---|---|---|
| Separation of concerns | No | The jobs are related. |
| Parallelism | No | It will be sequential. |
| Independent validator | **Yes** | It needs to assess the verdict independently. |
| Context-window pressure | No | The data managed is not large. |

**Decision:** split only once: Cortex + one validator subagent. No wider team.

## 2. Topology

**Pattern:** **single + subagents** (Cortex + one critic)

```
[Cron weekly / Hook ad-hoc] → [Cortex: pulls 1 project's data, drafts update, queues ≤10 stories]
     → [Critic ✓ checks A–E]
          ├─ pass → [PM review checkpoint, 8a HITL] → queued (never auto-posted)
          ├─ fail A/B/E → back to Cortex with reasons (max 2 revisions) → STUCK, held for PM
          └─ fail C/D  → ESCALATE immediately to PM
```

## 3. Roster

| Agent / subagent | Responsibility | Runs which Loop Spec |
|---|---|---|
| **Cortex** | Pulls data, drafts the update, proposes stories, ends DONE or ESCALATE | M2 loop (cron + hook) |
| **Critic** (`critic.py`) | Checks the draft against A–E and returns pass/fail with reasons | Called once per draft, inside the M2 loop |

## 4. Communication & hand-offs

- **Cortex → Critic:** the proposed draft (text) + the source log (the pulled data).
- **Critic → Cortex:** a JSON verdict, `{"verdict": "pass" | "fail", "reasons": [...]}`. The loop code handles routing; Cortex never sees the critic's reasoning, only its reasons when a draft needs revising.
- **Protocol:** a plain in-process Python call. No MCP or A2A.

## 5. The validator

- **What the critic checks:**
  - **A.** Correct project + real PR/issue IDs from pulled data
  - **B.** Every figure and status call traceable to pulled data (no invented numbers)
  - **C.** No commitment Cortex may not make: no ship date, no status change unless it escalates (M1 #4)
  - **D.** No confidential/embargoed roadmap item; nothing posted, created, or merged
  - **E.** Story batch ≤10 and actually queued, or escalated
  - *Left out: F (status vs. open issues). It's not aligned with the strategy.*
- **Fail action (tiered):** **revise** on A/B/E (sent back with reasons) · **escalate immediately** on C/D (above-the-line, no retry) · **log** every verdict. Why: it has a more flexible structure.
- **Revision cap:** **2**, then STUCK, and the draft is held for the PM (`MAX_REVISIONS=2`). Why: based on what was agreed in previous labs.
- **Pass action:** the draft advances to the PM review checkpoint (8a HITL). It is never posted automatically.

## 6. State: shared vs isolated

- **Shared:** the pulled source data + the draft. That's the evidence the critic needs to check A–E.
- **Isolated:** the critic gets a fresh context each call with its own prompt. It never sees Cortex's conversation, system prompt, or reasoning (no inherited blind spots). Only the critic's *reasons* go back to Cortex.
- **Across runs:** the critic is stateless. Only Cortex keeps M2's across-run state (approved updates + decisions, per project).
- **Why:** this is what is important.

## 7. Cost & latency budget

- **Extra calls:** +1 critic call per draft (fresh context, `gpt-4o`).
- **Cost:** ~$0.01 per critic call; worst case at the revision cap (3 drafts → 3 critic calls) ≈ $0.03 extra per run. Cortex stays on `gpt-4o-mini`. Total stays far under the $0.50 per-run cap.
- **Latency:** ~3–6 s per critic call; worst case ≈ 15 s before a draft reaches the PM. Acceptable for a weekly job.
- **Why:** to maintain lower cost: only the critic gets the stronger model; Cortex stays on mini.
- **Known gap → M5:** the code prices every call at mini rates, so the cost bound understates critic spend. This needs per-model pricing in M5 bounds (`05-bounds-evals/bounds-and-evals.md`).
