#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Yaroslav Halchenko <yaroslav.o.halchenko@dartmouth.edu>
# SPDX-License-Identifier: MIT
#
# Generated with Claude Code 2.1.259 / Claude Sonnet 4.6
"""Run read-only Claude security reviews of skill directories.

Requires Claude Code 2.1.248+ with --restricted and --bare support.
SECURITY_CMD selects a trusted Claude-compatible launcher (default: claude).
FAIL_ON selects failing verdicts (default: CRITICAL,HIGH).
Exit status: 0 below threshold, 1 findings, 2 invocation/input/report error.
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

_DEFAULT_CMD = "claude"
_FAIL_ON_DEFAULT = {"CRITICAL", "HIGH"}

SEVERITY_ORDER = ["SAFE", "LOW", "MEDIUM", "HIGH", "CRITICAL"]


def _review_prompt() -> str:
    text = (REPO_ROOT / "skill-security-review" / "SKILL.md").read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) != 3 or parts[0].strip():
        raise ValueError("canonical review skill has invalid frontmatter")
    return parts[2].strip()


def _fail_on_set() -> set[str]:
    raw = os.environ.get("FAIL_ON", ",".join(_FAIL_ON_DEFAULT))
    levels = {s.strip().upper() for s in raw.split(",") if s.strip()}
    if not levels or not levels <= set(SEVERITY_ORDER):
        raise ValueError("FAIL_ON must contain known, nonempty verdict levels")
    return levels


def _security_cmd() -> list[str]:
    raw = os.environ.get("SECURITY_CMD", _DEFAULT_CMD)
    command = shlex.split(raw)
    if not command:
        raise ValueError("SECURITY_CMD must not be empty")
    return command


# ---------------------------------------------------------------------------
# Skill discovery
# ---------------------------------------------------------------------------

def find_skill_dirs(repo_root: Path) -> list[Path]:
    from skill_common import find_skill_dirs as all_skill_dirs
    return [p for p in all_skill_dirs(repo_root) if p.name != "skill-security-review"]


# ---------------------------------------------------------------------------
# Invocation
# ---------------------------------------------------------------------------

def review_skill(skill_dir: Path, cmd_base: list[str]) -> tuple[str, str]:
    """Run the read-only security review against ``skill_dir``.

    Returns (verdict, full_output).
    """
    try:
        prompt = _review_prompt()
        full_cmd = cmd_base + [
            "--bare", "--restricted", "--tools", "Read,Glob,Grep",
            "--allowedTools", "Read,Glob,Grep", "--disallowedTools", "mcp__*",
            "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
            "--setting-sources", "", "--no-session-persistence",
            "--settings", '{"disableAllHooks":true}',
            "-p", prompt,
        ]
        # Do not inherit unrelated secrets or runtime/plugin injection variables.
        env = {key: os.environ[key] for key in
               ("PATH", "HOME", "LANG", "LC_ALL", "ANTHROPIC_API_KEY")
               if key in os.environ}
        result = subprocess.run(
            full_cmd, capture_output=True, text=True, stdin=subprocess.DEVNULL,
            cwd=skill_dir, env=env, timeout=300,
        )
        output = result.stdout
        if result.returncode:
            return "ERROR", f"review process exited {result.returncode}"
    except (OSError, ValueError, UnicodeError) as exc:
        return "ERROR", str(exc)
    except subprocess.TimeoutExpired:
        return "ERROR", f"timed out after 300s reviewing {skill_dir.name}"

    # stderr is diagnostic data, never a verdict.
    return _parse_report(skill_dir.name, output), output


def _parse_report(skill_name: str, output: str) -> str:
    """Reject incomplete reports and verdicts below their own findings."""
    lines = output.strip().splitlines()
    if (len(lines) < 4 or lines[0] != f"SKILL: {skill_name}"
            or not lines[1].startswith("VERDICT: ")
            or not lines[2].startswith("FINDINGS:")
            or not lines[-1].startswith("SUMMARY: ")
            or not lines[-1][9:].strip()
            or sum(line.startswith("VERDICT:") for line in lines) != 1):
        return "ERROR"
    verdict = lines[1].removeprefix("VERDICT: ")
    if verdict not in SEVERITY_ORDER:
        return "ERROR"
    findings = "\n".join([lines[2][9:]] + lines[3:-1]).strip()
    if verdict == "SAFE":
        return verdict if findings == "none" else "ERROR"
    levels = []
    for line in findings.splitlines():
        if not line.strip():
            continue
        match = re.fullmatch(r"- \[(LOW|MEDIUM|HIGH|CRITICAL)\] .+", line)
        if match:
            levels.append(match[1])
        elif not (line.startswith("  ") and levels):
            return "ERROR"
    if not levels or max(map(_severity_rank, levels)) != _severity_rank(verdict):
        return "ERROR"
    return verdict


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
        return 2

    try:
        cmd_base = _security_cmd()
        fail_on = _fail_on_set()
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

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
    errors = [name for name, v, _ in results if v in ("ERROR", "UNKNOWN")]
    if errors:
        print(f"ERRORS (check SECURITY_CMD): {', '.join(errors)}")
        return 2
    if failures:
        print(f"FAILED: {', '.join(n for n, _ in failures)}")
        return 1

    print("All skills passed security review.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
