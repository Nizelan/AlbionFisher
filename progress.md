# AlbionFisher — Loop State

> Persistent memory for loop engineering. Agents read and update this file each cycle.
> Do not rely on chat history — the repo is the source of truth.

## Current focus

- **Goal:** MVP scaffold done and verified → next: owner trains model (AF-5), then live gameplay validation
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
| AF-6 | Architect plan: project scaffold (capture/detection/control/fsm/ui) | high | done | Plan approved and implemented in AF-8 |
| AF-7 | Confirm minigame mechanics (SPEC §10 Q1) | medium | done | Owner: float drifts left; hold LMB moves right |
| AF-8 | Implement MVP scaffold per architect plan | high | done | Verified 2026-07-14: pytest 41/41, ruff clean, compileall OK, lazy imports OK |
| AF-9 | Live gameplay validation (SPEC §8 items 3-4) once model arrives | high | blocked | Blocked by AF-5 (owner's model) |

## In progress

_(none — next actionable item is AF-5, owned by the human)_

## Done (recent)

| ID | Task | Completed | PR / commit |
|----|------|-----------|-------------|
| AF-8 | MVP scaffold (config/capture/detection/control/fsm/ui + 41 unit tests) | 2026-07-14 | verified: pytest 41/41, ruff clean, compileall OK, lazy-import probe OK |
| AF-6 | Architect plan for scaffold | 2026-07-14 | plan in loop transcript; implemented in AF-8 |
| — | Loop engineering scaffold | — | initial |

### AF-8 verification record (2026-07-14)

- `pytest -q` → 41 passed (FSM transitions, cast retry cap, bite timeout, fail streak, minigame decide, config, class contract).
- `ruff check .` → clean after fixing 37 lint findings (modern type annotations, unused imports).
- `compileall albionfisher` → OK; lazy-import probe → no heavy libs imported by pure modules.
- Verifier static review: FSM matches SPEC §5 incl. confirmed minigame mechanic; degraded no-model mode present.
- Not verifiable yet (needs model, AF-9): live cast targeting, bite reaction, minigame loop — marked `# NEEDS-MODEL`.
- Known follow-up: `RESULT_WINDOW_S` (2 s) and `MAX_CAST_ATTEMPTS` (3) are constants in `fsm/machine.py`, not config.

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
