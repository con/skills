#!/usr/bin/env python3
"""Gather open GitHub issues via gh CLI."""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def detect_repo() -> str:
    """Detect OWNER/REPO from git remote origin."""
    result = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        capture_output=True, text=True, check=True,
    )
    url = result.stdout.strip()
    # Handle SSH: git@github.com:owner/repo.git
    if url.startswith("git@"):
        path = url.split(":", 1)[1]
    # Handle HTTPS: https://github.com/owner/repo.git
    elif "github.com" in url:
        path = url.split("github.com/", 1)[1]
    else:
        raise ValueError(f"Cannot parse repo from remote URL: {url}")
    return path.removesuffix(".git")


def gather_from_gh(
    repo: str, limit: int, label: str | None = None
) -> list[dict]:
    """Fetch open issues from GitHub using gh CLI."""
    cmd = [
        "gh", "issue", "list",
        "--repo", repo,
        "--json", "number,title,labels,createdAt,updatedAt,body,author,comments,url",
        "--limit", str(limit),
        "--state", "open",
    ]
    if label:
        cmd.extend(["--label", label])
    result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=60)
    return json.loads(result.stdout)


def compute_last_comment_at(comments: list[dict]) -> str | None:
    """Extract the timestamp of the most recent comment."""
    if not comments:
        return None
    dates = [c.get("createdAt", "") for c in comments if c.get("createdAt")]
    if not dates:
        return None
    return max(dates)


def transform_issues(raw_issues: list[dict]) -> list[dict]:
    """Transform gh CLI output to our schema."""
    issues = []
    for raw in raw_issues:
        last_comment = compute_last_comment_at(raw.get("comments", []))
        issues.append({
            "number": raw["number"],
            "title": raw["title"],
            "body": raw.get("body", ""),
            "labels": [label["name"] for label in raw.get("labels", [])],
            "state": "OPEN",
            "created_at": raw.get("createdAt", ""),
            "updated_at": raw.get("updatedAt", ""),
            "last_comment_at": last_comment,
            "author": raw.get("author", {}).get("login", "unknown"),
            "comments_count": len(raw.get("comments", [])),
            "url": raw.get("url", ""),
        })
    return issues


def get_head_sha() -> str:
    """Get HEAD commit SHA for building GitHub permalink URLs."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return ""


def main() -> None:
    parser = argparse.ArgumentParser(description="Gather open GitHub issues")
    parser.add_argument(
        "--repo", help="OWNER/REPO (auto-detected from git remote if omitted)"
    )
    parser.add_argument(
        "--limit", type=int, default=0, help="Max issues to fetch (0 = all, default: all)"
    )
    parser.add_argument("--label", help="Filter by label")
    parser.add_argument(
        "--output", type=Path, default=None,
        help="Output path (default: .git/triage/issues.json)",
    )
    args = parser.parse_args()

    repo = args.repo or detect_repo()
    output = args.output or Path(".git/triage/issues.json")
    output.parent.mkdir(parents=True, exist_ok=True)

    print(f"Gathering issues from {repo} (limit: {args.limit})...")
    raw_issues = gather_from_gh(repo, args.limit, args.label)
    issues = transform_issues(raw_issues)

    data = {
        "repo": repo,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": "gh",
        "head_sha": get_head_sha(),
        "issues": issues,
    }

    output.write_text(json.dumps(data, indent=2))
    print(f"Wrote {len(issues)} issues to {output}")


if __name__ == "__main__":
    main()
