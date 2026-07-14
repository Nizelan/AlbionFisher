# AlbionFisher — Loop State

> Persistent memory for loop engineering. Agents read and update this file each cycle.
> Do not rely on chat history — the repo is the source of truth.

## Current focus

- **Goal:** Spec approved → architect plan for MVP scaffold (capture + detection + FSM + UI)
- **Status:** `in_progress`
- **Last updated:** 2026-07-14

## Backlog

| ID | Task | Priority | Status | Notes |
|----|------|----------|--------|-------|
| AF-1 | Push loop scaffold to GitHub | high | done | `f8a1fbb` on `origin/main` |
| AF-2 | Choose stack — decided: Python 3.11+, ultralytics YOLO, PySide6 UI | high | done | See `docs/SPEC.md` §3 |
| AF-3 | Write program specification from owner description | high | done | `docs/SPEC.md` v0.1 |
| AF-4 | Define YOLO class list for training | high | done | `model/classes.yaml` (7 classes) |
| AF-5 | Owner: train YOLO model, drop `albionfisher.pt` into `model/` | high | pending | External — owner's dataset |
| AF-6 | Architect plan: project scaffold (capture/detection/control/fsm/ui) | high | pending | Next loop step |
| AF-7 | Confirm minigame mechanics (SPEC §10 Q1) | medium | done | Owner: float drifts left; hold LMB moves right |

## In progress

_(none)_

## Done (recent)

| ID | Task | Completed | PR / commit |
|----|------|-----------|-------------|
| — | Loop engineering scaffold | — | initial |

## Blockers

_(none)_

## Triage log

<!-- Automations and /loop runs append findings here -->

| Date | Source | Finding | Action taken |
|------|--------|---------|--------------|
| — | — | — | — |

## Decisions

<!-- Architecture and product decisions the loop must not re-litigate -->

- Loop engineering scaffold committed; subagents in `.cursor/agents/`.
- 2026-07-14 — Stack: Python 3.11+ / ultralytics YOLO / PySide6; vision-only (no memory reading). See `docs/SPEC.md`.
- 2026-07-14 — YOLO classes fixed in `model/classes.yaml`; ID changes require retrain + progress.md note.
- 2026-07-14 — Minigame mechanics confirmed by owner: float always drifts left, holding LMB moves it right (SPEC §5).
