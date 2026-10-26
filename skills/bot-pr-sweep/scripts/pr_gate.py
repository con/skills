#!/usr/bin/env python3
"""Fail-closed gate for dependency-bot pull requests.

Standard library only. Every subcommand reads raw GitHub REST JSON that the
sweep saved to files (``gh api ... > file``) and never contacts GitHub itself,
so the decision logic is unit-testable and the agent running the sweep has no
reason to read pull-request titles, bodies, comments or check output.

Subcommands
-----------
init                      create the run's working directory and print its path
select    PULLS.json      pick the open PRs opened by a trusted bot, matched on
                          the numeric account ID (``user.id``), never the login
gate      decide ``merge`` / ``pending`` / ``blocked`` / ``rejected`` for one PR
outcome   record what the sweep then did (merged, failed, dry run, repo error)
report    render the Markdown report from the ledger the commands above write

Exit status: ``gate`` exits 0 only for the verdict ``merge``, 1 for any other
verdict and 2 when the input is unusable. The other subcommands exit 0 on
success and 2 on unusable input. Nothing here ever exits 0 by accident: a
missing, empty, malformed or truncated payload is ``pending`` or ``blocked``.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

# GitHub account IDs never change, unlike logins. Verify an ID against a PR
# the bot opened in one of your repositories before changing this table.
TRUSTED_BOTS = {
    49699333: "dependabot[bot]",
    66853113: "pre-commit-ci[bot]",
}
# Bots whose commits GitHub creates and signs itself. Their commits must carry
# a verified signature, which rules out a commit that merely spoofs the bot's
# noreply address. pre-commit.ci pushes unsigned commits, so for it the gate
# relies on branch protection keeping other people off the bot's branch.
SIGNED_BOTS = frozenset({49699333})
# Commits GitHub creates itself (every Dependabot commit, every "Update
# branch" merge) carry GitHub's own `web-flow` account as the committer.
WEB_FLOW_ID = 19864447

PASSING_CONCLUSIONS = frozenset({"success"})
# GitHub counts these as passing for required checks; --strict refuses them.
TOLERATED_CONCLUSIONS = frozenset({"skipped", "neutral"})
# Conclusions that often mean the job never ran rather than that it failed.
RERUN_CONCLUSIONS = frozenset({"cancelled", "timed_out", "startup_failure", "stale"})
MERGEABLE_OK = frozenset({"clean", "has_hooks"})
RESULTS = frozenset({
    "merged", "merge-failed", "assigned", "assign-failed", "dry-run", "repo-error",
    "branch-updated", "update-failed",
})
DEFAULT_SETTLE = timedelta(minutes=10)

MERGE, PENDING, BLOCKED, REJECTED = "merge", "pending", "blocked", "rejected"

_URL = re.compile(r"https://[A-Za-z0-9._~:/?#@!$&'*+,;=%-]+")
_REPO = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
_SHA = re.compile(r"[0-9a-f]{40}")
_VERSION = re.compile(r"^version:\s*([0-9]+\.[0-9]+\.[0-9]+)\s*$", re.MULTILINE)


class GateInputError(Exception):
    """The input cannot be judged at all (wrong file, wrong repository)."""


# --------------------------------------------------------------------------
# Small helpers: every accessor tolerates garbage and returns a neutral value.
# --------------------------------------------------------------------------

def _dict(value: object) -> dict:
    return value if isinstance(value, dict) else {}


def _list(value: object) -> list:
    return value if isinstance(value, list) else []


def _int(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _str(value: object) -> str:
    return value if isinstance(value, str) else ""


def sanitize(value: object, limit: int = 100) -> str:
    """Make contributor-controlled text safe to print inside backticks."""
    text = "".join(ch if ch.isprintable() else " " for ch in _str(value))
    text = " ".join(text.replace("`", "'").split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def safe_url(value: object) -> str:
    text = _str(value)
    return text if _URL.fullmatch(text) else ""


def parse_time(value: object) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(_str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def iso(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_json(path: str) -> object:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def pages(document: object) -> list:
    """Unnest `gh api --paginate --slurp` output (an array of pages) into one list."""
    items: list = []
    for item in document if isinstance(document, list) else [document]:
        items.extend(item if isinstance(item, list) else [item])
    return items


def skill_version(skill_dir: Path) -> str:
    """The `version:` from this skill's SKILL.md frontmatter, for the report stamp."""
    try:
        text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    except OSError:
        return "unknown"
    match = _VERSION.search(text.split("\n---", 2)[0] if text.startswith("---") else "")
    return match.group(1) if match else "unknown"


def repo_name(value: str) -> str:
    if not _REPO.fullmatch(value):
        raise argparse.ArgumentTypeError(f"expected OWNER/REPO, got {value!r}")
    return value


def commit_sha(value: str) -> str:
    if not _SHA.fullmatch(value):
        raise argparse.ArgumentTypeError(f"expected a 40-character commit id, got {value!r}")
    return value


# --------------------------------------------------------------------------
# select
# --------------------------------------------------------------------------

def bot_name_hints() -> set[str]:
    """Name fragments that make an untrusted login look like a trusted bot."""
    hints = set()
    for login in TRUSTED_BOTS.values():
        base = login.split("[", 1)[0].lower()
        hints.add(base)
        if "-" in base:
            hints.add(base.rsplit("-", 1)[0])
    return hints


def select_bot_prs(pulls: list) -> tuple[list, list, int]:
    """Split open PRs into trusted-bot PRs, suspicious look-alikes and other bots."""
    selected, suspicious, other_bots = [], [], 0
    hints = bot_name_hints()
    for pull in pulls:
        pull = _dict(pull)
        user = _dict(pull.get("user"))
        number, user_id, login = _int(pull.get("number")), _int(user.get("id")), _str(user.get("login"))
        if number is None:
            continue
        entry = {
            "number": number, "login": login, "id": user_id,
            "head_sha": _str(_dict(pull.get("head")).get("sha")),
        }
        if user_id in TRUSTED_BOTS:
            if login != TRUSTED_BOTS[user_id]:
                suspicious.append({**entry, "reason": (
                    f"account {user_id} is {TRUSTED_BOTS[user_id]} but the login reads "
                    f"'{sanitize(login, 40)}'")})
            elif not _SHA.fullmatch(entry["head_sha"]):
                suspicious.append({**entry, "head_sha": "", "reason": "head commit id is malformed"})
            else:
                selected.append(entry)
        elif any(hint in login.lower() for hint in hints):
            suspicious.append({**entry, "reason": (
                f"login '{sanitize(login, 40)}' resembles a trusted bot but account "
                f"{user_id} is not trusted")})
        elif login.endswith("[bot]") or user.get("type") == "Bot":
            other_bots += 1
    return selected, suspicious, other_bots


# --------------------------------------------------------------------------
# gate
# --------------------------------------------------------------------------

def _signed(commit: dict) -> bool:
    return _dict(_dict(commit.get("commit")).get("verification")).get("verified") is True


def merge_commit_problems(commit: dict, parents: list[str], previous: str, allowed: bool) -> list[str]:
    """Why a merge commit on the bot's branch is not GitHub's own Update branch merge.

    Update branch merges the base into the bot's branch: two parents, one of
    them the bot's previous head, committed and signed by GitHub. Anything
    merged in that is not already in the base shows up as further commits in
    the pull request, where the author rule catches it.
    """
    if not allowed:
        return ["is a merge commit, so someone updated the bot's branch"]
    problems = []
    if len(parents) != 2:
        problems.append(f"merges {len(parents)} parents")
    elif previous not in parents:
        problems.append("does not continue the bot's previous commit")
    if _int(_dict(commit.get("committer")).get("id")) != WEB_FLOW_ID:
        problems.append("was not committed by GitHub, so it is not an Update branch merge")
    if not _signed(commit):
        problems.append("carries no valid GitHub signature")
    return problems


def evaluate(pr: object, commits: list, check_pages: list, status: object, *,
             repo: str, expected_head: str, require_checks: tuple[str, ...] = (),
             require_labels: tuple[str, ...] = (), forbid_labels: tuple[str, ...] = (),
             strict: bool = False, allow_branch_update: bool = False,
             settle: timedelta = DEFAULT_SETTLE, now: datetime | None = None) -> dict:
    """Decide one pull request. Returns the decision record (see SKILL.md)."""
    now = now or utc_now()
    pr = _dict(pr)
    user, head, base = _dict(pr.get("user")), _dict(pr.get("head")), _dict(pr.get("base"))
    number, user_id, login = _int(pr.get("number")), _int(user.get("id")), _str(user.get("login"))
    head_sha = _str(head.get("sha"))
    base_repo = _str(_dict(base.get("repo")).get("full_name"))
    head_repo = _str(_dict(head.get("repo")).get("full_name"))
    base_ref = sanitize(base.get("ref"), 60) or "the base branch"
    if number is None or not _SHA.fullmatch(head_sha):
        raise GateInputError("PR JSON has no number or no 40-character head.sha; is it a pull request object?")
    if base_repo.lower() != repo.lower():
        raise GateInputError(f"PR JSON belongs to '{sanitize(base_repo, 80) or 'an unknown repository'}', not {repo}")

    reasons: dict[str, list[str]] = {REJECTED: [], BLOCKED: [], PENDING: []}
    hints: list[str] = []
    rejected, blocked, pending = (reasons[k].append for k in (REJECTED, BLOCKED, PENDING))

    # Author: the account ID decides, the login must agree with it.
    if user_id not in TRUSTED_BOTS:
        rejected(f"author '{sanitize(login, 40)}' (account {user_id}) is not a trusted bot")
    elif login != TRUSTED_BOTS[user_id]:
        rejected(f"account {user_id} is {TRUSTED_BOTS[user_id]} but the login reads '{sanitize(login, 40)}'")
    elif user.get("type") != "Bot":
        rejected(f"account {user_id} is of type {sanitize(user.get('type'), 20) or 'unknown'}, not Bot")

    # Pull request state and labels.
    state = sanitize(pr.get("state"), 20)
    if state != "open":
        blocked(f"pull request is {state or 'in an unknown state'}")
    if pr.get("draft") is True:
        blocked("pull request is a draft")
    if head_repo.lower() != base_repo.lower():
        blocked(f"head branch lives in '{sanitize(head_repo, 80) or 'a deleted or foreign repository'}', not {repo}")
    if expected_head != head_sha:
        pending(f"head moved from {expected_head[:7]} to {head_sha[:7]} since listing; run the gate again")
    label_entries = pr.get("labels")
    labels_valid = isinstance(label_entries, list) and all(
        isinstance(label, dict) and isinstance(label.get("name"), str) for label in label_entries)
    if (require_labels or forbid_labels) and not labels_valid:
        pending("labels payload is missing or malformed; fetch the pull request again")
    labels = {label["name"].strip().casefold() for label in label_entries} if labels_valid else set()
    for label in require_labels if labels_valid else ():
        if label.strip().casefold() not in labels:
            blocked(f"required label `{sanitize(label, 60)}` is missing")
    for label in forbid_labels if labels_valid else ():
        if label.strip().casefold() in labels:
            blocked(f"label `{sanitize(label, 60)}` excludes the pull request from automatic merging")

    mergeable, mergeable_state = pr.get("mergeable"), sanitize(pr.get("mergeable_state"), 20)
    behind = False
    rebase_hint = ""
    if TRUSTED_BOTS.get(user_id) == "dependabot[bot]":
        rebase_hint = ("comment `@dependabot rebase` on the PR so the bot updates its own branch; "
                       "the sweep never pushes to it")
    if mergeable is None or mergeable_state in ("", "unknown"):
        pending("GitHub has not finished computing mergeability; retry shortly")
    elif mergeable is False or mergeable_state == "dirty":
        blocked(f"merge conflicts with `{base_ref}`")
        hints.append(rebase_hint)
    elif mergeable_state == "behind":
        behind = True
        blocked(f"branch is behind `{base_ref}` and the branch protection requires an up-to-date branch")
        hints.append("" if allow_branch_update else rebase_hint)
    elif mergeable_state == "blocked":
        blocked("branch protection is not satisfied (reviews, required checks or merge queue)")
    elif mergeable_state == "unstable":
        blocked("GitHub reports failing status checks (mergeable_state is unstable)")
    elif mergeable_state not in MERGEABLE_OK:
        blocked(f"unrecognized mergeable_state '{mergeable_state}'")

    # Commits: every one from a trusted bot, the list whole, merges only GitHub's own.
    commits = [_dict(c) for c in commits]
    expected_commits = _int(pr.get("commits"))
    if not commits:
        pending("no commits returned for the pull request")
    else:
        if expected_commits is None or len(commits) != expected_commits:
            pending(f"commit list incomplete ({len(commits)} of {expected_commits}); fetch every page")
        elif _str(commits[-1].get("sha")) != head_sha:
            pending("commit list does not end at the head commit; fetch it again")
        newest: datetime | None = None
        for index, commit in enumerate(commits):
            short = sanitize(commit.get("sha"), 40)[:7] or "?"
            parents = [_str(_dict(parent).get("sha")) for parent in _list(commit.get("parents"))]
            if len(parents) > 1:
                previous = _str(commits[index - 1].get("sha")) if index else ""
                for problem in merge_commit_problems(commit, parents, previous, allow_branch_update):
                    blocked(f"commit {short} {problem}")
            else:
                # Every ordinary commit is bound to the PR's author, not to the bot table as a whole,
                # so a commit spoofing another trusted bot's address does not pass.
                author_id = _int(_dict(commit.get("author")).get("id"))
                committer_id = _int(_dict(commit.get("committer")).get("id"))
                if author_id is None:
                    blocked(f"commit {short} has no GitHub-linked author account (REST commits JSON needed)")
                elif author_id != user_id:
                    blocked(f"commit {short} was authored by account {author_id}, not by the pull request's author")
                elif user_id in SIGNED_BOTS and not _signed(commit):
                    blocked(f"commit {short} claims to be by {TRUSTED_BOTS[user_id]} but carries no verified "
                            "GitHub signature")
                if committer_id not in (user_id, WEB_FLOW_ID):
                    blocked(f"commit {short} was committed by account {committer_id}, neither the author nor GitHub")
            when = parse_time(_dict(_dict(commit.get("commit")).get("committer")).get("date"))
            if when and (newest is None or when > newest):
                newest = when
        if settle > timedelta(0):
            if newest is None:
                pending("cannot read the commit dates needed for the settle time")
            elif now - newest < settle:
                minutes = int((now - newest).total_seconds() // 60)
                pending(f"head commit is {minutes} min old; waiting {int(settle.total_seconds() // 60)} min "
                        "for CI to register every check")

    # Check runs: complete list, every one bound to the head and finished, none failed.
    passed: list[str] = []
    tolerated: list[str] = []
    failed: list[str] = []
    unfinished: list[str] = []
    runs: list = []
    check_pages = list(check_pages)
    checks_valid = bool(check_pages) and all(isinstance(page, dict) and "check_runs" in page for page in check_pages)
    ci_known = checks_valid  # false whenever a payload does not describe this head commit
    if not checks_valid:
        pending("check-run payload is not a GitHub check-runs object; fetch it again")
    else:
        totals = {_int(page.get("total_count")) for page in check_pages}
        total = totals.pop() if len(totals) == 1 else None
        for page in check_pages:
            runs.extend(_list(page.get("check_runs")))
        if total is None:
            pending("check-run payload has no consistent total_count; the list cannot be confirmed complete")
        elif len(runs) != total:
            pending(f"check list incomplete: {len(runs)} of {total} check runs; fetch every page")
    for run in runs:
        run = _dict(run)
        name = sanitize(run.get("name"), 60) or "unnamed check"
        url = safe_url(run.get("html_url"))
        run_head = _str(run.get("head_sha"))
        if run_head != head_sha:
            ci_known = False
            pending(f"check `{name}` belongs to commit {sanitize(run_head, 40)[:7] or 'unknown'}, not {head_sha[:7]}"
                    + ("; use the REST check-runs endpoint" if not run_head else ""))
            continue
        run_status, conclusion = sanitize(run.get("status"), 20), sanitize(run.get("conclusion"), 20)
        if run_status != "completed":
            unfinished.append(name)
            pending(f"check `{name}` is {run_status or 'not reported'}")
        elif conclusion in PASSING_CONCLUSIONS:
            passed.append(name)
        elif conclusion in TOLERATED_CONCLUSIONS and not strict:
            tolerated.append(name)
        elif conclusion in TOLERATED_CONCLUSIONS:
            failed.append(name)
            blocked(f"check `{name}` concluded {conclusion}, which --strict refuses")
        else:
            failed.append(name)
            blocked(f"check `{name}` concluded {conclusion or 'nothing'}" + (f" ({url})" if url else ""))
            if conclusion in RERUN_CONCLUSIONS:
                hints.append(f"`{name}` ended as {conclusion}, which can mean the job never ran; a maintainer "
                             "can re-run it if its log shows no test output (the sweep never re-runs jobs)")

    # Commit statuses (the older API that pre-commit.ci, codecov and others use).
    status = _dict(status)
    contexts = [_dict(context) for context in _list(status.get("statuses"))]
    status_sha = _str(status.get("sha"))
    if status_sha != head_sha:
        ci_known = False
        pending(f"combined status describes commit {sanitize(status_sha, 40)[:7] or 'unknown'}, not {head_sha[:7]}")
    status_total = _int(status.get("total_count"))
    status_valid = "statuses" in status and status_total is not None
    ci_known = ci_known and status_valid
    if not status_valid:
        pending("combined-status payload is not a GitHub status object; fetch it again")
    elif status_total != len(contexts):
        pending(f"status list incomplete: {len(contexts)} of {status_total} contexts")
    for context in contexts:
        name = sanitize(context.get("context"), 60) or "unnamed status"
        url = safe_url(context.get("target_url"))
        context_state = sanitize(context.get("state"), 20)
        if context_state == "success":
            passed.append(name)
        elif context_state == "pending":
            unfinished.append(name)
            pending(f"status `{name}` is pending")
        else:
            failed.append(name)
            blocked(f"status `{name}` is {context_state or 'unknown'}" + (f" ({url})" if url else ""))

    if ci_known and not passed and not unfinished:
        blocked("no check run or status finished with success for the head commit; unverified PRs are never merged")
    for required in require_checks:
        wanted = sanitize(required, 60)
        if ci_known and wanted not in passed and wanted not in failed and wanted not in unfinished:
            blocked(f"required check `{wanted}` did not finish with success")

    verdict = next((kind for kind in (REJECTED, BLOCKED, PENDING) if reasons[kind]), MERGE)
    return {
        "event": "decision",
        "repo": repo,
        "number": number,
        "url": f"https://github.com/{repo}/pull/{number}",
        "title": sanitize(pr.get("title")),
        "login": sanitize(login, 40),
        "author_id": user_id,
        "head_sha": head_sha,
        "verdict": verdict,
        "reasons": reasons.get(verdict, []),
        "hints": [hint for hint in dict.fromkeys(hints) if hint],
        "checks": {"passed": passed, "tolerated": tolerated, "failed": failed, "unfinished": unfinished},
        # True when being behind the base is the only problem and the sweep may fix it.
        "update_branch": bool(allow_branch_update and behind and verdict == BLOCKED
                              and len(reasons[BLOCKED]) == 1 and not reasons[PENDING]),
        "evaluated_at": iso(now),
    }


# --------------------------------------------------------------------------
# report
# --------------------------------------------------------------------------

def _pr_line(decision: dict, notes: list[str]) -> str:
    title = f" `{decision['title']}`" if decision.get("title") else ""
    return f"- [{decision['repo']}#{decision['number']}]({decision['url']}){title} — " + "; ".join(notes)


def render_report(events: list, *, version: str, now: datetime, dry_run: bool = False) -> str:
    decisions: dict[tuple, dict] = {}
    outcomes: dict[tuple, dict[str, str]] = {}
    selections: list[dict] = []
    repo_errors: list[dict] = []
    for event in events:
        event = _dict(event)
        key = (event.get("repo"), event.get("number"))
        kind = event.get("event")
        if kind == "decision":
            decisions[key] = event
        elif kind == "outcome" and event.get("result") == "repo-error":
            repo_errors.append(event)
        elif kind == "outcome":
            outcomes.setdefault(key, {})[_str(event.get("result"))] = _str(event.get("detail"))
        elif kind == "selection":
            selections.append(event)

    buckets: dict[str, list[str]] = {"Merged": [], "Blocked": [], "Pending": [], "Needs attention": []}
    for key, decision in sorted(decisions.items(), key=lambda item: (str(item[0][0]), item[0][1] or 0)):
        results = outcomes.get(key, {})
        verdict = decision.get("verdict")
        notes = [] if verdict == MERGE else list(decision.get("reasons", []))[:4]
        if "merged" in results:
            notes.append("squash-merged" + (f" as `{sanitize(results['merged'], 40)[:7]}`" if results["merged"] else ""))
        if "dry-run" in results:
            notes.append("would merge (dry run)")
        if "branch-updated" in results:
            notes.append("branch updated from the base; the next run re-evaluates it")
        for result, label in (("merge-failed", "merge failed"), ("assign-failed", "assignment failed"),
                              ("update-failed", "branch update failed")):
            if result in results:
                notes.append(f"{label}: {sanitize(results[result], 160)}")
        if "assigned" in results:
            notes.append(f"assigned to {sanitize(results['assigned'], 40)}")
        if verdict != MERGE:
            notes.extend(decision.get("hints", []))
        failures = {"merge-failed", "assign-failed", "update-failed"} & results.keys()
        if verdict == MERGE and "merged" in results:
            bucket = "Merged"
        elif verdict == REJECTED or failures:
            bucket = "Needs attention"
        elif verdict == BLOCKED and "branch-updated" not in results:
            bucket = "Blocked"
        else:
            bucket = "Pending"
        buckets[bucket].append(_pr_line(decision, notes or ["green, not merged yet"]))
    for key, results in sorted(outcomes.items(), key=lambda item: (str(item[0][0]), item[0][1] or 0)):
        if key not in decisions:
            recorded = ", ".join(f"`{sanitize(result, 20)}`" for result in sorted(results))
            buckets["Needs attention"].append(
                f"- {key[0]}#{key[1]}: {recorded} recorded without a gate decision; check the ledger")
    for selection in selections:
        for entry in _list(selection.get("suspicious")):
            entry = _dict(entry)
            number = entry.get("number")
            buckets["Needs attention"].append(
                f"- [{selection.get('repo')}#{number}](https://github.com/{selection.get('repo')}/pull/{number})"
                f" — {sanitize(entry.get('reason'), 200)}; not touched")
    for error in repo_errors:
        buckets["Needs attention"].append(f"- {error.get('repo')}: {sanitize(error.get('detail'), 200)}")

    lines = [
        "# Bot PR sweep",
        "",
        f"- Generated {iso(now)} by the bot-pr-sweep skill, version {version}",
        f"- Mode: {'dry run (nothing merged or assigned)' if dry_run else 'live'}",
        f"- Repositories swept: {len(selections)}; trusted-bot PRs evaluated: {len(decisions)}",
    ]
    for heading, entries in buckets.items():
        lines += ["", f"## {heading} ({len(entries)})", ""]
        lines += entries or ["- none"]
    lines += ["", "## Repositories", ""]
    for selection in sorted(selections, key=lambda item: str(item.get("repo"))):
        lines.append(f"- {selection.get('repo')}: {selection.get('open_prs')} open PRs, "
                     f"{len(_list(selection.get('bot_prs')))} from trusted bots, "
                     f"{len(_list(selection.get('suspicious')))} suspicious, "
                     f"{selection.get('other_bots')} from other bots")
    if not selections:
        lines.append("- none recorded")
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def append_event(ledger: str | None, event: dict) -> None:
    if ledger:
        with open(ledger, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, sort_keys=True) + "\n")


def cmd_init(_args: argparse.Namespace) -> int:
    print(tempfile.mkdtemp(prefix="bot-pr-sweep-"))
    return 0


def cmd_select(args: argparse.Namespace) -> int:
    pulls = pages(load_json(args.pulls))
    selected, suspicious, other_bots = select_bot_prs(pulls)
    for entry in selected:
        print(f"{entry['number']}\t{entry['head_sha']}\t{entry['login']}\t{entry['id']}")
    print(f"{args.repo}: {len(pulls)} open PRs, {len(selected)} from trusted bots, "
          f"{len(suspicious)} suspicious, {other_bots} from other bots", file=sys.stderr)
    append_event(args.ledger, {
        "event": "selection", "repo": args.repo, "open_prs": len(pulls),
        "bot_prs": [entry["number"] for entry in selected], "suspicious": suspicious,
        "other_bots": other_bots,
    })
    return 0


def cmd_gate(args: argparse.Namespace) -> int:
    decision = evaluate(
        load_json(args.pr), pages(load_json(args.commits)), pages(load_json(args.check_runs)),
        load_json(args.status),
        repo=args.repo, expected_head=args.head_sha,
        require_checks=tuple(args.require_check or ()),
        require_labels=tuple(args.require_label or ()),
        forbid_labels=tuple(args.forbid_label or ()),
        strict=args.strict, allow_branch_update=args.allow_branch_update,
        settle=timedelta(minutes=args.settle_minutes),
        now=parse_time(args.now) if args.now else None,
    )
    print(json.dumps(decision, indent=2, sort_keys=True))
    append_event(args.ledger, decision)
    return 0 if decision["verdict"] == MERGE else 1


def cmd_outcome(args: argparse.Namespace) -> int:
    append_event(args.ledger, {
        "event": "outcome", "repo": args.repo, "number": args.number,
        "result": args.result, "detail": args.detail or "", "recorded_at": iso(utc_now()),
    })
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    ledger = Path(args.ledger)
    if not ledger.is_file():
        raise GateInputError(f"ledger {args.ledger} does not exist; the run's records are missing")
    events = [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines() if line.strip()]
    skill_dir = Path(args.skill_dir) if args.skill_dir else Path(__file__).resolve().parent.parent
    print(render_report(events, version=skill_version(skill_dir),
                        now=parse_time(args.now) or utc_now(), dry_run=args.dry_run), end="")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    subparsers = parser.add_subparsers(dest="command", required=True)

    def common(sub: argparse.ArgumentParser, ledger_required: bool = False) -> None:
        sub.add_argument("--repo", required=True, type=repo_name, help="OWNER/REPO the JSON came from")
        sub.add_argument("--ledger", required=ledger_required, help="JSONL file the report is rendered from")

    subparsers.add_parser("init", help="create the run's working directory and print its path")

    select = subparsers.add_parser("select", help="pick the PRs opened by trusted bots")
    common(select)
    select.add_argument("pulls", help="JSON from GET /repos/O/R/pulls?state=open, every page (--paginate --slurp)")

    gate = subparsers.add_parser("gate", help="decide one pull request")
    common(gate)
    gate.add_argument("--pr", required=True, help="JSON from GET /repos/O/R/pulls/N")
    gate.add_argument("--commits", required=True, help="JSON from GET /repos/O/R/pulls/N/commits, every page")
    gate.add_argument("--check-runs", required=True, help="JSON from GET /repos/O/R/commits/SHA/check-runs, every page")
    gate.add_argument("--status", required=True, help="JSON from GET /repos/O/R/commits/SHA/status")
    gate.add_argument("--head-sha", required=True, type=commit_sha,
                      help="head SHA seen when listing; the PR must still be there")
    gate.add_argument("--require-check", action="append", metavar="NAME",
                      help="a check run or status context that must finish with success (repeatable)")
    gate.add_argument("--require-label", action="append", metavar="NAME", help="a label the PR must carry (repeatable)")
    gate.add_argument("--forbid-label", action="append", metavar="NAME", help="a label that blocks merging (repeatable)")
    gate.add_argument("--strict", action="store_true",
                      help="refuse skipped and neutral conclusions (by default they are tolerated, as GitHub does)")
    gate.add_argument("--allow-branch-update", action="store_true",
                      help="accept GitHub's own Update branch merge commit and flag behind PRs for it")
    gate.add_argument("--settle-minutes", type=int, default=int(DEFAULT_SETTLE.total_seconds() // 60),
                      help="minimum age of the head commit before trusting the check list (0 disables)")
    gate.add_argument("--now", help="ISO 8601 time to evaluate at (tests)")

    outcome = subparsers.add_parser("outcome", help="record what the sweep did")
    common(outcome, ledger_required=True)
    outcome.add_argument("--number", type=int, help="PR number; omit for a repository-level error")
    outcome.add_argument("--result", required=True, choices=sorted(RESULTS))
    outcome.add_argument("--detail", help="merge SHA, assignee login or error text")

    report = subparsers.add_parser("report", help="render the Markdown report")
    report.add_argument("--ledger", required=True)
    report.add_argument("--skill-dir", help="directory holding SKILL.md (default: this skill)")
    report.add_argument("--dry-run", action="store_true", help="label the run as a dry run")
    report.add_argument("--now", help="ISO 8601 time to stamp (tests)")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    handlers = {"init": cmd_init, "select": cmd_select, "gate": cmd_gate, "outcome": cmd_outcome,
                "report": cmd_report}
    try:
        return handlers[args.command](args)
    except (GateInputError, OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
