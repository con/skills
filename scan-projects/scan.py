#!/usr/bin/env python3
"""Scan git repositories and generate projects.tsv summary."""

import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Optional


def run_git(repo_path: Path, *args) -> Optional[str]:
    """Run a git command in the given repository."""
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_path)] + list(args),
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except (subprocess.TimeoutExpired, subprocess.SubprocessError):
        return None


def get_earliest_commit(repo_path: Path) -> str:
    """Get the earliest commit date."""
    output = run_git(repo_path, "log", "--reverse", "--format=%aI", "--all")
    if output:
        return output.split("\n")[0]
    return "N/A"


def get_latest_commit(repo_path: Path) -> str:
    """Get the latest commit date from main/master branch."""
    # Try different branch names
    for ref in ["origin/HEAD", "origin/main", "origin/master", "main", "master", "HEAD"]:
        output = run_git(repo_path, "log", "-1", "--format=%aI", ref)
        if output:
            return output
    return "N/A"


def get_remote_url(repo_path: Path) -> str:
    """Get the git remote URL."""
    output = run_git(repo_path, "remote", "get-url", "origin")
    return output if output else "N/A"


def get_primary_language(repo_path: Path) -> str:
    """Determine primary language by counting file extensions."""
    # Language mappings
    lang_map = {
        ".py": "Python",
        ".js": "JavaScript",
        ".ts": "TypeScript",
        ".java": "Java",
        ".cpp": "C++",
        ".cc": "C++",
        ".cxx": "C++",
        ".c": "C",
        ".h": "C/C++",
        ".rs": "Rust",
        ".go": "Go",
        ".rb": "Ruby",
        ".jl": "Julia",
        ".r": "R",
        ".R": "R",
        ".m": "MATLAB",
        ".swift": "Swift",
        ".kt": "Kotlin",
        ".scala": "Scala",
        ".sh": "Shell",
        ".bash": "Shell",
        ".php": "PHP",
        ".cs": "C#",
        ".html": "HTML",
        ".css": "CSS",
        ".tex": "TeX",
    }

    # Exclude directories
    exclude_dirs = {".git", "node_modules", "venv", ".venv", "__pycache__",
                   ".tox", "dist", "build", ".eggs", ".npm", ".cache"}

    ext_counter = Counter()

    try:
        for root, dirs, files in os.walk(repo_path):
            # Remove excluded directories from dirs in-place
            dirs[:] = [d for d in dirs if d not in exclude_dirs]

            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in lang_map:
                    ext_counter[ext] += 1
    except (PermissionError, OSError):
        pass

    if ext_counter:
        most_common_ext = ext_counter.most_common(1)[0][0]
        return lang_map[most_common_ext]

    return "Unknown"


def get_license(repo_path: Path) -> str:
    """Find and parse LICENSE file."""
    # Common license file patterns
    license_patterns = ["LICENSE", "LICENSE.txt", "LICENSE.md", "COPYING",
                       "COPYING.txt", "LICENSE-MIT", "LICENSE-APACHE"]

    for pattern in license_patterns:
        for case_variant in [pattern, pattern.lower(), pattern.upper()]:
            license_file = repo_path / case_variant
            if license_file.exists():
                try:
                    content = license_file.read_text(encoding="utf-8", errors="ignore")
                    # Try to detect license type from content
                    first_lines = content[:500].upper()

                    if "MIT LICENSE" in first_lines or "MIT License" in content[:200]:
                        return "MIT"
                    elif "APACHE LICENSE" in first_lines:
                        if "VERSION 2.0" in first_lines:
                            return "Apache-2.0"
                        return "Apache"
                    elif "GNU GENERAL PUBLIC LICENSE" in first_lines:
                        if "VERSION 3" in first_lines:
                            return "GPL-3.0"
                        elif "VERSION 2" in first_lines:
                            return "GPL-2.0"
                        return "GPL"
                    elif "GNU LESSER GENERAL PUBLIC LICENSE" in first_lines:
                        return "LGPL"
                    elif "BSD" in first_lines:
                        if "3-CLAUSE" in first_lines:
                            return "BSD-3-Clause"
                        elif "2-CLAUSE" in first_lines:
                            return "BSD-2-Clause"
                        return "BSD"
                    elif "MOZILLA PUBLIC LICENSE" in first_lines:
                        return "MPL"
                    elif "CREATIVE COMMONS" in first_lines:
                        return "CC"
                    else:
                        # Return filename if we can't determine type
                        return os.path.basename(license_file)
                except (OSError, UnicodeDecodeError):
                    pass

    return "Unknown"


def get_summary(repo_path: Path) -> str:
    """Mark summary for Claude analysis."""
    # Mark all summaries as needing analysis by Claude
    return "NEEDS_ANALYSIS"


def scan_repository(repo_path: Path) -> dict:
    """Scan a single repository and return metadata."""
    folder = repo_path.name

    return {
        "folder": folder,
        "summary": get_summary(repo_path),
        "language": get_primary_language(repo_path),
        "license": get_license(repo_path),
        "earliest_commit": get_earliest_commit(repo_path),
        "latest_commit": get_latest_commit(repo_path),
        "url": get_remote_url(repo_path),
    }


def read_existing_tsv(tsv_path: Path) -> dict:
    """Read existing projects.tsv and return dict of folder -> data."""
    existing = {}
    if not tsv_path.exists():
        return existing

    try:
        with open(tsv_path, "r", encoding="utf-8") as f:
            header = f.readline().strip().split("\t")
            for line in f:
                parts = line.strip().split("\t")
                if len(parts) >= len(header):
                    folder = parts[0]
                    existing[folder] = dict(zip(header, parts))
    except (OSError, UnicodeDecodeError) as e:
        print(f"Warning: Could not read existing TSV: {e}", file=sys.stderr)

    return existing


def write_tsv(tsv_path: Path, projects: list):
    """Write projects data to TSV file."""
    headers = ["folder", "summary", "language", "license", "earliest_commit", "latest_commit", "url"]

    with open(tsv_path, "w", encoding="utf-8") as f:
        f.write("\t".join(headers) + "\n")
        for proj in projects:
            row = [proj.get(h, "N/A") for h in headers]
            # Escape tabs and newlines in data
            row = [str(val).replace("\t", " ").replace("\n", " ").replace("\r", " ") for val in row]
            f.write("\t".join(row) + "\n")


def main():
    """Main scanning function."""
    base_dir = Path.cwd()
    tsv_path = base_dir / "projects.tsv"

    # Read existing data
    existing = read_existing_tsv(tsv_path)

    # Scan directories
    all_projects = []
    new_count = 0
    skip_count = 0
    error_count = 0
    errors = []

    # Get all directories
    subdirs = [d for d in base_dir.iterdir() if d.is_dir() and d.name != ".claude"]
    total = len(subdirs)

    print(f"Scanning {total} directories...")

    for i, subdir in enumerate(subdirs, 1):
        folder_name = subdir.name

        # Skip if not a git repo
        if not (subdir / ".git").exists():
            continue

        print(f"[{i}/{total}] Processing {folder_name}...", end="")

        # Skip if already exists (unless we want to force update)
        if folder_name in existing:
            all_projects.append(existing[folder_name])
            skip_count += 1
            print(" (skipped)")
            continue

        try:
            proj_data = scan_repository(subdir)
            all_projects.append(proj_data)
            new_count += 1
            print(f" ✓ ({proj_data['language']})")
        except Exception as e:
            error_count += 1
            errors.append((folder_name, str(e)))
            print(f" ✗ Error: {e}")
            # Add placeholder entry
            all_projects.append({
                "folder": folder_name,
                "summary": "Error during scan",
                "language": "Unknown",
                "license": "Unknown",
                "earliest_commit": "N/A",
                "latest_commit": "N/A",
                "url": "N/A",
            })

    # Sort by folder name
    all_projects.sort(key=lambda x: x["folder"].lower())

    # Write TSV
    write_tsv(tsv_path, all_projects)

    # Print summary
    print("\n" + "=" * 60)
    print(f"Scanned {total} directories")
    print(f"- New projects: {new_count}")
    print(f"- Skipped (existing): {skip_count}")
    print(f"- Errors: {error_count}")

    if errors:
        print("\nErrors:")
        for folder, error in errors:
            print(f"  - {folder}: {error}")

    print(f"\nUpdated projects.tsv with {len(all_projects)} entries")
    print(f"\nYou can view the results with: vd projects.tsv")


if __name__ == "__main__":
    main()
