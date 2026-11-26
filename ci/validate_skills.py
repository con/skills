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
  E007  Frontmatter ``name`` must equal the containing directory name
  E008  Root-level skills must move into the published ``skills/`` collection
  W002  Recommended field ``allowed-tools`` missing
  W003  File exceeds 600 lines (readability concern)
  E003  Hardcoded absolute path referencing a real user home dir
        (pattern ``/home/<word>/`` or ``/Users/<Word>/``; tilde paths are fine)
  E004  Hardcoded secret-like assignment outside a code-block fence
        (pattern ``KEY = "..."``, ``token = '...'``, etc.)
  E009  ``SKILL_DIR/<path>`` must name a file bundled with the skill, and a
        skill using it must define ``SKILL_DIR`` with the shared sentence

Every skill's ``apm.yml`` (its APM package manifest, beside SKILL.md):
  E010  Present, a YAML mapping whose ``name`` equals the directory name,
        ``version`` is a ``MAJOR.MINOR.PATCH`` string, ``description`` is
        one line of at most 100 characters that differs from the SKILL.md
        ``description``, ``author`` is a non-empty string, ``license`` is
        a non-empty string (``ci/check_reuse.py`` checks that it is an SPDX
        expression matching REUSE), ``type`` is ``skill``, and any
        ``dependencies`` are ``apm: [{path: ../<sibling skill>}]`` entries
        naming other skills here
  E011  SKILL.md frontmatter has no ``version:``, ``author:`` or
        ``license:`` (nor under ``metadata:``); they live only in ``apm.yml``,
        the manifest APM reads and records in consumers' locks

Every *.py bundled alongside a SKILL.md:
  E005  Python syntax error (py_compile)
  E006  subprocess call with shell=True and a non-literal first argument
        (potential shell injection)

The Claude Code plugin marketplace (``.claude-plugin/marketplace.json``),
checked when no skill directories are given:
  E012  The file exists; plugin names are unique strings starting with
        ``con-``; each plugin lists skills as ``./skills/<name>`` of
        published skills; every published skill is in exactly one plugin;
        ``dependencies`` name other plugins of this marketplace, among them
        every plugin holding a skill that one of its skills' ``apm.yml``
        depends on

Exit codes: 0 = all clear, 1 = one or more errors, 2 = usage/internal error.
Warnings never affect the exit code.

Usage:
    python3 ci/validate_skills.py [<skill-dir> ...]

    If no directories are given, scans every immediate subdirectory of the
    `skills/` directory that contains a SKILL.md.
"""

from __future__ import annotations

import ast
import json
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

# Bundled-file references, resolved against the loaded skill's own directory
_SKILL_DIR_REF = re.compile(r'\bSKILL_DIR/([\w./-]*\w)')
SKILL_DIR_DEFINITION = '`SKILL_DIR` is the absolute path of the directory holding this SKILL.md'

# A skill's package version: MAJOR.MINOR.PATCH
_SEMVER = re.compile(r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)')

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

    # E007 — published skill identity must match its directory
    if fm.get("name") != skill_md.parent.name:
        result.error("E007", skill_md, "frontmatter name must equal directory name")

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

    # E009 — SKILL_DIR references
    refs = [(i, m.group(1)) for i, line in enumerate(lines, 1)
            for m in _SKILL_DIR_REF.finditer(line)]
    if refs and SKILL_DIR_DEFINITION not in text:
        result.error("E009", skill_md, "uses SKILL_DIR without the shared definition sentence")
    root = skill_md.parent.resolve()
    for i, ref in refs:
        target = (root / ref).resolve()
        if not (target.is_file() and target.is_relative_to(root)):
            result.error("E009", skill_md, f"SKILL_DIR/{ref} is not a file bundled with this skill", i)


def check_apm_manifest(skill_dir: Path, result: Result) -> None:
    """E010/E011: the skill's own APM manifest is the only place its version lives."""
    manifest = skill_dir / "apm.yml"
    if not manifest.is_file():
        result.error("E010", manifest, "missing; every skill is its own APM package (see AGENTS.md)")
        return
    try:
        data = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        result.error("E010", manifest, f"invalid YAML: {exc}")
        return
    if not isinstance(data, dict):
        result.error("E010", manifest, "must be a YAML mapping")
        return
    if data.get("name") != skill_dir.name:
        result.error("E010", manifest, "name must equal the skill directory name")
    version = data.get("version")
    if not (isinstance(version, str) and _SEMVER.fullmatch(version)):
        result.error("E010", manifest, f"version must be a MAJOR.MINOR.PATCH string, got {version!r}")

    fm, _ = _parse_frontmatter((skill_dir / "SKILL.md").read_text(encoding="utf-8"))
    fm = fm if isinstance(fm, dict) else {}

    # apm.yml description is the human one-liner (apm view, apm deps info);
    # the SKILL.md one tells the agent when to trigger. APM never merges them.
    description = data.get("description")
    if not (isinstance(description, str) and description.strip()):
        result.error("E010", manifest, "description must be a non-empty one-line summary for people")
    elif "\n" in description.strip() or len(description) > 100:
        result.error("E010", manifest, "description must be one line of at most 100 characters")
    elif description.strip() == str(fm.get("description", "")).strip():
        result.error("E010", manifest, "description repeats the SKILL.md description; "
                     "give people a short summary and leave triggering to SKILL.md")
    author = data.get("author")
    if not (isinstance(author, str) and author.strip()):
        result.error("E010", manifest, "author must name the skill's significant contributors")
    license_ = data.get("license")
    if not (isinstance(license_, str) and license_.strip()):
        result.error("E010", manifest, f"license must be a non-empty string, got {license_!r}")
    if data.get("type") != "skill":
        result.error("E010", manifest, f"type must be skill, got {data.get('type')!r}")
    check_manifest_dependencies(skill_dir, data.get("dependencies"), manifest, result)

    meta = fm.get("metadata") if isinstance(fm.get("metadata"), dict) else {}
    for key in ("version", "author", "license"):
        if key in fm or key in meta:
            result.error("E011", skill_dir / "SKILL.md",
                         f"frontmatter must not carry {key}:; it lives only in apm.yml")


def check_manifest_dependencies(skill_dir: Path, deps: object, manifest: Path, result: Result) -> None:
    """E010: dependencies may only name sibling skills, as same-repo relative paths.

    APM resolves ``path: ../<sibling>`` in a Git-installed skill to the same
    repository and commit, so the dependency is installed with the skill.
    """
    if deps is None:
        return
    if not (isinstance(deps, dict) and set(deps) == {"apm"} and isinstance(deps["apm"], list)):
        result.error("E010", manifest, "dependencies must be a mapping with only an apm: list")
        return
    seen: set[str] = set()
    for entry in deps["apm"]:
        path = entry.get("path") if isinstance(entry, dict) and set(entry) == {"path"} else None
        if isinstance(path, str) and path in seen:
            result.error("E010", manifest, f"dependency {path!r} is listed twice")
        seen.add(str(path))
        sibling = skill_dir.parent / str(path)[3:] if isinstance(path, str) and path.startswith("../") else None
        if (sibling is None or "/" in str(path)[3:] or sibling == skill_dir
                or not (sibling / "SKILL.md").is_file()):
            result.error("E010", manifest, f"dependency {entry!r} must be {{path: ../<another skill>}}")


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
    check_apm_manifest(skill_dir, result)

    for py_path in sorted(skill_dir.rglob("*.py")):
        check_python_file(py_path, result)

    return result


def check_collection_layout(repo_root: Path) -> Result:
    """Catch skills added using the layout from before the APM migration."""
    result = Result()
    for skill_md in sorted(repo_root.glob("*/SKILL.md")):
        result.error("E008", skill_md, "move this skill into skills/ so packaging and scans include it")
    return result


MARKETPLACE = Path(".claude-plugin") / "marketplace.json"


def sibling_dependencies(skill_dir: Path) -> set[str]:
    """The sibling skills a skill's apm.yml depends on (E010 reports a malformed one)."""
    try:
        data = yaml.safe_load((skill_dir / "apm.yml").read_text(encoding="utf-8"))
        entries = data["dependencies"]["apm"]
        return {entry["path"][3:] for entry in entries
                if isinstance(entry, dict) and isinstance(entry.get("path"), str)
                and entry["path"].startswith("../") and "/" not in entry["path"][3:]}
    except (OSError, yaml.YAMLError, KeyError, TypeError):
        return set()


def check_marketplace(repo_root: Path) -> Result:
    """Every published skill belongs to exactly one Claude Code plugin."""
    result = Result()
    path = repo_root / MARKETPLACE
    try:
        plugins = json.loads(path.read_text(encoding="utf-8"))["plugins"]
        names = [plugin["name"] for plugin in plugins]
    except (OSError, ValueError, KeyError, TypeError, RecursionError) as exc:
        result.error("E012", path, f"cannot read the plugin names: {exc!r}")
        return result
    if not all(isinstance(name, str) for name in names):
        result.error("E012", path, "give every plugin a string name")
        return result

    owners: dict[str, list[str]] = {d.name: [] for d in find_skill_dirs(repo_root)}
    for name in sorted({n for n in names if names.count(n) > 1}):
        result.error("E012", path, f"plugin name {name!r} is used more than once")
    for plugin in plugins:
        name = plugin["name"]
        if not name.startswith("con-"):
            result.error("E012", path, f"plugin name {name!r} must start with 'con-'")
        if not all(isinstance(plugin.get(key, []), list) for key in ("skills", "dependencies")):
            result.error("E012", path, f"plugin {name!r}: give 'skills' and 'dependencies' as lists")
            continue
        for dependency in plugin.get("dependencies", []):
            if isinstance(dependency, str) and "@" not in dependency and (
                    dependency == name or dependency not in names):
                result.error("E012", path, f"plugin {name!r} depends on {dependency!r}, "
                             "which is not another plugin of this marketplace")
        for entry in plugin.get("skills", []):
            skill = entry.removeprefix("./skills/") if isinstance(entry, str) else ""
            if skill == entry or skill not in owners:
                result.error("E012", path, f"plugin {name!r} lists {entry!r}; "
                             "list published skills as ./skills/<name>")
                continue
            owners[skill].append(name)
    for skill, plugin_names in owners.items():
        if len(plugin_names) != 1:
            where = ", ".join(repr(n) for n in plugin_names) or "none"
            result.error("E012", path, f"skill {skill!r} is in {len(plugin_names)} plugins "
                         f"({where}); put it in exactly one")
    # A plugin install brings only its own skills and its dependencies' plugins,
    # so a skill's apm.yml dependency in another plugin needs that plugin listed.
    listed = {plugin["name"]: {d for d in plugin.get("dependencies", []) if isinstance(d, str)}
              for plugin in plugins if isinstance(plugin.get("dependencies", []), list)}
    for skill, plugin_names in owners.items():
        if len(plugin_names) != 1:
            continue
        home = plugin_names[0]
        for needed in sorted(sibling_dependencies(repo_root / "skills" / skill)):
            needed_home = owners.get(needed, [])
            if len(needed_home) == 1 and needed_home[0] not in {home} | listed.get(home, set()):
                result.error("E012", path, f"plugin {home!r} lists {skill!r}, which depends on "
                             f"{needed!r} in {needed_home[0]!r}: add {needed_home[0]!r} to "
                             f"{home!r}'s dependencies")
    return result


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv

    repo_root = Path(__file__).parent.parent
    if args:
        skill_dirs = [Path(a).resolve() for a in args]
    else:
        layout = check_collection_layout(repo_root)
        if layout.errors:
            print("\n".join(layout.errors))
            return 1
        skill_dirs = find_skill_dirs(repo_root)
        marketplace = check_marketplace(repo_root)
        if marketplace.errors:
            print("\n".join(marketplace.errors))
            return 1

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
