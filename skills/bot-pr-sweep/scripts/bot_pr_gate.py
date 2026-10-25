#!/usr/bin/env python3
"""Decide whether a dependency-bot pull request is safe to act on.

Two checks, both pure functions over JSON that the GitHub MCP tools return:

* ``author``  -- is the PR really opened by a trusted bot? Matches the numeric
  account ID and the login together. The login alone is a name a sender can
  claim; the ID is what GitHub assigns to the account.
* ``checks``  -- is the head commit green? Every check run must have finished
  with success, skipped or neutral, and every commit status must be success.

Usage::

    bot_pr_gate.py author PR.json
    bot_pr_gate.py checks CHECK_RUNS.json COMMIT_STATUS.json

Exit status is 0 when the check passes and 1 otherwise, so the script can gate
a shell pipeline. The JSON files are the raw outputs of
``pull_request_read`` (``get``, ``get_check_runs``, ``get_status``).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Account IDs are assigned by GitHub and do not change when an account is
# renamed. Verify against a PR that was opened by the bot before trusting an
# update here (see SKILL.md, "Known bot identities").
TRUSTED_BOTS = {
    49699333: "dependabot[bot]",
    66853113: "pre-commit-ci[bot]",
}

PASSING_CHECK_CONCLUSIONS = {"success", "skipped", "neutral"}


def check_author(pr: dict) -> tuple[bool, str]:
    """Return (trusted, reason) for the PR's author."""
    user = pr.get("user") or {}
    user_id = user.get("id")
    login = user.get("login")
    if user_id is None or login is None:
        return False, "PR JSON has no user.id / user.login"
    expected_login = TRUSTED_BOTS.get(user_id)
    if expected_login is None:
        return False, f"user.id {user_id} ({login!r}) is not a trusted bot ID"
    if login != expected_login:
        return False, f"user.id {user_id} matches {expected_login}, but login is {login!r}"
    return True, f"author is {login} (id {user_id})"


def check_head(check_runs: dict, commit_status: dict) -> tuple[str, list[str]]:
    """Return (verdict, reasons) for the head commit.

    verdict is ``GREEN``, ``PENDING`` or ``RED``. ``PENDING`` means something
    has not finished yet and the sweep should look again later. ``RED`` means a
    finished check failed and the PR needs a human or a fix.
    """
    reasons: list[str] = []
    pending = False
    red = False

    for run in check_runs.get("check_runs", []):
        name = run.get("name", "?")
        status = run.get("status")
        conclusion = run.get("conclusion")
        if status != "completed":
            pending = True
            reasons.append(f"check {name!r} is {status}")
        elif conclusion not in PASSING_CHECK_CONCLUSIONS:
            red = True
            reasons.append(f"check {name!r} concluded {conclusion}")

    combined = commit_status.get("state")
    contexts = commit_status.get("statuses", [])
    if combined == "pending" and not contexts:
        pending = True
        reasons.append("combined status is pending with no contexts reported")
    elif combined == "failure" or combined == "error":
        red = True
        reasons.append(f"combined status is {combined}")
    for ctx in contexts:
        state = ctx.get("state")
        if state == "pending":
            pending = True
            reasons.append(f"status {ctx.get('context')!r} is pending")
        elif state != "success":
            red = True
            reasons.append(f"status {ctx.get('context')!r} is {state}")

    if red:
        return "RED", reasons
    if pending:
        return "PENDING", reasons
    return "GREEN", reasons


def _load(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_author = sub.add_parser("author", help="verify the PR author by account ID")
    p_author.add_argument("pr_json")

    p_checks = sub.add_parser("checks", help="verify the head commit is green")
    p_checks.add_argument("check_runs_json")
    p_checks.add_argument("status_json")

    args = parser.parse_args(argv)

    if args.cmd == "author":
        trusted, reason = check_author(_load(args.pr_json))
        print(("TRUSTED: " if trusted else "UNTRUSTED: ") + reason)
        return 0 if trusted else 1

    verdict, reasons = check_head(_load(args.check_runs_json), _load(args.status_json))
    print(verdict)
    for reason in reasons:
        print(f"  - {reason}")
    return 0 if verdict == "GREEN" else 1


if __name__ == "__main__":
    sys.exit(main())
