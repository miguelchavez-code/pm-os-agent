"""Cortex, a minimal, explicit agent loop you (and your coding agent) can read end
to end. This is the agent you ship: your PM chief-of-staff. You build it by
directing your coding agent (Claude Code / Cursor / Codex) to shape this file. You
never have to hand-write it.

Every bound the course talks about is visible right here in code, not buried in a
framework: the max-iteration counter, the cost cap, the revision cap, the
stop/escalate conditions, the auto-queue cap, and the absence of any publish tool.

Usage (ask your coding agent to run these for you, or run them yourself):
    python agent.py                # runs the happy-path task (weekly status update)
    python agent.py missing-data   # the stuck/escalate case
    python agent.py jailbreak       # the prompt-injection refusal case

Every run ends by showing the drafted status update in a FINAL STATUS UPDATE block
(or LAST DRAFT, held, if a bound trips), and saves it to run-output/. That file is
always a draft held for a human, it is never posted, there is no publish tool.

Requires OPENAI_API_KEY in your environment (see .env.example). Model and bounds
are read from env so you can tune them, that tuning is your M5 deliverable.

The loop is deliberately transparent (hand-written tool-calling on the openai
client) so a grader can see the machinery. Keep the bounds explicit if you rework it.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from openai import OpenAI

import tools
from critic import review
from prompts import CORTEX_SYSTEM

try:  # load .env if python-dotenv is installed; harmless if it isn't
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# --- Bounds (your M5 deliverable: tune these and justify them) ----------------
MODEL = os.environ.get("CORTEX_MODEL", "gpt-4o-mini")
# M3: the critic can run on its own (stronger) model; defaults to Cortex's model.
CRITIC_MODEL = os.environ.get("CORTEX_CRITIC_MODEL", MODEL)
MAX_ITERATIONS = int(os.environ.get("CORTEX_MAX_ITERATIONS", "8"))
MAX_REVISIONS = int(os.environ.get("CORTEX_MAX_REVISIONS", "2"))
COST_CAP_USD = float(os.environ.get("CORTEX_COST_CAP_USD", "0.50"))
MAX_QUEUE_ITEMS = int(os.environ.get("CORTEX_MAX_QUEUE_ITEMS", "10"))
# M2 loop spec, stuck exit: give up after this many failed data pulls.
MAX_PULL_FAILURES = int(os.environ.get("CORTEX_MAX_PULL_FAILURES", "3"))
PULL_TOOLS = {"get_project", "get_activity"}
# M3 test switch: corrupt Cortex's FIRST draft to prove the critic catches it.
# Off unless set. "metric" -> invented figure (check B); "date" -> commitment (check C).
INJECT_BAD_DRAFT = os.environ.get("CORTEX_INJECT_BAD_DRAFT", "").strip().lower()
BAD_LINES = {
    "metric": "\n\n**Customer sentiment:** NPS rose to 62 this week (up from 48).",
    "date": "\n\n**Commitment:** GA ships to all customers on August 15, 2026.",
}
# Rough $ per 1M tokens for your chosen model, set to match its pricing.
PRICE_IN = float(os.environ.get("CORTEX_PRICE_IN_PER_M", "0.15"))
PRICE_OUT = float(os.environ.get("CORTEX_PRICE_OUT_PER_M", "0.60"))

TOOL_SCHEMAS = [
    {"type": "function", "function": {
        "name": "get_project", "description": "Look up a project by its ID (status, flags, linked PRD).",
        "parameters": {"type": "object", "properties": {
            "project_id": {"type": "string"}}, "required": ["project_id"]}}},
    {"type": "function", "function": {
        "name": "get_activity",
        "description": "Pull recent engineering activity for a project (merged PRs, open issues, Sev-1s).",
        "parameters": {"type": "object", "properties": {
            "project_id": {"type": "string"}}, "required": ["project_id"]}}},
    {"type": "function", "function": {
        "name": "search_past_updates",
        "description": "Search previous status updates and decisions for tone and precedent.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {
        "name": "get_roadmap",
        "description": "Return the roadmap. Some items are flagged confidential/embargoed.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {
        "name": "get_norms", "description": "Return the team norms / PM playbook the agent must follow.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {
        "name": "propose_stories",
        "description": "Queue a set of backlog stories for human approval (creates nothing; rejected above the item cap).",
        "parameters": {"type": "object", "properties": {
            "project_id": {"type": "string"},
            "stories": {"type": "array", "items": {"type": "string"}},
            "reason": {"type": "string"}}, "required": ["project_id", "stories"]}}},
]


class Bounds:
    """Tracks spend and trips the cost cap. This is enforced OUTSIDE the model."""

    def __init__(self):
        self.cost = 0.0

    def add(self, usage) -> None:
        self.cost += (usage.prompt_tokens * PRICE_IN
                      + usage.completion_tokens * PRICE_OUT) / 1_000_000

    def over_cap(self) -> bool:
        return self.cost >= COST_CAP_USD


OUTPUT_DIR = Path(__file__).parent / "run-output"


def log_verdict(which: str, step: int, revisions: int, verdict: dict) -> None:
    """M3 fail action 'log': append every critic verdict to run-output/critic-log.jsonl."""
    import datetime
    OUTPUT_DIR.mkdir(exist_ok=True)
    rec = {"ts": datetime.datetime.now().isoformat(timespec="seconds"), "task": which,
           "step": step, "revisions_so_far": revisions,
           **{k: v for k, v in verdict.items() if k != "_usage"}}
    with open(OUTPUT_DIR / "critic-log.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")


def banner(text: str) -> None:
    print(f"\n{'=' * 64}\n{text}\n{'=' * 64}")


def emit_deliverable(which: str, draft: str, *, accepted: bool,
                     reason: str, cost: float) -> None:
    """Surface AND persist Cortex's drafted status update so it can't get lost in
    the scroll-back. This is still a DRAFT held for human review, never a post,
    there is no publish tool, and an escalated run is held on purpose.

    Runs on every exit: an accepted pass prints the FINAL update; a bound trip or
    escalation prints the LAST draft it managed to write plus why it was held.
    """
    banner("FINAL STATUS UPDATE (draft, validator-approved, NOT posted)" if accepted
           else "LAST DRAFT (held, NOT posted, escalated to a human)")
    if draft.strip():
        print(draft.rstrip())
    else:
        print("(Cortex stopped before it produced a draft, nothing to show.)")
    if not accepted:
        print(f"\nWhy it was held: {reason}")

    if draft.strip():
        OUTPUT_DIR.mkdir(exist_ok=True)
        out = OUTPUT_DIR / f"status-update-{which}.md"
        state = "accepted by validator" if accepted else "HELD, escalated"
        out.write_text(
            f"<!-- Cortex draft, {state}; NOT posted. Run cost ~ ${cost:.4f}. -->\n"
            f"<!-- {reason} -->\n\n{draft.rstrip()}\n", encoding="utf-8")
        print(f"\nSaved draft -> {out.relative_to(Path(__file__).parent)}  "
              f"(for your review, nothing was posted)")


def run(which: str = "happy") -> None:
    client = OpenAI()
    bounds = Bounds()
    task = tools.get_task(which)
    if "error" in task:
        print(task)
        return

    banner(f"CORTEX RUN, fixture: task-{which}  (auto-queue cap {MAX_QUEUE_ITEMS} items)")
    print(task["body"])

    messages = [
        {"role": "system", "content": CORTEX_SYSTEM},
        {"role": "user", "content": f"PM task brief:\n\n{task['body']}"},
    ]
    source_log: list[str] = [task["body"]]
    revisions = 0
    last_draft = ""
    # M2 loop-spec state (within-run layer, purged when the run ends).
    pull_failures = 0
    queued_count: int | None = None      # set when propose_stories confirms a queue
    batch_rejected = False               # set when the queue cap rejects a batch
    stories_requested = "stor" in task["body"].lower()

    for step in range(1, MAX_ITERATIONS + 1):
        if bounds.over_cap():
            reason = f"cost cap ${COST_CAP_USD} hit at ${bounds.cost:.4f}"
            banner(f"BOUND TRIPPED, {reason}. Halting and escalating to a human.")
            emit_deliverable(which, last_draft, accepted=False,
                             reason=reason, cost=bounds.cost)
            return

        resp = client.chat.completions.create(
            model=MODEL, messages=messages, tools=TOOL_SCHEMAS)
        bounds.add(resp.usage)
        msg = resp.choices[0].message

        if msg.tool_calls:
            messages.append(msg)
            for call in msg.tool_calls:
                fn = call.function.name
                args = json.loads(call.function.arguments or "{}")
                result = tools.TOOLS[fn](**args)
                source_log.append(f"{fn}({args}) -> {json.dumps(result)}")
                print(f"\n[step {step}] TOOL {fn}({args})")
                print(f"          -> {json.dumps(result)[:300]}")
                messages.append({"role": "tool", "tool_call_id": call.id,
                                 "content": json.dumps(result)})
                # M2 loop-spec signals, detected in code, not by the model.
                if fn in PULL_TOOLS and "error" in result:
                    pull_failures += 1
                    print(f"          !! data pull failed ({pull_failures}/{MAX_PULL_FAILURES})")
                if fn == "propose_stories":
                    if result.get("status") == "queued_for_approval":
                        queued_count = result.get("count", 0)
                    elif result.get("error") == "batch_exceeds_queue_cap":
                        batch_rejected = True
            if pull_failures >= MAX_PULL_FAILURES:
                reason = f"STUCK: data pull failed {pull_failures}x"
                banner(f"STUCK, data pull failed {pull_failures}x. Stopping, logging, "
                       f"holding the draft for a human. Run cost ≈ ${bounds.cost:.4f}")
                emit_deliverable(which, last_draft, accepted=False,
                                 reason=reason, cost=bounds.cost)
                return
            continue

        # No tool calls => Cortex produced a proposed output. Validate it.
        proposed = msg.content or ""
        if INJECT_BAD_DRAFT in BAD_LINES and revisions == 0:
            proposed += BAD_LINES[INJECT_BAD_DRAFT]
            msg.content = proposed  # Cortex "owns" the bad line, so it must fix it
            print(f"\n[test] injected bad line ({INJECT_BAD_DRAFT}) into draft #1")
        last_draft = proposed
        # Escalate exit (M2 spec): Cortex chose ESCALATE, or infra rejected the batch.
        is_escalate = proposed.lstrip().upper().startswith("ESCALATE") or batch_rejected
        print(f"\n[step {step}] PROPOSED OUTPUT:\n{proposed}")

        banner(f"CRITIC, independent validation ({CRITIC_MODEL})")
        verdict = review(client, CRITIC_MODEL, proposed, "\n".join(source_log))
        # Estimate critic spend too.
        bounds.cost += (verdict["_usage"]["prompt"] * PRICE_IN
                        + verdict["_usage"]["completion"] * PRICE_OUT) / 1_000_000
        print(json.dumps({k: v for k, v in verdict.items() if k != "_usage"}, indent=2))
        log_verdict(which, step, revisions, verdict)

        # M3 tiered fail action: C (commitment) / D (leak or action) are above the
        # agent line, so escalate immediately, no retry. A/B/E fall through to revise.
        failed = {str(c).upper() for c in verdict.get("failed_checks", [])}
        if verdict["verdict"] == "fail" and failed & {"C", "D"}:
            hit = ", ".join(sorted(failed & {"C", "D"}))
            banner(f"ESCALATE (critic failed check {hit}, above the agent line). No retry, "
                   f"held for the PM. Nothing posted. Run cost ≈ ${bounds.cost:.4f}")
            emit_deliverable(which, proposed, accepted=False,
                             reason=f"ESCALATE: critic failed {hit}", cost=bounds.cost)
            return

        if verdict["verdict"] == "pass" and is_escalate:
            why = ("story batch over the queue cap" if batch_rejected
                   else "Cortex hit a human-owned decision (#4 / #6)")
            banner(f"ESCALATE (HITL), {why}. Stopping and asking the PM. "
                   f"Nothing posted. Run cost ≈ ${bounds.cost:.4f}")
            emit_deliverable(which, proposed, accepted=False,
                             reason=f"ESCALATE: {why}", cost=bounds.cost)
            return

        missing_queue = stories_requested and queued_count is None
        if verdict["verdict"] == "pass" and not missing_queue:
            n = queued_count or 0
            banner(f"SUCCESS, HITL CHECKPOINT: draft + {n} stories ready for your "
                   f"review. Nothing posted, no commitments made. "
                   f"Run cost ≈ ${bounds.cost:.4f}")
            emit_deliverable(which, proposed, accepted=True,
                             reason=f"critic passed + {n} stories queued", cost=bounds.cost)
            return

        if revisions >= MAX_REVISIONS:
            reason = (f"STUCK: not done after {MAX_REVISIONS} revisions "
                      f"({'stories never queued' if verdict['verdict'] == 'pass' else 'critic rejected'})")
            banner(f"STUCK, revision cap hit ({MAX_REVISIONS}). Holding the draft for "
                   f"a human instead of looping. Run cost ≈ ${bounds.cost:.4f}")
            emit_deliverable(which, last_draft, accepted=False,
                             reason=reason, cost=bounds.cost)
            return

        revisions += 1
        messages.append(msg)
        if verdict["verdict"] == "pass":  # good draft, but success needs the queue too
            print(f"\n-> critic passed, but no stories queued; revision {revisions}/{MAX_REVISIONS}")
            messages.append({"role": "user", "content":
                             "The draft passed review, but the task asked for stories and "
                             "none are queued. Call propose_stories, or ESCALATE."})
        else:
            print(f"\n-> critic rejected; revision {revisions}/{MAX_REVISIONS}")
            messages.append({"role": "user", "content":
                             "A validator rejected that for these reasons: "
                             f"{verdict['reasons']}. Fix it or escalate."})

    banner(f"STUCK, max iterations ({MAX_ITERATIONS}) reached without finishing. "
           f"Holding for a human. Run cost ≈ ${bounds.cost:.4f}")
    emit_deliverable(which, last_draft, accepted=False,
                     reason=f"STUCK: max iterations ({MAX_ITERATIONS}) reached",
                     cost=bounds.cost)


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "happy")
