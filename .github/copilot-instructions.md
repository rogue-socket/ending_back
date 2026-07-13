# GitHub Copilot Instructions

This repository packages the `backend-tutor` skill.

When the user asks to start, continue, review, quiz, or practice backend engineering, load `SKILL.md` and follow its session controller. Load `references/` lazily by mode. Create or resume the course workspace at `~/backend-dev/` unless the environment cannot write there; in that case use `./backend-dev/` and tell the user.

When the user asks to maintain this repository, do not run the course. Follow `AGENTS.md` for repository guidance.
