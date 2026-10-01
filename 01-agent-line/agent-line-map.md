# Agent Line Map: Cortex PM Chief-of-Staff Agent

> Module 1 · The Agent Line
>
> ✅ **What this validates:** every risky action has a clear owner, by the end you'll have proven an above/below-the-line map with HITL checkpoints, scored on reversibility, blast radius, and measurability.

## The workflow, decision by decision

List every discrete decision or action in your agent's workflow, then score each one and place it **above** the line (a human owns it) or **below** (the agent owns it). Borderline calls get an HITL checkpoint.

| Decision / action | Reversibility (H/M/L) | Blast radius (H/M/L) | Measurability (H/M/L) | Above / Below | HITL? |
|---|---|---|---|---|---|
| 1. Pull project state + activity | H | L | H | Below | · |
| 2. Decide relevant context | H | M | L | HITL | required: approve context + exclusion list |
| 3. Draft the update | H | L | M | Below | · (gated at 8a) |
| 4. Decide tone / commitment level | L | H | L | HITL | required: approve tone + commitments |
| 5. Flag at-risk / escalation | H | L | M | Below | · |
| 6. Choose what to escalate | L | H | M | HITL | required: approve each escalation |
| 7. Propose a story batch (capped) | H | M | M | Below | · (human picks stories at sprint planning) |
| 8a. Post an update (team/project channel) | M | M | M | HITL | required: approve before posting |
| 8b. Approve a company-wide update | L | H | M | Above | human-only, Cortex never approves |

## Agent anatomy (sketch)

- **Model:** `gpt-4o-mini` by default, due to the nature of the task. Escalate to a frontier model for #4 (tone/commitment) and #6 (what to escalate), or after the critic rejects twice.
- **Tools:** read-only `get_project`, `get_activity`, `search_past_updates`, `get_roadmap`, `get_norms` · capped write `propose_stories` (≤10/run) · **no posting tool**, so 8a/8b can't be bypassed by the agent.
- **Memory:** persists roadmap, team norms, approved past updates, approved decisions (escalations, tone/commitment calls) · purged each run: activity snapshots, rejected drafts, critic exchanges. Only approved outputs are kept, so no irrelevant data persists.
- **Loop:** _placeholder, defined in M2 loop-spec.md_
- **Bounds:** _placeholder, defined in M5 bounds-and-evals.md_
- **Evals:** _placeholder, defined in M5 bounds-and-evals.md_

## The golden rule, applied

1. **Pull project state + activity** sits **below** the line because it's high reversibility to reverse (read-only, re-runnable), has a low blast radius, and is highly measurable against the source. Deciding factor: **reversibility**.
2. **Decide relevant context** is **HITL** because, though highly reversible, it's low measurability: a reviewer can't see what was left out, so Cortex lists its exclusions to avoid missing important information. Deciding factor: **measurability**.
3. **Draft the update** sits **below** the line because an unposted draft is highly reversible, has a low blast radius until 8a, and is medium measurability; gating it here would mean the review happens twice. Deciding factor: **reversibility**.
4. **Decide tone / commitment level** is **HITL** because a commitment to leadership is low reversibility, has a high blast radius, and is low measurability until weeks later. Deciding factor: **reversibility**.
5. **Flag at-risk / escalation** sits **below** the line because a flag is just a marker: highly reversible, low blast radius, medium measurability. Deciding factor: **blast radius**.
6. **Choose what to escalate** is **HITL** because an escalation is low reversibility and has a high blast radius; it needs a person's judgement to communicate to other people and teams. Deciding factor: **blast radius**.
7. **Propose a story batch (capped)** sits **below** the line because it's just a proposal: highly reversible, cap-bounded blast radius, medium measurability against the PRD. Deciding factor: **reversibility**.
8a. **Post an update (team/project channel)** is **HITL** because it's medium reversibility with a limited audience, so the impact of the communication is moderate. Deciding factor: **blast radius**.
8b. **Approve a company-wide update** sits **above** the line because it's low reversibility and reaches the whole company: the highest blast radius in the workflow. Deciding factor: **blast radius**.

## Hardest call

**#2, Decide relevant context.** On first pass I placed it **below** the line: *"it is a recommendation to be reviewed by a human."* Scoring exposed the gap: a reviewer sees what Cortex *included*, not what it *left out*, so measurability is **Low**. I moved it to **HITL**, with Cortex listing its exclusions, *"just to avoid missing any important information."* **Deciding axis: measurability.**
