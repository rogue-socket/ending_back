# Host adapters

The backend course follows the same protocol and workspace on every host. Host-specific files
only make the router discoverable; they do not fork the curriculum.

| Host | Discovery file | Start instruction |
|---|---|---|
| Claude Code | `SKILL.md` and `CLAUDE.md` | `start the backend tutor` |
| Codex | `AGENTS.md` or `~/.codex/skills/backend-tutor` | `start the backend tutor` |
| GitHub Copilot | `.github/copilot-instructions.md` | `Use the backend-tutor skill in this repo and start the course.` |

Create or resume `~/backend-dev/` on every host. If that path is unavailable, use
`./backend-dev/` and tell the learner. Read `SKILL.md` first and lazy-load the reference file
for the active lane, orientation, or mode.
