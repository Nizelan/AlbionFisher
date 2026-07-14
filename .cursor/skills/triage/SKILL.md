---
name: triage
description: Triage procedure for loop cycles — CI, backlog, and progress.md updates. Use from automations or /loop runs.
---
# Triage (AlbionFisher)

Run at the start of a loop cycle.

## Steps

1. Read `AGENTS.md` and `progress.md`.
2. If a codebase exists: run build/test/lint; note failures.
3. Scan GitHub issues and recent commits (via `gh` or git log when available).
4. Update **Triage log** and **Backlog** in `progress.md`.
5. Recommend the single highest-priority item for `/developer` next.

## Output

Short markdown summary for the orchestrating agent or automation inbox:
- Critical issues (must fix)
- Scheduled work
- Suggested next action

Do not implement fixes in triage.
