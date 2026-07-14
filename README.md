# AlbionFisher

Assistant tooling for **Albion Online** fishing — built with [loop engineering](https://addyosmani.com/blog/loop-engineering/) in Cursor.

**Repository:** https://github.com/Nizelan/AlbionFisher

> ## ⚠ Terms of Service warning
>
> Automating gameplay **violates the Albion Online Terms of Service** and can
> get your account **permanently banned**. Anti-cheat systems may detect
> synthetic input. This software is developed and used **solely at the
> owner's own risk and responsibility** (see `docs/SPEC.md` §9). Do not use it
> on an account you are not prepared to lose.

## Status

MVP scaffold implemented: window capture, YOLO detection wrapper, fishing FSM,
input control, PySide6 GUI, unit tests. Needs owner-trained model weights in
`model/albionfisher.pt` to actually detect anything (see `docs/SPEC.md` §4).

## Install

Requires **Windows 10/11** and **Python 3.11+**.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt        # runtime (ultralytics/torch are heavy)
pip install -r requirements-dev.txt    # pytest + ruff, for development
```

Drop your trained model into `model/albionfisher.pt`. Class list must match
`model/classes.yaml` — the app verifies this at startup and warns on mismatch.
Without weights the app still starts, in degraded mode with a warning banner.

## Run

```powershell
python -m albionfisher
```

1. Pick the Albion Online window from the dropdown (Refresh if empty).
2. Press **Start**. **F10** is the global emergency stop — it releases all
   inputs immediately from any state.
3. Tune settings in `config/settings.yaml` (confidence, timeouts, cast
   strength, stop conditions) or via the GUI fields before starting.

## Test & lint

```powershell
pytest          # pure unit tests: FSM, minigame controller, config, class contract
ruff check .    # lint
```

Unit tests need only `pytest` + `PyYAML` — no GPU, game, or Qt required.

## Loop engineering

This repo is designed for autonomous cycles:

| Piece | Location |
|-------|----------|
| Loop guide | [`AGENTS.md`](AGENTS.md) |
| Backlog & state | [`progress.md`](progress.md) |
| Subagents | [`.cursor/agents/`](.cursor/agents/) |
| Triage skill | [`.cursor/skills/triage/`](.cursor/skills/triage/) |

Typical flow: **triage → architect → developer → verifier** → update `progress.md` → PR.

## Connect local folder to GitHub

Git is required. If not installed: [Git for Windows](https://git-scm.com/download/win).

From this directory in PowerShell:

```powershell
.\scripts\connect-github.ps1
```

Or manually:

```powershell
git init
git remote add origin https://github.com/Nizelan/AlbionFisher.git
git add .
git commit -m "chore: loop engineering scaffold for AlbionFisher"
git branch -M main
git push -u origin main
```

Use SSH if you prefer: `git@github.com:Nizelan/AlbionFisher.git`

## Next steps

1. Owner: train the YOLO model on `model/classes.yaml` classes and drop
   `albionfisher.pt` into `model/` (AF-5).
2. Live tuning of minigame deadzone/hysteresis and timeouts against the game.
3. Optional: [Cursor Automations](https://cursor.com/docs/cloud-agent/automations) for daily triage or CI triggers.

## License

TBD
