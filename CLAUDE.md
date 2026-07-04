# BotTO repository rules

- Reply in **English** by default.
- Explain the "why" and "what" before changing files.
- Prefer the simplest solution that fits the problem.
- Memory pointers in `pointers.py` must be validated after TO updates.
- Never touch passwords, autologin, or friends' accounts without explicit confirmation.
- Use `PROJECT_PLAN.md` as the canonical status/roadmap document.
- Keep `README.md` short; do not duplicate the full plan there.

## Subagents

Use the agents in `.claude/agents/` when a task is bounded enough to delegate safely. The usual picks are:

- `memory-pointer-finder` — pointer validation
- `class-rotation-designer` — class rotations
- `ocr-helper` — Tesseract/OCR tuning
- `discord-integrator` — webhook and alert work
- `safety-auditor` — check changes against repo rules
- `cheat-engine-companion` — Cheat Engine guidance
- `talisman-online-specialist` — game knowledge

## Security

- Bot never reads or writes game passwords.
- Game client only from the official site.
- Review upstream diffs before merging.
- Keep long daily breaks and avoid ranking-chasing.
- Full security context lives in `PROJECT_PLAN.md`.

## Links

- `README.md` — quick project overview
- `PROJECT_PLAN.md` — canonical plan and progress
- `INDEX.md` — navigation
