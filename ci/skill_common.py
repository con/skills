"""Shared immediate-child skill discovery."""
from pathlib import Path


def find_skill_dirs(repo_root: Path) -> list[Path]:
    return sorted(p.parent for p in repo_root.glob("*/SKILL.md")
                  if p.parent.name != "ci")
