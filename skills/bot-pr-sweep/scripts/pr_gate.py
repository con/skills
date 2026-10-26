#!/usr/bin/env python3
"""Fail-closed gate for dependency-bot pull requests.

Standard library only. Every subcommand reads raw GitHub REST JSON that the
sweep saved to files (``gh api ... > file``) and never contacts GitHub itself,
so the decision logic is unit-testable and the agent running the sweep has no
reason to read pull-request titles, bodies, comments or check output.

Subcommands
-----------
select    PULLS.json...   pick the open PRs opened by a trusted bot, matched on
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
from datetime import datetime, timedelta, timezone
from pathlib import Path

# GitHub account IDs never change, unlike logins. Verify an ID before adding
# it: `gh api 'users/dependabot%5Bbot%5D' --jq .id`, or read `user.id` off a
# PR that bot opened in one of your repositories.
TRUSTED_BOTS = {
    49699333: "dependabot[bot]",
    66853113: "pre-commit-ci[bot]",
}
# Commits created through GitHub's API (every Dependabot commit) carry GitHub's
# own `web-flow` account as the committer.
WEB_FLOW_ID = 19864447

PASSING_CONCLUSIONS = frozenset({"success"})
# Accepted only when named with --allow-conclusion.
OPTIONAL_CONCLUSIONS = frozenset({"skipped", "neutral"})
MERGEABLE_OK = frozenset({"clean", "has_hooks"})
RESULTS = frozenset({
    "merged", "merge-failed", "assigned", "assign-failed", "dry-run", "repo-error",
})
DEFAULT_SETTLE = timedelta(minutes=10)

MERGE, PENDING, BLOCKED, REJECTED = "merge", "pending", "blocked", "rejected"

_URL = re.compile(r"^https://[A-Za-z0-9._~:/?#@!$&'*+,;=%-]+$")
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
    return text if _URL.match(text) else ""


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


def load_documents(path: Path) -> list:
    """Parse a file holding one JSON document or several concatenated ones.

    ``gh api --paginate`` prints one document per page, ``--slurp`` wraps them
    in an array, and a single page is a plain document. All three are accepted.
    """
    text = Path(path).read_text(encoding="utf-8")
    decoder = json.JSONDecoder()
    documents: list = []
    index = 0
    while True:
        while index < len(text) and text[index].isspace():
            index += 1
        if index >= len(text):
            return documents
        value, index = decoder.raw_decode(text, index)
        documents.append(value)


def flatten(documents: list) -> list:
    """Unnest pages so plain, concatenated and slurped output all become one list."""
    items: list = []
    for document in documents:
        if isinstance(document, list):
            for item in document:
                items.extend(item if isinstance(item, list) else [item])
        else:
            items.append(document)
    return items


def skill_version(skill_dir: Path) -> str:
    """The `version:` from this skill's SKILL.md frontmatter, for the report stamp."""
    try:
        text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    except OSError:
        return "unknown"
    match = _VERSION.search(text.split("\n---", 2)[0] if text.startswith("---") else "")
    return match.group(1) if match else "unknown"


def parse_bot(spec: str) -> tuple[int, str]:
    login, separator, raw_id = spec.rpartition("=")
    if not separator or not login or not raw_id.isdigit():
        raise argparse.ArgumentTypeError(f"expected LOGIN=NUMERIC_ID, got {spec!r}")
    return int(raw_id), login


def trusted_bots(extra: list[tuple[int, str]] | None) -> dict[int, str]:
    bots = dict(TRUSTED_BOTS)
    bots.update(extra or [])
    return bots


# --------------------------------------------------------------------------
# select
# --------------------------------------------------------------------------

def bot_name_hints(bots: dict[int, str]) -> set[str]:
    """Name fragments that make an untrusted login look like a trusted bot."""
    hints = set()
    for login in bots.values():
        base = login.split("[", 1)[0].lower()
        hints.add(base)
        if "-" in base:
            hints.add(base.rsplit("-", 1)[0])
    return hints


def select_bot_prs(pulls: list, bots: dict[int, str]) -> tuple[list, list, int]:
    """Split open PRs into trusted-bot PRs, suspicious look-alikes and other bots."""
    selected, suspicious, other_bots = [], [], 0
    hints = bot_name_hints(bots)
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
        if user_id in bots:
            if login == bots[user_id]:
                selected.append(entry)
            else:
                suspicious.append({**entry, "reason": (
                    f"account {user_id} is {bots[user_id]} but the login reads "
                    f"'{sanitize(login, 40)}'")})
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

def evaluate(pr: object, commits: list, check_pages: list, status: object, *,
             repo: str, bots: dict[int, str], expected_head: str = "",
             require_checks: tuple[str, ...] = (), allow_conclusions: tuple[str, ...] = (),
             settle: timedelta = DEFAULT_SETTLE, now: datetime | None = None) -> dict:
    """Decide one pull request. Returns the decision record (see SKILL.md)."""
    now = now or utc_now()
    pr = _dict(pr)
    user, head, base = _dict(pr.get("user")), _dict(pr.get("head")), _dict(pr.get("base"))
    number, user_id, login = _int(pr.get("number")), _int(user.get("id")), _str(user.get("login"))
    head_sha = _str(head.get("sha"))
    base_repo = _str(_dict(base.get("repo")).get("full_name"))
    head_repo = _str(_dict(head.get("repo")).get("full_name"))
    base_ref = _str(base.get("ref")) or "the base branch"
    if number is None or not head_sha:
        raise GateInputError("PR JSON has no number or head.sha; is it a pull request object?")
    if base_repo.lower() != repo.lower():
        raise GateInputError(f"PR JSON belongs to {base_repo or 'an unknown repository'}, not {repo}")

    reasons: dict[str, list[str]] = {REJECTED: [], BLOCKED: [], PENDING: []}
    hints: list[str] = []
    rejected, blocked, pending = (reasons[k].append for k in (REJECTED, BLOCKED, PENDING))

    # Author: the account ID decides, the login must agree with it.
    if user_id not in bots:
        rejected(f"author '{sanitize(login, 40)}' (account {user_id}) is not a trusted bot")
    elif login != bots[user_id]:
        rejected(f"account {user_id} is {bots[user_id]} but the login reads '{sanitize(login, 40)}'")
    elif user.get("type") != "Bot":
        rejected(f"account {user_id} is of type {sanitize(user.get('type'), 20) or 'unknown'}, not Bot")

    # Pull request state.
    state = _str(pr.get("state"))
    if state != "open":
        blocked(f"pull request is {state or 'in an unknown state'}")
    if pr.get("draft") is True:
        blocked("pull request is a draft")
    if head_repo.lower() != base_repo.lower():
        blocked(f"head branch lives in {head_repo or 'a deleted or foreign repository'}, not {base_repo}")
    if expected_head and expected_head != head_sha:
        pending(f"head moved from {expected_head[:7]} to {head_sha[:7]} since listing; run the gate again")
    mergeable, mergeable_state = pr.get("mergeable"), _str(pr.get("mergeable_state"))
    rebase_hint = ""
    if user_id == 49699333:
        rebase_hint = ("comment `@dependabot rebase` on the PR so the bot updates its own branch; "
                       "the sweep never pushes to it")
    if mergeable is None or mergeable_state in ("", "unknown"):
        pending("GitHub has not finished computing mergeability; retry shortly")
    elif mergeable is False or mergeable_state == "dirty":
        blocked(f"merge conflicts with {base_ref}")
        hints.append(rebase_hint)
    elif mergeable_state == "behind":
        blocked(f"branch is behind {base_ref} and the branch protection requires an up-to-date branch")
        hints.append(rebase_hint)
    elif mergeable_state == "blocked":
        blocked("branch protection is not satisfied (reviews, required checks or merge queue)")
    elif mergeable_state == "unstable":
        blocked("GitHub reports failing status checks (mergeable_state is unstable)")
    elif mergeable_state == "draft":
        if pr.get("draft") is not True:
            blocked("pull request is a draft")
    elif mergeable_state not in MERGEABLE_OK:
        blocked(f"unrecognized mergeable_state '{sanitize(mergeable_state, 20)}'")

    # Commits: every one must come from a trusted bot, and the list must be whole.
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
        for commit in commits:
            short = _str(commit.get("sha"))[:7] or "?"
            author_id = _int(_dict(commit.get("author")).get("id"))
            committer_id = _int(_dict(commit.get("committer")).get("id"))
            if author_id is None:
                blocked(f"commit {short} has no GitHub-linked author account (REST commits JSON needed)")
            elif author_id not in bots:
                blocked(f"commit {short} was authored by account {author_id}, not a trusted bot")
            if committer_id is None or (committer_id not in bots and committer_id != WEB_FLOW_ID):
                blocked(f"commit {short} was committed by account {committer_id}, neither a trusted bot nor GitHub")
            if len(_list(commit.get("parents"))) > 1:
                blocked(f"commit {short} is a merge commit, so someone updated the bot's branch")
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

    # Check runs: complete list, every one finished and passed.
    passed: list[str] = []
    failed: list[str] = []
    unfinished: list[str] = []
    runs: list = []
    pages = list(check_pages)
    checks_valid = bool(pages) and all(isinstance(page, dict) and "check_runs" in page for page in pages)
    if not checks_valid:
        pending("check-run payload is not a GitHub check-runs object; fetch it again")
    else:
        totals = {_int(page.get("total_count")) for page in pages}
        total = totals.pop() if len(totals) == 1 else None
        for page in pages:
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
        if run_head and run_head != head_sha:
            pending(f"check `{name}` belongs to commit {run_head[:7]}, not {head_sha[:7]}")
            continue
        run_status, conclusion = _str(run.get("status")), _str(run.get("conclusion"))
        if run_status != "completed":
            unfinished.append(name)
            pending(f"check `{name}` is {run_status or 'not reported'}")
        elif conclusion in PASSING_CONCLUSIONS or conclusion in allow_conclusions:
            passed.append(name)
        elif conclusion in OPTIONAL_CONCLUSIONS:
            failed.append(name)
            blocked(f"check `{name}` concluded {conclusion}; pass --allow-conclusion {conclusion} to accept that")
        else:
            failed.append(name)
            blocked(f"check `{name}` concluded {conclusion or 'nothing'}" + (f" ({url})" if url else ""))

    # Commit statuses (the older API that pre-commit.ci, codecov and others use).
    status = _dict(status)
    contexts = [_dict(context) for context in _list(status.get("statuses"))]
    status_sha = _str(status.get("sha"))
    if status_sha and status_sha != head_sha:
        pending(f"combined status describes commit {status_sha[:7]}, not {head_sha[:7]}")
    status_total = _int(status.get("total_count"))
    status_valid = "statuses" in status and status_total is not None
    if not status_valid:
        pending("combined-status payload is not a GitHub status object; fetch it again")
    elif status_total != len(contexts):
        pending(f"status list incomplete: {len(contexts)} of {status_total} contexts")
    for context in contexts:
        name = sanitize(context.get("context"), 60) or "unnamed status"
        url = safe_url(context.get("target_url"))
        context_state = _str(context.get("state"))
        if context_state == "success":
            passed.append(name)
        elif context_state == "pending":
            unfinished.append(name)
            pending(f"status `{name}` is pending")
        else:
            failed.append(name)
            blocked(f"status `{name}` is {context_state or 'unknown'}" + (f" ({url})" if url else ""))

    if checks_valid and status_valid and not runs and not contexts:
        blocked("no check runs or commit statuses exist for the head commit; unverified PRs are never merged")
    for required in require_checks:
        wanted = sanitize(required, 60)
        if wanted not in passed and wanted not in failed and wanted not in unfinished:
            blocked(f"required check `{wanted}` was not reported")

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
        "checks": {"passed": passed, "failed": failed, "unfinished": unfinished},
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
    outcomes: dict[tuple, list[dict]] = {}
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
            outcomes.setdefault(key, []).append(event)
        elif kind == "selection":
            selections.append(event)

    merged, blocked, pending, attention = [], [], [], []
    for key, decision in sorted(decisions.items(), key=lambda item: (str(item[0][0]), item[0][1] or 0)):
        results = {_str(outcome.get("result")): _str(outcome.get("detail")) for outcome in outcomes.get(key, [])}
        notes: list[str] = []
        if "merged" in results:
            notes.append("squash-merged" + (f" as `{results['merged'][:7]}`" if results["merged"] else ""))
        if "dry-run" in results:
            notes.append("would merge (dry run)")
        if "merge-failed" in results:
            notes.append(f"merge failed: {sanitize(results['merge-failed'], 160)}")
        if "assigned" in results:
            notes.append(f"assigned to {sanitize(results['assigned'], 40)}")
        if "assign-failed" in results:
            notes.append(f"assignment failed: {sanitize(results['assign-failed'], 160)}")
        verdict = decision.get("verdict")
        if verdict != MERGE:
            notes = list(decision.get("reasons", []))[:4] + notes
            notes.extend(decision.get("hints", []))
        line = _pr_line(decision, notes)
        if verdict == MERGE and "merged" in results:
            merged.append(line)
        elif verdict == MERGE and "merge-failed" not in results:
            pending.append(line if notes else _pr_line(decision, ["green, not merged yet"]))
        elif verdict in (MERGE, REJECTED) or "assign-failed" in results:
            attention.append(line)
        elif verdict == BLOCKED:
            blocked.append(line)
        else:
            pending.append(line)
    for selection in selections:
        for entry in _list(selection.get("suspicious")):
            entry = _dict(entry)
            number = entry.get("number")
            attention.append(
                f"- [{selection.get('repo')}#{number}](https://github.com/{selection.get('repo')}/pull/{number})"
                f" — {sanitize(entry.get('reason'), 200)}; not touched")
    for error in repo_errors:
        attention.append(f"- {error.get('repo')}: {sanitize(error.get('detail'), 200)}")

    lines = [
        "# Bot PR sweep",
        "",
        f"- Generated {iso(now)} by the bot-pr-sweep skill, version {version}",
        f"- Mode: {'dry run (nothing merged or assigned)' if dry_run else 'live'}",
        f"- Repositories swept: {len(selections)}; trusted-bot PRs evaluated: {len(decisions)}",
    ]
    for heading, entries in (("Merged", merged), ("Blocked", blocked), ("Pending", pending),
                             ("Needs attention", attention)):
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


def cmd_select(args: argparse.Namespace) -> int:
    pulls = flatten([doc for path in args.pulls for doc in load_documents(path)])
    selected, suspicious, other_bots = select_bot_prs(pulls, trusted_bots(args.bot))
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
    pr_documents = load_documents(args.pr)
    if len(pr_documents) != 1:
        raise GateInputError("--pr must hold exactly one pull request object")
    status_documents = load_documents(args.status)
    decision = evaluate(
        pr_documents[0],
        flatten([doc for path in args.commits for doc in load_documents(path)]),
        flatten([doc for path in args.check_runs for doc in load_documents(path)]),
        status_documents[0] if status_documents else {},
        repo=args.repo, bots=trusted_bots(args.bot), expected_head=args.head_sha or "",
        require_checks=tuple(args.require_check or ()),
        allow_conclusions=tuple(args.allow_conclusion or ()),
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
    events = load_documents(args.ledger) if Path(args.ledger).exists() else []
    skill_dir = Path(args.skill_dir) if args.skill_dir else Path(__file__).resolve().parent.parent
    print(render_report(events, version=skill_version(skill_dir),
                        now=parse_time(args.now) or utc_now(), dry_run=args.dry_run), end="")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    subparsers = parser.add_subparsers(dest="command", required=True)

    def common(sub: argparse.ArgumentParser, ledger_required: bool = False) -> None:
        sub.add_argument("--repo", required=True, help="OWNER/REPO the JSON came from")
        sub.add_argument("--ledger", required=ledger_required, help="JSONL file the report is rendered from")
        sub.add_argument("--bot", action="append", type=parse_bot, metavar="LOGIN=ID",
                         help="add or override a trusted bot (repeatable)")

    select = subparsers.add_parser("select", help="pick the PRs opened by trusted bots")
    common(select)
    select.add_argument("pulls", nargs="+", help="JSON from GET /repos/O/R/pulls?state=open (all pages)")

    gate = subparsers.add_parser("gate", help="decide one pull request")
    common(gate)
    gate.add_argument("--pr", required=True, help="JSON from GET /repos/O/R/pulls/N")
    gate.add_argument("--commits", required=True, nargs="+", help="JSON from GET /repos/O/R/pulls/N/commits")
    gate.add_argument("--check-runs", required=True, nargs="+", help="JSON from GET /repos/O/R/commits/SHA/check-runs")
    gate.add_argument("--status", required=True, help="JSON from GET /repos/O/R/commits/SHA/status")
    gate.add_argument("--head-sha", help="head SHA seen when listing; the PR must still be there")
    gate.add_argument("--require-check", action="append", metavar="NAME",
                      help="a check run or status context that must be present and passing (repeatable)")
    gate.add_argument("--allow-conclusion", action="append", choices=sorted(OPTIONAL_CONCLUSIONS),
                      help="also accept this check conclusion (repeatable)")
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
    handlers = {"select": cmd_select, "gate": cmd_gate, "outcome": cmd_outcome, "report": cmd_report}
    try:
        return handlers[args.command](args)
    except (GateInputError, OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
