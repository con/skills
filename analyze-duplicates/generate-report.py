#!/usr/bin/env python3
"""Generate a Markdown duplication report from jscpd JSON output.

Reads one or more jscpd-report.json files and produces a GitHub/Gitea-friendly
Markdown report with <details> sections for each duplicate cluster.

Usage:
    python3 generate-report.py [OPTIONS] REPORT_JSON [REPORT_JSON ...]

Options:
    --threshold N        Duplication warning threshold percentage (default: 5)
    --output PATH        Output markdown file (default: stdout)
    --cross-project PATH Include cross-project scan results from this JSON file
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def detect_git_info(scan_path):
    """Try to detect the remote browse URL and branch for a git repo."""
    try:
        branch = subprocess.run(
            ["git", "-C", scan_path, "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=5,
        ).stdout.strip()
        # Find the remote that the branch tracks, fall back to origin
        tracking_remote = subprocess.run(
            ["git", "-C", scan_path, "config",
             f"branch.{branch}.remote"],
            capture_output=True, text=True, timeout=5,
        ).stdout.strip() or "origin"
        remote_url = subprocess.run(
            ["git", "-C", scan_path, "remote", "get-url", tracking_remote],
            capture_output=True, text=True, timeout=5,
        ).stdout.strip()
        if not remote_url or not branch:
            return None, None
        # Convert git@ or https:// URL to browse URL
        browse_url = remote_url
        browse_url = re.sub(r"\.git$", "", browse_url)
        browse_url = re.sub(
            r"^git@([^:]+):", r"https://\1/", browse_url
        )
        return browse_url, branch
    except (subprocess.SubprocessError, OSError):
        return None, None


def file_link(name, start, end, repo_url, branch):
    """Format a file reference, as a hyperlink if repo info is available."""
    label = f"`{name}` (lines {start}-{end})"
    if repo_url and branch:
        # Strip leading ./ or ../ — jscpd paths are relative to scan dir
        clean = re.sub(r"^(\.\./?)+" , "", name)
        url = f"{repo_url}/blob/{branch}/{clean}#L{start}-L{end}"
        return f"[{label}]({url})"
    return label


def load_report(path):
    """Load a jscpd JSON report."""
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Error loading {path}: {exc}", file=sys.stderr)
        sys.exit(1)


def guess_project_name(report_path):
    """Infer project name from the report's parent directory name."""
    parent = Path(report_path).parent.name
    # Strip jscpd- prefix if present
    if parent.startswith("jscpd-"):
        return parent[6:]
    return parent


def format_language(fmt):
    """Map jscpd format names to markdown code fence language hints."""
    mapping = {
        "python": "python",
        "javascript": "javascript",
        "typescript": "typescript",
        "markup": "html",
        "markdown": "markdown",
        "yaml": "yaml",
        "json": "json",
        "css": "css",
        "go": "go",
        "rust": "rust",
        "java": "java",
        "csharp": "csharp",
        "ruby": "ruby",
        "bash": "bash",
        "shell": "bash",
    }
    return mapping.get(fmt, "")


def render_summary_table(projects):
    """Render the summary table with human-aligned columns."""
    headers = ["Project", "Files", "Lines", "Clones", "Duplicated Lines", "Percentage"]
    rows = []
    for p in projects:
        stats = p["stats"]
        rows.append([
            p["name"],
            str(stats.get("sources", 0)),
            str(stats.get("lines", 0)),
            str(stats.get("clones", 0)),
            str(stats.get("duplicatedLines", 0)),
            f"{stats.get('percentage', 0.0):.2f}%",
        ])

    # Compute column widths (max of header and all row values)
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    # First column left-aligned, rest right-aligned
    def fmt_row(cells):
        parts = []
        for i, cell in enumerate(cells):
            if i == 0:
                parts.append(f" {cell:<{widths[i]}} ")
            else:
                parts.append(f" {cell:>{widths[i]}} ")
        return "|" + "|".join(parts) + "|"

    def fmt_sep():
        parts = []
        for i, w in enumerate(widths):
            if i == 0:
                parts.append("-" * (w + 2))
            else:
                parts.append("-" * (w + 1) + ":")
        return "|" + "|".join(parts) + "|"

    lines = [fmt_row(headers), fmt_sep()]
    for row in rows:
        lines.append(fmt_row(row))
    return "\n".join(lines)


def truncate_fragment(fragment, max_lines=30):
    """Truncate long code fragments for readability."""
    lines = fragment.splitlines()
    if len(lines) <= max_lines:
        return fragment
    kept = lines[:max_lines]
    kept.append(f"... ({len(lines) - max_lines} more lines)")
    return "\n".join(kept)


def classify_cluster(dup):
    """Classify a duplicate cluster and propose mediation strategy.

    Returns (difficulty, strategy, rationale) where difficulty is one of:
    trivial, easy, moderate, hard.
    """
    first_name = dup["firstFile"]["name"]
    second_name = dup["secondFile"]["name"]
    n_lines = dup.get("lines", 0)
    fmt = dup.get("format", "")
    same_file = first_name == second_name

    # Detect test files
    is_test = any(
        t in n for n in (first_name, second_name)
        for t in ("test_", "tests/", "_test.", "conftest", "spec.", "spec/")
    )

    # Detect generated / binary-like artifacts (SVG, images, configs)
    is_asset = any(
        n.endswith((".svg", ".png", ".jpg", ".ico", ".woff", ".woff2", ".eot", ".ttf"))
        for n in (first_name, second_name)
    )
    if is_asset:
        if same_file:
            return ("trivial", "Internal duplication in asset file",
                    "Repeated content within an asset file. Usually harmless.")
        return (
            "easy",
            "Deduplicate asset — keep one copy and reference it",
            "Same asset committed in multiple locations. "
            "Keep a single canonical copy and reference/symlink from other locations.",
        )

    # Detect documentation / markdown
    is_docs = fmt in ("markdown", "markup") or any(
        n.endswith((".md", ".rst", ".adoc")) for n in (first_name, second_name)
    )

    # Same directory?
    first_dir = "/".join(first_name.split("/")[:-1])
    second_dir = "/".join(second_name.split("/")[:-1])
    same_dir = first_dir == second_dir

    if is_docs:
        if same_file:
            return (
                "easy",
                "Consolidate repeated sections within this document",
                "Same content appears multiple times in one file. "
                "Merge into a single section and add internal cross-references.",
            )
        return (
            "moderate",
            "Create a canonical section and cross-reference",
            "Duplicated documentation across files. Extract shared content "
            "into a single authoritative location and reference it "
            "(e.g., includes, links, or shortcodes).",
        )

    if is_test:
        if same_file:
            difficulty = "easy" if n_lines <= 10 else "moderate"
            return (
                difficulty,
                "Extract test fixture or parametrize",
                "Duplicated test setup/assertions within one test file. "
                "Use `@pytest.fixture`, `@pytest.mark.parametrize`, "
                "or a helper function to share the common pattern.",
            )
        return (
            "moderate",
            "Extract shared test fixture to conftest.py",
            "Duplicated test code across files. Move common setup into "
            "`conftest.py` as a shared fixture, or into a test utilities module.",
        )

    if same_file:
        difficulty = "trivial" if n_lines <= 8 else "easy"
        return (
            difficulty,
            "Extract local helper function",
            f"Duplicated logic within `{first_name.split('/')[-1]}`. "
            "Extract into a private function in the same module.",
        )

    if same_dir:
        difficulty = "easy" if n_lines <= 10 else "moderate"
        return (
            difficulty,
            "Extract shared function into sibling module",
            f"Duplicated code in same package (`{first_dir or './'}`). "
            "Extract into a shared utility module within the package.",
        )

    # Different directories / packages
    difficulty = "moderate" if n_lines <= 15 else "hard"
    return (
        difficulty,
        "Extract into shared library or utils package",
        "Duplicated code across different packages. Consider a shared "
        "utility module or library that both can import.",
    )


DIFFICULTY_LABELS = {
    "trivial": "Trivial",
    "easy": "Easy",
    "moderate": "Moderate",
    "hard": "Hard",
}


def render_overview_table(all_dups):
    """Render a compact overview table of all clusters with mediation info."""
    headers = ["C", "Lines", "Difficulty", "Strategy", "Files"]
    rows = []
    for i, (_proj, dup) in enumerate(all_dups, 1):
        difficulty, strategy, _rationale = classify_cluster(dup)
        first_name = dup["firstFile"]["name"]
        second_name = dup["secondFile"]["name"]
        first_short = first_name.rsplit("/", 1)[-1]
        second_short = second_name.rsplit("/", 1)[-1]
        if first_name == second_name:
            files_str = first_short
        elif first_short == second_short:
            # Same filename in different dirs — show parent/file
            first_ctx = "/".join(first_name.rsplit("/", 2)[-2:])
            second_ctx = "/".join(second_name.rsplit("/", 2)[-2:])
            files_str = f"{first_ctx} / {second_ctx}"
        else:
            files_str = f"{first_short} / {second_short}"
        label = DIFFICULTY_LABELS.get(difficulty, difficulty)
        rows.append([
            str(i),
            str(dup.get("lines", 0)),
            label,
            strategy,
            files_str,
        ])

    widths = [len(h) for h in headers]
    for row in rows:
        for j, cell in enumerate(row):
            widths[j] = max(widths[j], len(cell))

    def fmt_row(cells):
        parts = []
        for j, cell in enumerate(cells):
            parts.append(f" {cell:<{widths[j]}} ")
        return "|" + "|".join(parts) + "|"

    lines = [
        fmt_row(headers),
        "|" + "|".join("-" * (w + 2) for w in widths) + "|",
    ]
    for row in rows:
        lines.append(fmt_row(row))
    return "\n".join(lines)


def render_cluster(idx, dup, prefix="", repo_url=None, branch=None):
    """Render a single duplicate cluster as a <details> block with mediation."""
    fmt = dup.get("format", "")
    lang = format_language(fmt)
    first = dup["firstFile"]
    second = dup["secondFile"]
    n_lines = dup.get("lines", 0)

    first_name = first["name"]
    second_name = second["name"]

    first_link = file_link(first_name, first["start"], first["end"],
                           repo_url, branch)
    second_link = file_link(second_name, second["start"], second["end"],
                            repo_url, branch)

    difficulty, strategy, rationale = classify_cluster(dup)
    diff_label = DIFFICULTY_LABELS.get(difficulty, difficulty)

    label = f"{prefix}Cluster {idx}"
    # Summary line uses plain text (no links — they don't work inside <summary>)
    summary = (
        f"[{diff_label}] "
        f"`{first_name}` lines {first['start']}-{first['end']} "
        f"&harr; `{second_name}` lines {second['start']}-{second['end']} "
        f"({n_lines} lines)"
    )

    fragment = dup.get("fragment", "")
    fragment = truncate_fragment(fragment)

    block = [
        "<details>",
        f"<summary><b>{label}</b>: {summary}</summary>",
        "",
        "**Files involved:**",
        f"- {first_link}",
        f"- {second_link}",
        "",
    ]

    if fragment.strip():
        fence = "~~~"
        while fence in fragment:
            fence += "~"
        block.extend([
            "**Duplicated fragment:**",
            f"{fence}{lang}",
            fragment,
            fence,
            "",
        ])

    # Inline mediation recommendation
    block.extend([
        f"**Mediation** ({diff_label}): {strategy}",
        "",
        f"> {rationale}",
        "",
    ])

    block.extend(["</details>", ""])
    return "\n".join(block)


def render_report(projects, threshold, cross_project=None, jscpd_version=None,
                   badge_path=None, repo_url=None, branch=None):
    """Render the full Markdown report."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    version_str = jscpd_version or "unknown"

    parts = [
        "# Duplication Analysis Report",
        "",
        f"> Generated: {now} | Tool: jscpd {version_str} | Threshold: {threshold}%",
        "",
    ]

    if badge_path:
        parts.append(f"![Copy/Paste]({badge_path})")
        parts.append("")

    parts.extend([
        "## Summary",
        "",
        render_summary_table(projects),
        "",
    ])

    # Status badge
    any_over = any(p["stats"]["percentage"] > threshold for p in projects)
    if any_over:
        over = [p for p in projects if p["stats"]["percentage"] > threshold]
        names = ", ".join(p["name"] for p in over)
        parts.append(
            f"> **WARNING**: Duplication exceeds {threshold}% threshold in: {names}"
        )
    else:
        parts.append(
            f"> Duplication is within the {threshold}% threshold for all projects."
        )
    parts.append("")

    # Collect all duplicates for the overview table
    all_dups = []
    for p in projects:
        for dup in sorted(
            p.get("duplicates", []),
            key=lambda d: d.get("lines", 0),
            reverse=True,
        ):
            all_dups.append((p["name"], dup))
    if cross_project:
        for dup in sorted(
            cross_project.get("duplicates", []),
            key=lambda d: d.get("lines", 0),
            reverse=True,
        ):
            all_dups.append(("cross-project", dup))

    # Duplicate Clusters section with overview table at the top
    parts.append("## Duplicate Clusters")
    parts.append("")

    if not all_dups:
        parts.append("No duplicates found.")
        parts.append("")
        return "\n".join(parts)

    # Overview table
    parts.append(render_overview_table(all_dups))
    parts.append("")

    # Per-project cluster details
    global_idx = 1
    for p in projects:
        if len(projects) > 1:
            parts.append(f"### {p['name']}")
            parts.append("")

        duplicates = p.get("duplicates", [])
        if not duplicates:
            parts.append("No duplicates found.")
            parts.append("")
            continue

        duplicates = sorted(duplicates, key=lambda d: d.get("lines", 0), reverse=True)

        for dup in duplicates:
            parts.append(render_cluster(global_idx, dup,
                                        repo_url=repo_url, branch=branch))
            global_idx += 1

    # Cross-project section
    if cross_project:
        cross_dups = cross_project.get("duplicates", [])
        if cross_dups:
            parts.append("### Cross-Project Duplicates")
            parts.append("")
            cross_dups = sorted(
                cross_dups, key=lambda d: d.get("lines", 0), reverse=True
            )
            for i, dup in enumerate(cross_dups, 1):
                parts.append(render_cluster(global_idx, dup,
                                            prefix="Cross-project ",
                                            repo_url=repo_url, branch=branch))
                global_idx += 1

    return "\n".join(parts)


def main():
    parser = argparse.ArgumentParser(
        description="Generate Markdown duplication report from jscpd JSON"
    )
    parser.add_argument(
        "reports", nargs="+", help="Path(s) to jscpd-report.json files"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=5.0,
        help="Duplication warning threshold percentage (default: 5)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output markdown file (default: stdout)",
    )
    parser.add_argument(
        "--cross-project",
        default=None,
        help="Path to cross-project jscpd-report.json",
    )
    parser.add_argument(
        "--jscpd-version",
        default=None,
        help="jscpd version string for the report header",
    )
    parser.add_argument(
        "--badge-path",
        default=None,
        help="Relative path to the jscpd-badge.svg for embedding in report",
    )
    parser.add_argument(
        "--repo-url",
        default=None,
        help="Repository browse URL (e.g., https://github.com/owner/repo). "
             "Auto-detected from git remote if not specified.",
    )
    parser.add_argument(
        "--branch",
        default=None,
        help="Branch name for file links. Auto-detected from git if not specified.",
    )
    parser.add_argument(
        "--scan-path",
        default=".",
        help="Path that was scanned (used for git auto-detection, default: .)",
    )
    args = parser.parse_args()

    # Auto-detect repo URL and branch if not provided
    repo_url = args.repo_url
    branch = args.branch
    if not repo_url or not branch:
        auto_url, auto_branch = detect_git_info(args.scan_path)
        if not repo_url:
            repo_url = auto_url
        if not branch:
            branch = auto_branch

    projects = []
    for rpath in args.reports:
        data = load_report(rpath)
        name = guess_project_name(rpath)
        projects.append({
            "name": name,
            "stats": data.get("statistics", {}).get("total", {}),
            "duplicates": data.get("duplicates", []),
        })

    cross_project_data = None
    if args.cross_project:
        cross_project_data = load_report(args.cross_project)

    report = render_report(
        projects,
        args.threshold,
        cross_project=cross_project_data,
        jscpd_version=args.jscpd_version,
        badge_path=args.badge_path,
        repo_url=repo_url,
        branch=branch,
    )

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w") as f:
            f.write(report)
        print(f"Report written to: {args.output}", file=sys.stderr)
    else:
        print(report)


if __name__ == "__main__":
    main()
