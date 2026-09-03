#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Yaroslav Halchenko <yaroslav.o.halchenko@dartmouth.edu>
# SPDX-License-Identifier: MIT
#
# Generated with Claude Code 2.1.259 / Claude Sonnet 4.6
"""Run the skill-security-review skill against every skill in this repo.

Invokes ``claude --dangerously-skip-permissions --plugin-dir <repo-root>
-p "/skill-security-review"`` (or the command in SECURITY_CMD env var) once
per skill directory and collects the structured VERDICT reports.

Configuration
-------------
SECURITY_CMD   Override the base command. Default:
               ``claude --dangerously-skip-permissions``
               Set to ``yolo --worktree=skip --`` to run via the Podman
               wrapper locally, or to any other claude-compatible launcher.
FAIL_ON        Comma-separated list of verdict levels that cause a non-zero
               exit. Default: ``CRITICAL,HIGH``.

Usage
-----
    python3 ci/security_review.py [<skill-dir> ...]

If no directories are given, every immediate subdirectory of the repo root
that contains a SKILL.md is reviewed (same discovery logic as validate_skills.py,
excluding the skill-security-review skill itself to avoid recursion).

Exit codes: 0 = all at or below threshold, 1 = one or more findings at or
above FAIL_ON threshold, 2 = usage / invocation error.
"""

from __future__ import annotations

import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).parent.parent

_DEFAULT_CMD = "claude --dangerously-skip-permissions"
_FAIL_ON_DEFAULT = {"CRITICAL", "HIGH"}

SEVERITY_ORDER = ["SAFE", "LOW", "MEDIUM", "HIGH", "CRITICAL"]


def _fail_on_set() -> set[str]:
    raw = os.environ.get("FAIL_ON", ",".join(_FAIL_ON_DEFAULT))
    return {s.strip().upper() for s in raw.split(",") if s.strip()}


def _security_cmd() -> list[str]:
    raw = os.environ.get("SECURITY_CMD", _DEFAULT_CMD)
    return shlex.split(raw)


# ---------------------------------------------------------------------------
# Skill discovery
# ---------------------------------------------------------------------------

def find_skill_dirs(repo_root: Path) -> list[Path]:
    return sorted(
        p.parent
        for p in repo_root.glob("*/SKILL.md")
        if p.parent.name not in {"ci", "skill-security-review"}
    )


# ---------------------------------------------------------------------------
# Invocation
# ---------------------------------------------------------------------------

def review_skill(skill_dir: Path, cmd_base: list[str]) -> tuple[str, str]:
    """Run the security review skill against ``skill_dir``.

    Returns (verdict, full_output).
    """
    full_cmd = cmd_base + [
        "--plugin-dir", str(REPO_ROOT),
        "-p", "/skill-security-review",
    ]
    env = os.environ.copy()
    env["SKILL_DIR"] = str(skill_dir)

    try:
        result = subprocess.run(
            full_cmd,
            capture_output=True,
            text=True,
            env=env,
            cwd=skill_dir,
            timeout=300,
        )
        output = result.stdout + result.stderr
    except FileNotFoundError:
        cmd_name = cmd_base[0]
        return "ERROR", f"command not found: {cmd_name!r}\nSet SECURITY_CMD to the correct claude launcher."
    except subprocess.TimeoutExpired:
        return "ERROR", f"timed out after 300s reviewing {skill_dir.name}"

    # Extract VERDICT line from structured output
    match = re.search(r"^VERDICT:\s*(\w+)", output, re.MULTILINE)
    verdict = match.group(1).upper() if match else "UNKNOWN"
    return verdict, output


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _severity_rank(v: str) -> int:
    try:
        return SEVERITY_ORDER.index(v)
    except ValueError:
        return -1  # ERROR / UNKNOWN sort lowest for ranking purposes


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv

    if args:
        skill_dirs = [Path(a).resolve() for a in args]
    else:
        skill_dirs = find_skill_dirs(REPO_ROOT)

    if not skill_dirs:
        sys.stderr.write("warning: no skill directories found\n")
        return 0

    cmd_base = _security_cmd()
    fail_on = _fail_on_set()

    print(f"Security review — command: {' '.join(cmd_base)}")
    print(f"Fail on: {', '.join(sorted(fail_on, key=_severity_rank, reverse=True))}")
    print(f"Reviewing {len(skill_dirs)} skill(s)…\n")

    results: list[tuple[str, str, str]] = []  # (skill_name, verdict, output)
    for skill_dir in skill_dirs:
        print(f"  → {skill_dir.name} … ", end="", flush=True)
        verdict, output = review_skill(skill_dir, cmd_base)
        icon = {"SAFE": "✅", "LOW": "🔵", "MEDIUM": "🟡",
                "HIGH": "🟠", "CRITICAL": "🔴"}.get(verdict, "❓")
        print(f"{icon} {verdict}")
        results.append((skill_dir.name, verdict, output))

    # Full output for non-safe results
    print()
    for skill_name, verdict, output in results:
        if verdict not in ("SAFE",):
            print(f"{'─' * 60}")
            print(f"  {skill_name}  ({verdict})")
            print(output.strip())
            print()

    print(f"{'─' * 60}")
    failures = [
        (name, v) for name, v, _ in results
        if v in fail_on
    ]
    if failures:
        print(f"FAILED: {', '.join(n for n, _ in failures)}")
        return 1

    errors = [name for name, v, _ in results if v in ("ERROR", "UNKNOWN")]
    if errors:
        print(f"ERRORS (check SECURITY_CMD): {', '.join(errors)}")
        return 2

    print("All skills passed security review.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
