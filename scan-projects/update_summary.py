#!/usr/bin/env python3
"""Update summary for a specific project in projects.tsv."""

import csv
import sys
from pathlib import Path


def update_summary(folder_name: str, new_summary: str, tsv_path: Path = None):
    """Update the summary for a specific project."""
    if tsv_path is None:
        tsv_path = Path.cwd() / "projects.tsv"

    if not tsv_path.exists():
        print(f"Error: {tsv_path} not found", file=sys.stderr)
        return False

    # Read all rows
    rows = []
    headers = None
    updated = False

    with open(tsv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        headers = reader.fieldnames

        for row in reader:
            if row["folder"] == folder_name:
                row["summary"] = new_summary
                updated = True
            rows.append(row)

    if not updated:
        print(f"Warning: Project '{folder_name}' not found in TSV", file=sys.stderr)
        return False

    # Write back
    with open(tsv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)

    return True


def get_projects_needing_analysis(tsv_path: Path = None, limit: int = None):
    """Get list of projects that need summary analysis."""
    if tsv_path is None:
        tsv_path = Path.cwd() / "projects.tsv"

    projects = []

    with open(tsv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")

        for row in reader:
            if row["summary"] == "NEEDS_ANALYSIS":
                projects.append(row["folder"])
                if limit and len(projects) >= limit:
                    break

    return projects


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  List projects needing analysis:")
        print("    python3 update_summary.py --list [limit]")
        print("  Update a project summary:")
        print("    python3 update_summary.py <folder> <summary>")
        sys.exit(1)

    if sys.argv[1] == "--list":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
        projects = get_projects_needing_analysis(limit=limit)
        print(f"Projects needing analysis: {len(projects)}")
        for proj in projects:
            print(f"  - {proj}")
    else:
        folder = sys.argv[1]
        summary = sys.argv[2]
        if update_summary(folder, summary):
            print(f"Updated summary for '{folder}'")
        else:
            sys.exit(1)
