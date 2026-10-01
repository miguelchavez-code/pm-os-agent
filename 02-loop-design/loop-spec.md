# Loop Spec: Cortex PM Chief-of-Staff Agent

> Module 2 · Loop Engineering, ★ Deliverable 2
>
> ✅ **What this validates:** the agent knows when to run and when to stop, by the end you'll have proven a one-page Loop Spec with a trigger, a definition of "done," and explicit stop conditions.
>
> Your one-page blueprint for how the work you handed to the agent (M1) actually *runs*.
> An agent is just a prompt that fires itself, this spec says when it fires, what "done" means, and what it needs to do the job. Living document; refine as the course progresses.

## 1. Trigger & loop type

**Chosen type:** **cron** (primary) + **hook** (backup)

**Why:** cron will create the schedule based on the current process (weekly leadership update) and a hook in case I get a notification (ad-hoc request).

**Ruled out:** heartbeat and goal: the others will have the agent running constantly without a need.

**Idempotency / dedupe:** one draft per *project ID + ISO week* for cron runs; *message ID* for hook runs. A duplicate trigger is logged and skipped, not re-drafted.

## 2. Goal / definition of done

A status update grounded in pulled activity has passed the critic, and the story batch (≤10) is queued. Both are waiting for PM approval at 8a. **Cortex never posts.** Why: you will have the recommendation ready for review. It will save you one step if you decide to approve.

## 3. Stop conditions

| Condition | What it looks like | What happens |
|---|---|---|
| **Success** | Critic returns `pass` **and** `propose_stories` confirms the batch is queued | Stop + notify PM: "draft + N stories ready for review". *Makes it a finite loop.* |
| **Stuck / give up** | A data pull fails 3×, **or** the critic rejects 2× (`MAX_REVISIONS`), **or** 8 iterations pass without success (`MAX_ITERATIONS`) | Stop, log the reason, hold the last draft (not posted), notify PM. *To avoid infinite loops.* |
| **Escalate to human** | A date or status change Green→Amber/Red (#4), an at-risk flag that needs routing (#6), or a story batch over the cap of 10 (#7) | HITL checkpoint from agent-line-map: stop and ask the PM. Batches over the cap are rejected, not trimmed. *To keep alignment to our initial decisions.* |

**Observed (M2 re-run, `missing-data`):** after 2 failed pulls for `P-HALO`, Cortex wandered to other projects' activity (P-VEGA, P-NORTH, P-ORBIT). Those pulls succeeded, so the 3-failure exit never fired, and the 8-iteration cap halted it as STUCK. This also breaks §4's one-project scope. **Fix planned:** restrict pulls to the task's project (M4 context / M5 bounds). **✅ Fixed in M4:** project-scoped retrieval in `agent.py` (`call_tool`). Out-of-project pulls now count as failed pulls, so `missing-data` hits the 3-failure STUCK exit in 3 steps instead of 8.

## 4. State

Per project, in two layers. **Within a run:** iteration count, revision count, pull retries, the current draft, and critic verdicts, all purged when the run ends. **Across runs:** dedupe keys (project + ISO week, message IDs), approved past updates, and approved decisions (#4, #6). **Scope:** one project. Nothing is shared between projects, so a confidential project can't leak. Why: it provides more visibility and context to the agent.

## 5. The five things a loop can lean on

_`state` is always-on. `connectors` only if you already have one wired (e.g. a Jira key or Google MCP), otherwise just note it as a plan. `skills`, `subagents`, `work tree` scale with autonomy; "not needed yet, because…" is a valid answer._

| Component | For Cortex |
|---|---|
| **Work tree** (isolated workspace per run, a git worktree) | Not needed yet, because Cortex only reads data and writes to a queue; it never edits code or files. |
| **Skills** (reusable capabilities) | Not needed yet, because there's one workflow and `prompts.py` covers it. Revisit if the format is reused across projects. |
| **Plugins / connectors** (tools & access, optional if you don't have one yet) | Plan only: Cortex reads fixtures today. Planned: Jira/GitHub for activity, Slack for the hook trigger. |
| **Subagents** (independent check when the loop can't grade itself) | `critic.py` already validates independently, so Cortex doesn't grade itself. Full design → M3 `orchestration-map.md`. |
| **State tracking** | Per-project two-layer state (see §4). |

> Context plan (M4) and the hand-off to bounds & evals (M5) come in later modules, you'll add them to their own deliverables then, not here.

## Link to live loop

[`00-build/agent.py`](../00-build/agent.py)
