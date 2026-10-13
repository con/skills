#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Yaroslav Halchenko <yaroslav.o.halchenko@dartmouth.edu>
# SPDX-License-Identifier: MIT
"""Refresh the vendored STAMPED checklist pin.

Downloads ``stamped-checklist.json`` from stamped-checklist-schema at a tag,
resolves that tag to a commit, and writes

    checklist/stamped-checklist-<version>.json
    checklist/lock.json

The checklist is the only item source the STAMPED skills use, and it is never
hand-edited: this script is the only writer.  Run it through the project's
recorded mechanism so the refresh is itself provenance-tracked, e.g.

    datalad run -m 'vendor checklist v0.3.2' \
        python3 stamped-conventions/scripts/vendor_checklist.py --tag v0.3.2

Then bump ``version:`` in ``stamped-conventions/SKILL.md`` (MINOR) and add a
changelog line, because every report records the pin it used.

Usage:
    vendor_checklist.py [--tag v0.3.1] [--check] [--force] [--offline FILE]

    --check    verify the files on disk against lock.json and exit
    --force    replace an existing vendored file for the same version
    --offline  read the JSON from FILE instead of the network (commit still
               has to be given with --commit)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
import urllib.request

REPO = "https://github.com/stamped-principles/stamped-checklist-schema"
API = "https://api.github.com/repos/stamped-principles/stamped-checklist-schema"
RAW = "https://raw.githubusercontent.com/stamped-principles/stamped-checklist-schema"
PATH_IN_REPO = "stamped-checklist.json"

HERE = pathlib.Path(__file__).resolve().parent
CHECKLIST_DIR = HERE.parent / "checklist"
LOCK = CHECKLIST_DIR / "lock.json"


def _fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "con-skills-stamped-conventions"})
    with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310 - fixed https host
        return resp.read()


def _counts(data: dict) -> dict:
    return {lvl["level"]: sum(len(e["items"]) for e in lvl["entries"]) for lvl in data["data"]}


def check() -> int:
    if not LOCK.exists():
        print(f"error: {LOCK} is missing", file=sys.stderr)
        return 1
    lock = json.loads(LOCK.read_text())
    target = CHECKLIST_DIR / lock["file"]
    if not target.exists():
        print(f"error: {target} is missing but lock.json names it", file=sys.stderr)
        return 1
    raw = target.read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    if actual != lock["sha256"]:
        print(
            f"error: {target.name} sha256 {actual} != lock {lock['sha256']}\n"
            "       the vendored checklist was edited by hand; re-run without --check",
            file=sys.stderr,
        )
        return 1
    data = json.loads(raw)
    if data["checklist_version"] != lock["checklist_version"]:
        print("error: checklist_version in the file and in lock.json disagree", file=sys.stderr)
        return 1
    if _counts(data) != lock["item_counts"]:
        print("error: item counts in the file and in lock.json disagree", file=sys.stderr)
        return 1
    total = sum(lock["item_counts"].values())
    print(f"ok: checklist {lock['checklist_version']} ({total} items) matches lock.json")
    return 0


def vendor(tag: str, commit: str | None, offline: pathlib.Path | None, force: bool, today: str) -> int:
    if offline is None:
        if commit is None:
            meta = json.loads(_fetch(f"{API}/commits/{tag}"))
            commit = meta["sha"]
        raw = _fetch(f"{RAW}/{commit}/{PATH_IN_REPO}")
    else:
        if commit is None:
            print("error: --offline requires --commit", file=sys.stderr)
            return 2
        raw = offline.read_bytes()

    data = json.loads(raw)
    version = data["checklist_version"]
    target = CHECKLIST_DIR / f"stamped-checklist-{version}.json"
    if target.exists() and target.read_bytes() != raw and not force:
        print(f"error: {target} exists with different content; pass --force", file=sys.stderr)
        return 1

    counts = _counts(data)
    lock = {
        "checklist_version": version,
        "schema_version": data.get("schema_version"),
        "principles_version": data.get("principles_version"),
        "source": {
            "repo": REPO,
            "tag": tag,
            "commit": commit,
            "path": PATH_IN_REPO,
            "url": f"{RAW}/{commit}/{PATH_IN_REPO}",
        },
        "file": target.name,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "size": len(raw),
        "vendored_at": today,
        "vendored_by": "stamped-conventions/scripts/vendor_checklist.py",
        "item_counts": counts,
    }

    CHECKLIST_DIR.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
    LOCK.write_text(json.dumps(lock, indent=2) + "\n")
    total = sum(counts.values())
    print(f"vendored checklist {version} ({total} items: {counts}) from {tag} @ {commit[:7]}")
    print(f"  {target}\n  {LOCK}")
    print("next: bump version: in stamped-conventions/SKILL.md and add a changelog line")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tag", default="v0.3.1", help="upstream tag to pin (default: %(default)s)")
    ap.add_argument("--commit", help="commit the tag resolves to (looked up when omitted)")
    ap.add_argument("--offline", type=pathlib.Path, help="read the JSON from a local file")
    ap.add_argument("--check", action="store_true", help="verify the vendored files against lock.json")
    ap.add_argument("--force", action="store_true", help="replace an existing vendored file")
    ap.add_argument("--date", default=None, help="date recorded as vendored_at (default: today, UTC)")
    args = ap.parse_args(argv)

    if args.check:
        return check()
    import datetime

    today = args.date or datetime.datetime.now(datetime.timezone.utc).date().isoformat()
    return vendor(args.tag, args.commit, args.offline, args.force, today)


if __name__ == "__main__":
    sys.exit(main())
