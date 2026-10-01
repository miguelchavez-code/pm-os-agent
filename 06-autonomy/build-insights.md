# Build Insights: Cortex PM Chief-of-Staff Agent

> Module 6 · ★ Deliverable 4, what you learned building it
>
> ✅ **What this validates:** you can reflect on what building it taught you, by the end you'll have proven the friction, the learning, and the aha that changes how you'd design your next agent.

## Friction

- Environment setup cost more than the agent design: macOS's protected Python needed a virtual environment, the sandbox blocked OpenAI until I allowed the domain, and GitHub pushes needed GitHub Desktop.
- The cheap critic model mislabelled checks and invented problems.
- Cortex quietly wandered into other projects' data when its own project was missing.

## Learning

1. A bound only counts if code enforces it; a prompt sentence is a wish.
2. The validator's *model* matters as much as its checks.
3. Every source needs a retrieve-or-include decision, or stale numbers creep in (41% vs. 43%).

## Aha moment

Drawing the agent line before building made every later decision easier. "No posting tool" did more for safety than any prompt.

## What you'd do differently

Write the eval cases (M5) first and build to pass them; scope retrieval to one project from day one; add a code-level injection check before drafting.
