# AlbionFisher — Agent Loop Guide

This repository uses **loop engineering**: scheduled discovery, delegated subagents, verification, and persistent state — not one-off prompting.

**Remote:** https://github.com/Nizelan/AlbionFisher.git

## Loop shape

```
Automation (cron / GitHub CI / manual)
  → read progress.md + triage skill
  → for each actionable item:
      architect (plan, readonly) → developer (implement) → verifier (test, skeptical)
      → update progress.md → open PR if applicable
  → human review for anything outside automation scope
```

## State files

| File | Purpose |
|------|---------|
| `progress.md` | Backlog, in-progress, done, blockers, triage log |
| `AGENTS.md` | This file — loop design and conventions |
| `.cursor/agents/` | Role-specific subagents |
| `.cursor/skills/` | Repeatable procedures (triage, etc.) |

## Subagents

| Agent | Role | When to use |
|-------|------|-------------|
| `triage` | Scan CI, issues, recent commits; write findings to `progress.md` | Start of each loop cycle |
| `researcher` | UX, acceptance criteria, external docs | New features, unclear requirements |
| `architect` | Technical plan only (readonly) | Before non-trivial implementation |
| `developer` | Implementation | After plan is approved or for small fixes |
| `verifier` | Run tests, lint, skeptical review | After every implementation claim |

Invoke explicitly: `/verifier confirm tests pass`, `/architect plan auth module`.

## Conventions

- Update `progress.md` at the end of every loop iteration.
- Verifier must run before marking a task `done`.
- Prefer small PRs; one backlog item per PR when possible.
- Do not commit secrets (`.env`, keys). See `.gitignore`.
- When stack/language is chosen, document build and test commands in a skill under `.cursor/skills/`.

## Cursor Automations (cloud)

Suggested automations once the codebase exists:

1. **Daily triage** — cron; prompt calls `$triage`; updates `progress.md`.
2. **CI failure** — GitHub `CI completed` trigger; developer + verifier subagents; comment or PR.
3. **PR review assist** — on PR opened; readonly review against acceptance criteria.

Create via Agents Window, [cursor.com/automations](https://cursor.com/automations), or `/automate` in chat.

## Human responsibilities

- Define goals and acceptance criteria in `progress.md`.
- Review PRs and verifier output — loops do not replace judgment.
- Regenerate automation webhook keys after scope changes (see Cursor docs).
