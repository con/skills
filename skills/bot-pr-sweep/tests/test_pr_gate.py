"""Unit tests for pr_gate.py. Run with: python3 -m unittest discover -s tests -v"""

import argparse
import io
import json
import re
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timedelta, timezone
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR / "scripts"))

import pr_gate as gate  # noqa: E402

DEPENDABOT, PRE_COMMIT_CI, WEB_FLOW = 49699333, 66853113, 19864447
RENOVATE = 29139614
REPO = "acme/widgets"
HEAD = "a" * 40
OTHER = "b" * 40
NOW = datetime(2026, 10, 26, 12, 0, tzinfo=timezone.utc)


def user(login="dependabot[bot]", uid=DEPENDABOT, kind="Bot"):
    return {"login": login, "id": uid, "type": kind}


def pull(**overrides):
    pr = {
        "number": 7, "state": "open", "draft": False, "merged": False,
        "mergeable": True, "mergeable_state": "clean", "commits": 1,
        "title": "Bump requests from 2.31.0 to 2.32.0", "user": user(),
        "head": {"sha": HEAD, "ref": "dependabot/pip/requests-2.32.0", "repo": {"full_name": REPO}},
        "base": {"ref": "main", "repo": {"full_name": REPO}},
    }
    pr.update(overrides)
    return pr


def commit(sha=HEAD, author=DEPENDABOT, committer=WEB_FLOW, date="2026-10-26T11:00:00Z", parents=1):
    return {
        "sha": sha,
        "author": {"id": author, "login": "a"} if author is not None else None,
        "committer": {"id": committer, "login": "c"} if committer is not None else None,
        "parents": [{"sha": "p%d" % i} for i in range(parents)],
        "commit": {"author": {"name": "dependabot[bot]"}, "committer": {"date": date}},
    }


def run(name="tests", status="completed", conclusion="success", head=HEAD,
        url="https://github.com/acme/widgets/actions/runs/1/job/2"):
    return {"name": name, "status": status, "conclusion": conclusion, "head_sha": head, "html_url": url}


def runs(*items, total=None):
    return {"total_count": len(items) if total is None else total, "check_runs": list(items)}


def context(name="pre-commit.ci - pr", state="success", url="https://results.pre-commit.ci/run/1"):
    return {"context": name, "state": state, "target_url": url}


def status(*contexts, sha=HEAD, total=None):
    state = "success" if contexts and all(c["state"] == "success" for c in contexts) else "pending"
    return {"state": state, "sha": sha, "statuses": list(contexts),
            "total_count": len(contexts) if total is None else total}


def evaluate(**overrides):
    kwargs = dict(pr=pull(), commits=[commit()], check_pages=[runs(run())], status=status(),
                  repo=REPO, bots=gate.TRUSTED_BOTS, now=NOW)
    kwargs.update(overrides)
    return gate.evaluate(**kwargs)


class AuthorTests(unittest.TestCase):
    def test_green_dependabot_pr_merges(self):
        decision = evaluate()
        self.assertEqual(decision["verdict"], "merge")
        self.assertEqual(decision["reasons"], [])
        self.assertEqual(decision["head_sha"], HEAD)
        self.assertEqual(decision["url"], "https://github.com/acme/widgets/pull/7")

    def test_trusted_login_with_unknown_id_is_rejected(self):
        decision = evaluate(pr=pull(user=user(uid=424242)))
        self.assertEqual(decision["verdict"], "rejected")
        self.assertIn("not a trusted bot", decision["reasons"][0])

    def test_trusted_id_with_other_login_is_rejected(self):
        decision = evaluate(pr=pull(user=user(login="dependabot-helper[bot]")))
        self.assertEqual(decision["verdict"], "rejected")

    def test_trusted_id_of_user_type_is_rejected(self):
        self.assertEqual(evaluate(pr=pull(user=user(kind="User")))["verdict"], "rejected")

    def test_pre_commit_ci_commits_itself(self):
        decision = evaluate(pr=pull(user=user("pre-commit-ci[bot]", PRE_COMMIT_CI)),
                            commits=[commit(author=PRE_COMMIT_CI, committer=PRE_COMMIT_CI)])
        self.assertEqual(decision["verdict"], "merge")

    def test_extra_bot_can_be_trusted_explicitly(self):
        bots = gate.trusted_bots([(RENOVATE, "renovate[bot]")])
        pr = pull(user=user("renovate[bot]", RENOVATE))
        commits = [commit(author=RENOVATE, committer=RENOVATE)]
        self.assertEqual(evaluate(pr=pr, commits=commits)["verdict"], "rejected")
        self.assertEqual(evaluate(pr=pr, commits=commits, bots=bots)["verdict"], "merge")

    def test_rejected_outranks_everything_else(self):
        decision = evaluate(pr=pull(user=user(uid=1), draft=True), check_pages=[runs()])
        self.assertEqual(decision["verdict"], "rejected")


class SelectTests(unittest.TestCase):
    def test_selection_uses_the_account_id(self):
        pulls = [
            pull(),
            pull(number=8, user=user("dependabot[bot]", 1)),
            pull(number=9, user=user("someone", 55, "User")),
            pull(number=10, user=user("renovate[bot]", RENOVATE)),
            pull(number=11, user=user("pre-commit-ci[bot]", PRE_COMMIT_CI)),
            pull(number=12, user=user("my-dependabot-mirror", 77, "User")),
            pull(number=13, user=user("stranger", DEPENDABOT)),
        ]
        selected, suspicious, other_bots = gate.select_bot_prs(pulls, gate.TRUSTED_BOTS)
        self.assertEqual([entry["number"] for entry in selected], [7, 11])
        self.assertEqual(selected[0]["head_sha"], HEAD)
        self.assertEqual({entry["number"] for entry in suspicious}, {8, 12, 13})
        self.assertEqual(other_bots, 1)

    def test_malformed_entries_are_skipped(self):
        self.assertEqual(gate.select_bot_prs([None, "x", {"user": user()}], gate.TRUSTED_BOTS), ([], [], 0))

    def test_name_hints(self):
        self.assertEqual(gate.bot_name_hints(gate.TRUSTED_BOTS), {"dependabot", "pre-commit-ci", "pre-commit"})


class CheckRunTests(unittest.TestCase):
    def test_no_ci_at_all_blocks(self):
        decision = evaluate(check_pages=[runs()], status=status())
        self.assertEqual(decision["verdict"], "blocked")
        self.assertIn("no check runs or commit statuses", decision["reasons"][0])

    def test_truncated_list_is_pending(self):
        pages = [runs(*[run(name=f"c{i}") for i in range(100)], total=150)]
        decision = evaluate(check_pages=pages)
        self.assertEqual(decision["verdict"], "pending")
        self.assertIn("100 of 150", decision["reasons"][0])

    def test_inconsistent_totals_are_pending(self):
        pages = [runs(run(name="a"), total=2), runs(run(name="b"), total=3)]
        self.assertEqual(evaluate(check_pages=pages)["verdict"], "pending")

    def test_pages_are_merged(self):
        pages = [runs(run(name="a"), total=2), runs(run(name="b"), total=2)]
        decision = evaluate(check_pages=pages)
        self.assertEqual(decision["verdict"], "merge")
        self.assertEqual(decision["checks"]["passed"], ["a", "b"])

    def test_missing_total_count_is_pending(self):
        self.assertEqual(evaluate(check_pages=[{"check_runs": [run()]}])["verdict"], "pending")

    def test_error_or_empty_payload_is_pending(self):
        for pages in ([{"message": "Not Found"}], [], [None], ["oops"]):
            with self.subTest(pages=pages):
                self.assertEqual(evaluate(check_pages=pages)["verdict"], "pending")

    def test_unfinished_check_is_pending(self):
        for state in ("queued", "in_progress", "waiting", ""):
            with self.subTest(status=state):
                decision = evaluate(check_pages=[runs(run(status=state, conclusion=None))])
                self.assertEqual(decision["verdict"], "pending")
                self.assertEqual(decision["checks"]["unfinished"], ["tests"])

    def test_failed_check_blocks_with_link(self):
        decision = evaluate(check_pages=[runs(run(conclusion="failure"))])
        self.assertEqual(decision["verdict"], "blocked")
        self.assertIn("concluded failure", decision["reasons"][0])
        self.assertIn("https://github.com/acme/widgets/actions/runs/1/job/2", decision["reasons"][0])
        self.assertEqual(decision["checks"]["failed"], ["tests"])

    def test_other_bad_conclusions_block(self):
        for conclusion in ("cancelled", "timed_out", "action_required", "stale", "startup_failure", None):
            with self.subTest(conclusion=conclusion):
                self.assertEqual(evaluate(check_pages=[runs(run(conclusion=conclusion))])["verdict"], "blocked")

    def test_skipped_and_neutral_need_opt_in(self):
        for conclusion in ("skipped", "neutral"):
            with self.subTest(conclusion=conclusion):
                decision = evaluate(check_pages=[runs(run(conclusion=conclusion))])
                self.assertEqual(decision["verdict"], "blocked")
                self.assertIn(f"--allow-conclusion {conclusion}", decision["reasons"][0])
                allowed = evaluate(check_pages=[runs(run(conclusion=conclusion))], allow_conclusions=(conclusion,))
                self.assertEqual(allowed["verdict"], "merge")

    def test_check_for_another_commit_is_pending(self):
        self.assertEqual(evaluate(check_pages=[runs(run(head=OTHER))])["verdict"], "pending")

    def test_untrusted_check_name_is_sanitized(self):
        decision = evaluate(check_pages=[runs(run(name="tests `rm -rf`\n[click](https://x)"))])
        self.assertEqual(decision["checks"]["passed"], ["tests 'rm -rf' [click](https://x)"])

    def test_required_check_must_be_reported(self):
        decision = evaluate(require_checks=("lint",))
        self.assertEqual(decision["verdict"], "blocked")
        self.assertIn("required check `lint` was not reported", decision["reasons"][0])
        self.assertEqual(evaluate(require_checks=("lint",), check_pages=[runs(run(), run(name="lint"))])["verdict"], "merge")
        self.assertEqual(evaluate(require_checks=("lint",), status=status(context("lint")))["verdict"], "merge")

    def test_blocked_outranks_pending(self):
        pages = [runs(run(conclusion="failure"), run(name="b", status="queued", conclusion=None))]
        self.assertEqual(evaluate(check_pages=pages)["verdict"], "blocked")


class StatusTests(unittest.TestCase):
    def test_statuses_alone_count_as_ci(self):
        decision = evaluate(check_pages=[runs()], status=status(context()))
        self.assertEqual(decision["verdict"], "merge")
        self.assertEqual(decision["checks"]["passed"], ["pre-commit.ci - pr"])

    def test_failed_status_blocks_with_link(self):
        decision = evaluate(status=status(context(state="failure")))
        self.assertEqual(decision["verdict"], "blocked")
        self.assertIn("https://results.pre-commit.ci/run/1", decision["reasons"][0])

    def test_error_status_blocks(self):
        self.assertEqual(evaluate(status=status(context(state="error")))["verdict"], "blocked")

    def test_pending_status_is_pending(self):
        decision = evaluate(status=status(context(state="pending")))
        self.assertEqual(decision["verdict"], "pending")
        self.assertEqual(decision["checks"]["unfinished"], ["pre-commit.ci - pr"])

    def test_status_for_another_commit_is_pending(self):
        self.assertEqual(evaluate(status=status(sha=OTHER))["verdict"], "pending")

    def test_incomplete_status_list_is_pending(self):
        self.assertEqual(evaluate(status=status(context(), total=3))["verdict"], "pending")

    def test_missing_status_payload_is_pending(self):
        for payload in ({}, {"message": "Not Found"}, None, []):
            with self.subTest(payload=payload):
                self.assertEqual(evaluate(status=payload)["verdict"], "pending")

    def test_unsafe_target_url_is_dropped(self):
        decision = evaluate(status=status(context(state="failure", url="javascript:alert(1)")))
        self.assertNotIn("javascript", decision["reasons"][0])


class PullRequestStateTests(unittest.TestCase):
    def test_draft_blocks(self):
        self.assertEqual(evaluate(pr=pull(draft=True))["verdict"], "blocked")

    def test_closed_blocks(self):
        decision = evaluate(pr=pull(state="closed", merged=True))
        self.assertEqual(decision["verdict"], "blocked")
        self.assertIn("pull request is closed", decision["reasons"][0])

    def test_fork_or_deleted_head_blocks(self):
        for repo in ({"full_name": "forker/widgets"}, None):
            with self.subTest(repo=repo):
                pr = pull(head={"sha": HEAD, "ref": "x", "repo": repo})
                self.assertEqual(evaluate(pr=pr)["verdict"], "blocked")

    def test_moved_head_is_pending(self):
        decision = evaluate(expected_head=OTHER)
        self.assertEqual(decision["verdict"], "pending")
        self.assertIn("head moved", decision["reasons"][0])

    def test_unknown_mergeability_is_pending(self):
        self.assertEqual(evaluate(pr=pull(mergeable=None, mergeable_state="unknown"))["verdict"], "pending")
        self.assertEqual(evaluate(pr=pull(mergeable=None, mergeable_state=""))["verdict"], "pending")

    def test_behind_blocks_with_the_bots_rebase_command(self):
        decision = evaluate(pr=pull(mergeable_state="behind"))
        self.assertEqual(decision["verdict"], "blocked")
        self.assertIn("behind main", decision["reasons"][0])
        self.assertIn("@dependabot rebase", decision["hints"][0])

    def test_conflicts_block(self):
        decision = evaluate(pr=pull(mergeable=False, mergeable_state="dirty"))
        self.assertEqual(decision["verdict"], "blocked")
        self.assertIn("merge conflicts", decision["reasons"][0])

    def test_pre_commit_ci_gets_no_dependabot_hint(self):
        pr = pull(user=user("pre-commit-ci[bot]", PRE_COMMIT_CI), mergeable_state="behind")
        decision = evaluate(pr=pr, commits=[commit(author=PRE_COMMIT_CI, committer=PRE_COMMIT_CI)])
        self.assertEqual(decision["verdict"], "blocked")
        self.assertEqual(decision["hints"], [])

    def test_protection_and_unstable_block(self):
        for state, text in (("blocked", "branch protection"), ("unstable", "unstable"), ("weird", "unrecognized")):
            with self.subTest(state=state):
                decision = evaluate(pr=pull(mergeable_state=state))
                self.assertEqual(decision["verdict"], "blocked")
                self.assertIn(text, decision["reasons"][0])

    def test_has_hooks_is_mergeable(self):
        self.assertEqual(evaluate(pr=pull(mergeable_state="has_hooks"))["verdict"], "merge")

    def test_wrong_repository_is_an_input_error(self):
        with self.assertRaises(gate.GateInputError):
            evaluate(repo="acme/other")

    def test_non_pr_payload_is_an_input_error(self):
        for payload in ({}, [], None, {"number": 7}):
            with self.subTest(payload=payload), self.assertRaises(gate.GateInputError):
                evaluate(pr=payload)


class CommitTests(unittest.TestCase):
    def test_commit_by_someone_else_blocks(self):
        decision = evaluate(commits=[commit(author=12345)])
        self.assertEqual(decision["verdict"], "blocked")
        self.assertIn("authored by account 12345", decision["reasons"][0])

    def test_unlinked_author_blocks(self):
        decision = evaluate(commits=[commit(author=None)])
        self.assertEqual(decision["verdict"], "blocked")
        self.assertIn("no GitHub-linked author", decision["reasons"][0])

    def test_commit_shape_without_account_ids_blocks(self):
        mcp_shape = {"sha": HEAD, "html_url": "https://github.com/acme/widgets/commit/" + HEAD,
                     "author": {"name": "dependabot[bot]", "email": "x@y", "date": "2026-10-26T11:00:00Z"}}
        self.assertEqual(evaluate(commits=[mcp_shape])["verdict"], "blocked")

    def test_unknown_committer_blocks(self):
        for committer in (999, None):
            with self.subTest(committer=committer):
                self.assertEqual(evaluate(commits=[commit(committer=committer)])["verdict"], "blocked")

    def test_merge_commit_blocks(self):
        decision = evaluate(commits=[commit(parents=2)])
        self.assertEqual(decision["verdict"], "blocked")
        self.assertIn("merge commit", decision["reasons"][0])

    def test_incomplete_commit_list_is_pending(self):
        decision = evaluate(pr=pull(commits=2))
        self.assertEqual(decision["verdict"], "pending")
        self.assertIn("1 of 2", decision["reasons"][0])

    def test_commit_list_must_end_at_head(self):
        self.assertEqual(evaluate(commits=[commit(sha=OTHER)])["verdict"], "pending")

    def test_no_commits_is_pending(self):
        self.assertEqual(evaluate(commits=[])["verdict"], "pending")

    def test_fresh_head_waits_for_the_settle_time(self):
        fresh = [commit(date="2026-10-26T11:55:00Z")]
        decision = evaluate(commits=fresh)
        self.assertEqual(decision["verdict"], "pending")
        self.assertIn("5 min old", decision["reasons"][0])
        self.assertEqual(evaluate(commits=fresh, settle=timedelta(0))["verdict"], "merge")
        self.assertEqual(evaluate(commits=fresh, settle=timedelta(minutes=5))["verdict"], "merge")

    def test_missing_commit_date_is_pending(self):
        self.assertEqual(evaluate(commits=[commit(date=None)])["verdict"], "pending")


class HelperTests(unittest.TestCase):
    def test_sanitize(self):
        self.assertEqual(gate.sanitize("Bump `x`\n[evil](http://e)\x07 now"), "Bump 'x' [evil](http://e) now")
        self.assertEqual(gate.sanitize("x" * 120, 10), "x" * 9 + "…")
        self.assertEqual(gate.sanitize(None), "")
        self.assertEqual(gate.sanitize(["list"]), "")

    def test_safe_url(self):
        self.assertEqual(gate.safe_url("https://github.com/a/b/pull/1"), "https://github.com/a/b/pull/1")
        for bad in ("javascript:alert(1)", "http://insecure", "https://x.y/<s>", "https://x.y/a b", 7, None):
            with self.subTest(bad=bad):
                self.assertEqual(gate.safe_url(bad), "")

    def test_parse_time(self):
        self.assertEqual(gate.parse_time("2026-10-26T11:00:00Z"), datetime(2026, 10, 26, 11, tzinfo=timezone.utc))
        self.assertIsNone(gate.parse_time("yesterday"))
        self.assertIsNone(gate.parse_time(None))

    def test_parse_bot(self):
        self.assertEqual(gate.parse_bot("renovate[bot]=29139614"), (RENOVATE, "renovate[bot]"))
        for bad in ("renovate[bot]", "=1", "renovate[bot]=abc", "renovate[bot]=-1"):
            with self.subTest(bad=bad), self.assertRaises(argparse.ArgumentTypeError):
                gate.parse_bot(bad)

    def test_documents_in_every_gh_output_shape(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "pages.json"
            cases = {
                '[{"number": 1}, {"number": 2}]\n[{"number": 3}]': [1, 2, 3],
                '[[{"number": 1}], [{"number": 2}]]': [1, 2],
                '[{"number": 1}]': [1],
                '{"number": 1}\n{"number": 2}': [1, 2],
                '': [],
            }
            for text, numbers in cases.items():
                with self.subTest(text=text):
                    path.write_text(text, encoding="utf-8")
                    items = gate.flatten(gate.load_documents(path))
                    self.assertEqual([item["number"] for item in items], numbers)
            path.write_text("[not json", encoding="utf-8")
            with self.assertRaises(ValueError):
                gate.load_documents(path)

    def test_skill_version_comes_from_the_frontmatter(self):
        self.assertRegex(gate.skill_version(SKILL_DIR), r"^\d+\.\d+\.\d+$")
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(gate.skill_version(Path(directory)), "unknown")
            (Path(directory) / "SKILL.md").write_text("---\nname: x\n---\nversion: 9.9.9\n", encoding="utf-8")
            self.assertEqual(gate.skill_version(Path(directory)), "unknown")
            (Path(directory) / "SKILL.md").write_text("---\nname: x\nversion: 1.2.3\n---\nbody\n", encoding="utf-8")
            self.assertEqual(gate.skill_version(Path(directory)), "1.2.3")


class ReportTests(unittest.TestCase):
    def events(self):
        merged = evaluate()
        blocked = evaluate(pr=pull(number=8, title="Bump x\n[evil](https://e)"), check_pages=[runs(run(conclusion="failure"))])
        behind = evaluate(pr=pull(number=9, mergeable_state="behind"))
        pending = evaluate(pr=pull(number=10), check_pages=[runs(run(status="queued", conclusion=None))])
        rejected = evaluate(pr=pull(number=11, user=user(uid=5)))
        return [
            {"event": "selection", "repo": REPO, "open_prs": 9, "bot_prs": [7, 8, 9, 10], "other_bots": 1,
             "suspicious": [{"number": 12, "login": "dependabot[bot]", "id": 1, "reason": "account 1 is not trusted"}]},
            merged, blocked, behind, pending, rejected,
            {"event": "outcome", "repo": REPO, "number": 7, "result": "assigned", "detail": "maintainer"},
            {"event": "outcome", "repo": REPO, "number": 7, "result": "merged", "detail": "c" * 40},
            {"event": "outcome", "repo": REPO, "number": 8, "result": "assigned", "detail": "maintainer"},
            {"event": "outcome", "repo": REPO, "number": 9, "result": "assign-failed", "detail": "HTTP 422"},
            {"event": "outcome", "repo": "acme/other", "number": None, "result": "repo-error", "detail": "HTTP 403"},
        ]

    def test_report_groups_prs_and_stamps_the_version(self):
        text = gate.render_report(self.events(), version="0.1.0", now=NOW)
        self.assertIn("version 0.1.0", text)
        self.assertIn("Generated 2026-10-26T12:00:00Z", text)
        self.assertIn("- Mode: live", text)
        self.assertIn("## Merged (1)", text)
        self.assertIn("## Blocked (1)", text)
        self.assertIn("## Pending (1)", text)
        self.assertIn("## Needs attention (4)", text)
        self.assertIn("[acme/widgets#7](https://github.com/acme/widgets/pull/7)", text)
        self.assertIn("squash-merged as `ccccccc`; assigned to maintainer", text)
        self.assertIn("`Bump x [evil](https://e)`", text)
        self.assertNotIn("\n[evil]", text)
        self.assertIn("@dependabot rebase", text)
        self.assertIn("assignment failed: HTTP 422", text)
        self.assertIn("pull/12) — account 1 is not trusted; not touched", text)
        self.assertIn("- acme/other: HTTP 403", text)
        self.assertIn("- acme/widgets: 9 open PRs, 4 from trusted bots, 1 suspicious, 1 from other bots", text)

    def test_dry_run_and_failed_merge(self):
        events = [evaluate(), {"event": "outcome", "repo": REPO, "number": 7, "result": "dry-run"}]
        text = gate.render_report(events, version="0.1.0", now=NOW, dry_run=True)
        self.assertIn("- Mode: dry run", text)
        self.assertIn("## Pending (1)", text)
        self.assertIn("would merge (dry run)", text)
        events = [evaluate(), {"event": "outcome", "repo": REPO, "number": 7, "result": "merge-failed", "detail": "HTTP 409"}]
        text = gate.render_report(events, version="0.1.0", now=NOW)
        self.assertIn("## Needs attention (1)", text)
        self.assertIn("merge failed: HTTP 409", text)

    def test_empty_report(self):
        text = gate.render_report([], version="0.1.0", now=NOW)
        self.assertIn("## Merged (0)\n\n- none", text)
        self.assertIn("- none recorded", text)


class CliTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.ledger = self.root / "ledger.jsonl"
        self.files = {
            "pr": pull(), "commits": [commit()], "checks": runs(run()), "status": status(),
            "pulls": [pull(), pull(number=8, user=user("dependabot[bot]", 1))],
        }
        for name, payload in self.files.items():
            (self.root / f"{name}.json").write_text(json.dumps(payload), encoding="utf-8")

    def path(self, name):
        return str(self.root / f"{name}.json")

    def main(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = gate.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def gate_args(self, **extra):
        argv = ["gate", "--repo", REPO, "--ledger", str(self.ledger), "--pr", self.path("pr"),
                "--commits", self.path("commits"), "--check-runs", self.path("checks"),
                "--status", self.path("status"), "--now", "2026-10-26T12:00:00Z", "--head-sha", HEAD]
        for key, value in extra.items():
            argv += [key, value]
        return argv

    def test_gate_exit_codes(self):
        code, out, _ = self.main(*self.gate_args())
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["verdict"], "merge")
        self.assertEqual(json.loads(self.ledger.read_text().splitlines()[0])["event"], "decision")
        (self.root / "checks.json").write_text(json.dumps(runs(run(conclusion="failure"))), encoding="utf-8")
        code, out, _ = self.main(*self.gate_args())
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(out)["verdict"], "blocked")
        code, _, err = self.main(*self.gate_args(**{"--repo": "acme/other"}))
        self.assertEqual(code, 2)
        self.assertIn("not acme/other", err)
        (self.root / "pr.json").write_text("{broken", encoding="utf-8")
        self.assertEqual(self.main(*self.gate_args())[0], 2)
        (self.root / "pr.json").write_text("", encoding="utf-8")
        self.assertEqual(self.main(*self.gate_args())[0], 2)

    def test_gate_options(self):
        (self.root / "checks.json").write_text(json.dumps(runs(run(conclusion="skipped"))), encoding="utf-8")
        self.assertEqual(self.main(*self.gate_args())[0], 1)
        self.assertEqual(self.main(*self.gate_args(**{"--allow-conclusion": "skipped"}))[0], 0)
        self.assertEqual(self.main(*self.gate_args(**{"--require-check": "lint", "--allow-conclusion": "skipped"}))[0], 1)
        self.assertEqual(self.main(*self.gate_args(**{"--head-sha": OTHER}))[0], 1)
        (self.root / "checks.json").write_text(json.dumps(runs(run())), encoding="utf-8")
        (self.root / "pr.json").write_text(json.dumps(pull(user=user("renovate[bot]", RENOVATE))), encoding="utf-8")
        (self.root / "commits.json").write_text(json.dumps([commit(author=RENOVATE, committer=RENOVATE)]), encoding="utf-8")
        self.assertEqual(self.main(*self.gate_args())[0], 1)
        self.assertEqual(self.main(*self.gate_args(**{"--bot": f"renovate[bot]={RENOVATE}"}))[0], 0)

    def test_select_outcome_and_report(self):
        code, out, err = self.main("select", "--repo", REPO, "--ledger", str(self.ledger), self.path("pulls"))
        self.assertEqual(code, 0)
        self.assertEqual(out, f"7\t{HEAD}\tdependabot[bot]\t{DEPENDABOT}\n")
        self.assertIn("2 open PRs, 1 from trusted bots, 1 suspicious", err)
        self.assertEqual(self.main(*self.gate_args())[0], 0)
        code, _, _ = self.main("outcome", "--repo", REPO, "--ledger", str(self.ledger), "--number", "7",
                               "--result", "merged", "--detail", "d" * 40)
        self.assertEqual(code, 0)
        code, _, _ = self.main("outcome", "--repo", "acme/other", "--ledger", str(self.ledger),
                               "--result", "repo-error", "--detail", "HTTP 403")
        self.assertEqual(code, 0)
        code, out, _ = self.main("report", "--ledger", str(self.ledger), "--now", "2026-10-26T12:30:00Z")
        self.assertEqual(code, 0)
        self.assertRegex(out, r"version \d+\.\d+\.\d+")
        self.assertIn("## Merged (1)", out)
        self.assertIn("squash-merged as `ddddddd`", out)
        self.assertIn("pull/8) — login 'dependabot[bot]' resembles a trusted bot but account 1 is not trusted; not touched", out)
        self.assertIn("- acme/other: HTTP 403", out)
        code, out, _ = self.main("report", "--ledger", str(self.root / "missing.jsonl"), "--dry-run")
        self.assertEqual(code, 0)
        self.assertIn("dry run", out)

    def test_outcome_rejects_unknown_results(self):
        with self.assertRaises(SystemExit):
            self.main("outcome", "--repo", REPO, "--ledger", str(self.ledger), "--result", "whatever")


if __name__ == "__main__":
    unittest.main()
