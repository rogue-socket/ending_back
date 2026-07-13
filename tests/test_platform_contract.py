"""Verify the portable-provider and two-path contracts stay explicit."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text()


def main() -> int:
    for path in ("CLAUDE.md", "AGENTS.md", ".github/copilot-instructions.md"):
        assert (ROOT / path).is_file(), f"missing provider adapter: {path}"

    install = read("INSTALL.md").lower()
    for provider in ("claude code", "codex cli", "copilot"):
        assert provider in install, f"INSTALL.md does not document {provider}"

    skill = read("SKILL.md").lower()
    for path in ("foundations_first", "builder_first"):
        assert path in skill, f"SKILL.md does not define {path}"

    for path in (
        "references/curriculum.md",
        "references/builder-first.md",
        "references/exercise-bank.md",
        "references/incidents.md",
        "references/session-control.md",
        "references/spaced-repetition.md",
        "references/theory-modes.md",
        "references/anti-patterns-with-examples.md",
        "references/host-adapters.md",
        "SKILL_ANATOMY.md",
    ):
        assert (ROOT / path).is_file(), f"missing shared skill component: {path}"

    assert "finish direct questions before advancing" in skill
    builder = read("references/builder-first.md")
    assert "Testing starts here, not later" in builder

    print("PASS: provider adapters and both learning paths are present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
