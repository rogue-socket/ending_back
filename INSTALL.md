# Install

This is the **`main`** branch — covers every supported (OS × harness) combo. If you want a leaner, single-path README, switch to one of the platform branches:

| Branch | OS | Harness |
|---|---|---|
| [`main`](https://github.com/rogue-socket/backend-tutor/tree/main) | macOS / Linux / Windows | any |
| [`cc-windows`](https://github.com/rogue-socket/backend-tutor/tree/cc-windows) | Windows | Claude Code |
| [`codex-macos`](https://github.com/rogue-socket/backend-tutor/tree/codex-macos) | macOS / Linux | Codex CLI |
| [`codex-windows`](https://github.com/rogue-socket/backend-tutor/tree/codex-windows) | Windows | Codex CLI |

Platform branches strip the conditionals and ship just the path that applies to that combo. They're rebased onto `main` periodically (`tools/sync-platform-branches.sh`).

---

## macOS / Linux

### Claude Code

```bash
git clone https://github.com/rogue-socket/backend-tutor ~/Documents/backend-tutor
ln -s ~/Documents/backend-tutor ~/.claude/skills/backend-tutor
```

Then in any Claude Code session: `> start the backend tutor`.

### Codex CLI

```bash
git clone https://github.com/rogue-socket/backend-tutor ~/Documents/backend-tutor
cd ~/Documents/backend-tutor
codex "start the backend tutor"
```

Codex reads `AGENTS.md` from cwd; no symlink needed.

### GitHub Copilot CLI / Cursor / Aider / others

GitHub Copilot uses this repository's `.github/copilot-instructions.md` adapter. Open Copilot Chat from the cloned repository and ask:

```text
Use the backend-tutor skill in this repo and start the course.
```

Cursor, Aider, and other AGENTS.md-aware harnesses follow the Codex shape: `cd` into the cloned repo (or copy `AGENTS.md` into your project) before invoking the agent.

---

## Windows

### Claude Code (PowerShell, no admin / Developer Mode required)

Use a directory junction — junctions work for any user without elevated permissions, unlike symlinks:

```powershell
git clone https://github.com/rogue-socket/backend-tutor "$env:USERPROFILE\Documents\backend-tutor"

$src = "$env:USERPROFILE\Documents\backend-tutor"
$dst = "$env:USERPROFILE\.claude\skills\backend-tutor"
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.claude\skills" | Out-Null
cmd /c mklink /J "$dst" "$src"
```

Verify:

```powershell
Get-Item $dst | Select-Object Name, Target
```

Then in any Claude Code session: `> start the backend tutor`.

### Codex CLI (PowerShell)

```powershell
git clone https://github.com/rogue-socket/backend-tutor "$env:USERPROFILE\Documents\backend-tutor"
cd "$env:USERPROFILE\Documents\backend-tutor"
codex "start the backend tutor"
```

Codex reads `AGENTS.md` from cwd; no junction needed.

### GitHub Copilot CLI / other harnesses on Windows

For GitHub Copilot, open Copilot Chat from the cloned repository and use the same prompt as macOS/Linux. Other AGENTS.md-aware harnesses follow the Codex shape — `cd` into the cloned repo before invoking the agent.

---

## Resume — any platform, any harness

```
> /continue
```

Reads `~/backend-dev/session-state.md` (or `%USERPROFILE%\backend-dev\session-state.md` on Windows) and picks up where you left off, even if the previous session ran in a different harness.
