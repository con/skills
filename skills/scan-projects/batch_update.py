#!/usr/bin/env python3
"""Batch update summaries from a JSON input."""

import csv
import json
import sys
from pathlib import Path


def batch_update_summaries(updates: dict, tsv_path: Path = None):
    """
    Batch update summaries.

    Args:
        updates: Dict of {folder_name: new_summary}
        tsv_path: Path to projects.tsv

    Returns:
        Tuple of (num_updated, num_not_found)
    """
    if tsv_path is None:
        tsv_path = Path.cwd() / "projects.tsv"

    if not tsv_path.exists():
        print(f"Error: {tsv_path} not found", file=sys.stderr)
        return 0, 0

    # Read all rows
    rows = []
    headers = None
    updated_count = 0
    not_found = []

    with open(tsv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        headers = reader.fieldnames

        for row in reader:
            folder = row["folder"]
            if folder in updates:
                row["summary"] = updates[folder]
                updated_count += 1
            rows.append(row)

    # Check for folders that weren't found
    found_folders = {row["folder"] for row in rows}
    not_found = [f for f in updates.keys() if f not in found_folders]

    # Write back
    with open(tsv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)

    return updated_count, len(not_found)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  From JSON file:")
        print("    python3 batch_update.py updates.json")
        print("  From stdin:")
        print("    echo '{\"folder1\": \"summary1\"}' | python3 batch_update.py -")
        print("")
        print("JSON format: {\"folder_name\": \"summary text\", ...}")
        sys.exit(1)

    # Read JSON
    if sys.argv[1] == "-":
        updates = json.load(sys.stdin)
    else:
        with open(sys.argv[1], "r") as f:
            updates = json.load(f)

    # Perform batch update
    updated, not_found = batch_update_summaries(updates)

    print(f"Updated {updated} project summaries")
    if not_found > 0:
        print(f"Warning: {not_found} projects not found in TSV", file=sys.stderr)
