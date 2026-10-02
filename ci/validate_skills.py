#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Yaroslav Halchenko <yaroslav.o.halchenko@dartmouth.edu>
# SPDX-License-Identifier: MIT
#
# Generated with Claude Code 2.1.259 / Claude Sonnet 4.6
"""Structural validator for SKILL.md files in con/skills.

Checks performed
----------------
Every SKILL.md:
  E001  Frontmatter present and valid YAML (between opening/closing ``---`` lines)
  E002  Required field ``description`` present and non-empty
  W001  Recommended field ``name`` missing
  W002  Recommended field ``allowed-tools`` missing
  W003  File exceeds 600 lines (readability concern)
  E003  Hardcoded absolute path referencing a real user home dir
        (pattern ``/home/<word>/`` or ``/Users/<Word>/``; tilde paths are fine)
  E004  Hardcoded secret-like assignment outside a code-block fence
        (pattern ``KEY = "..."``, ``token = '...'``, etc.)

Every *.py bundled alongside a SKILL.md:
  E005  Python syntax error (py_compile)
  E006  subprocess call with shell=True and a non-literal first argument
        (potential shell injection)

Exit codes: 0 = all clear, 1 = one or more errors, 2 = usage/internal error.
Warnings never affect the exit code.

Usage:
    python3 ci/validate_skills.py [<skill-dir> ...]

    If no directories are given, scans every immediate subdirectory of the
    repo root that contains a SKILL.md.
"""

from __future__ import annotations

import ast
import py_compile
import re
import sys
import tempfile
from pathlib import Path

from skill_common import find_skill_dirs

try:
    import yaml
except ImportError:
    sys.stderr.write("error: PyYAML required — pip install pyyaml\n")
    sys.exit(2)

# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# Real user home dirs — /home/<word>/ or /Users/<Word>/
# Exclude /home/ alone and paths ending there (e.g. "stored in /home/")
_ABS_HOME = re.compile(r'/(?:home/[a-z][a-zA-Z0-9_.-]+|Users/[A-Z][a-zA-Z0-9_.-]+)/')

# Looks like a secret assignment: KEY = "value", token = 'value', etc.
# Only catches it outside a code fence block (tracked by the caller).
_SECRET_ASSIGN = re.compile(
    r'(?i)\b(?:api_key|secret|token|password|passwd|credential|auth_key)\s*=\s*["\'][^"\']{6,}["\']'
)

# subprocess(..., shell=True) where the first arg is not a plain string literal
_SHELL_TRUE = re.compile(r'shell\s*=\s*True')


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_frontmatter(text: str) -> tuple[dict | None, str]:
    """Return (parsed_yaml_dict, body_after_frontmatter) or (None, full_text)."""
    if not text.startswith("---"):
        return None, text
    rest = text[3:]
    end = rest.find("\n---")
    if end == -1:
        return None, text
    fm_text = rest[:end]
    body = rest[end + 4:]  # skip the closing \n---
    try:
        parsed = yaml.safe_load(fm_text) or {}
    except yaml.YAMLError:
        parsed = None
    return parsed, body


def _in_code_fence(lines: list[str], lineno: int) -> bool:
    """Return True if line ``lineno`` (0-based) is inside a fenced code block."""
    depth = 0
    for i, line in enumerate(lines):
        if i == lineno:
            break
        if re.match(r"^```", line):
            depth = 1 - depth
    return bool(depth)


# ---------------------------------------------------------------------------
# Per-file checks
# ---------------------------------------------------------------------------

class Result:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, code: str, path: Path, msg: str, line: int | None = None) -> None:
        loc = f"{path}:{line}" if line else str(path)
        self.errors.append(f"  ERROR {code}  {loc}  {msg}")

    def warn(self, code: str, path: Path, msg: str, line: int | None = None) -> None:
        loc = f"{path}:{line}" if line else str(path)
        self.warnings.append(f"  WARN  {code}  {loc}  {msg}")


def check_skill_md(skill_md: Path, result: Result) -> None:
    text = skill_md.read_text(encoding="utf-8")
    lines = text.splitlines()

    # E001 — frontmatter
    fm, body = _parse_frontmatter(text)
    if not isinstance(fm, dict):
        result.error("E001", skill_md, "missing or unparseable YAML frontmatter")
        return  # remaining checks need the frontmatter

    # E002 — description
    desc = fm.get("description", "")
    if not desc or not str(desc).strip():
        result.error("E002", skill_md, "frontmatter missing required field 'description'")

    # W001 — name
    if not fm.get("name"):
        result.warn("W001", skill_md, "frontmatter missing recommended field 'name'")

    # W002 — allowed-tools
    if not fm.get("allowed-tools"):
        result.warn("W002", skill_md, "frontmatter missing recommended field 'allowed-tools'")

    # W003 — length
    if len(lines) > 600:
        result.warn("W003", skill_md, f"file is {len(lines)} lines (>600); consider splitting")

    # E003 — hardcoded absolute home paths
    for i, line in enumerate(lines, 1):
        if _ABS_HOME.search(line):
            result.error("E003", skill_md, f"hardcoded absolute home path: {line.strip()!r}", i)

    # E004 — secret-like assignments outside code fences
    for i, line in enumerate(lines):
        if not _in_code_fence(lines, i) and _SECRET_ASSIGN.search(line):
            result.error("E004", skill_md, f"possible hardcoded secret: {line.strip()!r}", i + 1)


def check_python_file(py_path: Path, result: Result) -> None:
    # E005 — syntax
    try:
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as tmp:
            tmp.write(py_path.read_bytes())
            tmp_name = tmp.name
        py_compile.compile(tmp_name, doraise=True)
    except py_compile.PyCompileError as exc:
        result.error("E005", py_path, f"Python syntax error: {exc}")
        return  # no point parsing AST

    # E006 — subprocess shell=True with non-literal first arg
    try:
        tree = ast.parse(py_path.read_text(encoding="utf-8"))
    except SyntaxError:
        return  # already caught above

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        # Match subprocess.run / subprocess.Popen / subprocess.call etc.
        is_subprocess = (
            isinstance(func, ast.Attribute)
            and isinstance(func.value, ast.Name)
            and func.value.id == "subprocess"
        ) or (
            isinstance(func, ast.Name)
            and func.id in {"Popen", "run", "call", "check_call", "check_output"}
        )
        if not is_subprocess:
            continue
        has_shell_true = any(
            isinstance(kw.value, ast.Constant) and kw.value.value is True
            for kw in node.keywords
            if kw.arg == "shell"
        )
        if not has_shell_true:
            continue
        # First positional arg must be a plain string literal to be safe
        if node.args:
            first = node.args[0]
            if not isinstance(first, ast.Constant):
                result.error(
                    "E006", py_path,
                    "subprocess call with shell=True and non-literal command "
                    f"(potential injection) at line {node.lineno}",
                    node.lineno,
                )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------



def validate_skill(skill_dir: Path) -> Result:
    result = Result()
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        result.error("E001", skill_dir, "no SKILL.md found")
        return result

    check_skill_md(skill_md, result)

    for py_path in sorted(skill_dir.rglob("*.py")):
        check_python_file(py_path, result)

    return result


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv

    repo_root = Path(__file__).parent.parent
    if args:
        skill_dirs = [Path(a).resolve() for a in args]
    else:
        skill_dirs = find_skill_dirs(repo_root)

    if not skill_dirs:
        sys.stderr.write("warning: no skill directories found\n")
        return 0

    total_errors = 0
    total_warnings = 0
    failed_skills: list[str] = []

    for skill_dir in skill_dirs:
        result = validate_skill(skill_dir)
        skill_name = skill_dir.name
        if result.errors or result.warnings:
            print(f"\n{'❌' if result.errors else '⚠️ '} {skill_name}")
            for msg in result.errors:
                print(msg)
            for msg in result.warnings:
                print(msg)
        else:
            print(f"✅ {skill_name}")
        total_errors += len(result.errors)
        total_warnings += len(result.warnings)
        if result.errors:
            failed_skills.append(skill_name)

    print(f"\n{'─' * 60}")
    print(f"Skills checked: {len(skill_dirs)}  "
          f"Errors: {total_errors}  Warnings: {total_warnings}")
    if failed_skills:
        print(f"Failed: {', '.join(failed_skills)}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
