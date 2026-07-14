# AlbionFisher

Assistant tooling for **Albion Online** fishing — built with [loop engineering](https://addyosmani.com/blog/loop-engineering/) in Cursor.

**Repository:** https://github.com/Nizelan/AlbionFisher

## Status

Early setup: loop scaffold (subagents, skills, state files) is in place; application code TBD.

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

1. Push this scaffold to GitHub (script above).
2. Choose stack (e.g. C#, Python, Electron) and record build/test commands in a new skill.
3. Set first goal in `progress.md`.
4. Optional: [Cursor Automations](https://cursor.com/docs/cloud-agent/automations) for daily triage or CI triggers.

## License

TBD
