"""Unit tests for pr_gate.py. Run with: python3 -m unittest discover -s tests -v"""

import io
import json
import os
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
RENOVATE, MAINTAINER = 29139614, 51133164
REPO = "acme/widgets"
HEAD = "a" * 40
OTHER = "b" * 40
BASE = "c" * 40
MERGE_SHA = "d" * 40
NOW = datetime(2026, 10, 26, 12, 0, tzinfo=timezone.utc)


def user(login="dependabot[bot]", uid=DEPENDABOT, kind="Bot"):
    return {"login": login, "id": uid, "type": kind}


def pull(**overrides):
    pr = {
        "number": 7, "state": "open", "draft": False, "merged": False,
        "mergeable": True, "mergeable_state": "clean", "commits": 1, "labels": [],
        "title": "Bump requests from 2.31.0 to 2.32.0", "user": user(),
        "head": {"sha": HEAD, "ref": "dependabot/pip/requests-2.32.0", "repo": {"full_name": REPO}},
        "base": {"ref": "main", "repo": {"full_name": REPO}},
    }
    pr.update(overrides)
    return pr


def commit(sha=HEAD, author=DEPENDABOT, committer=WEB_FLOW, date="2026-10-26T11:00:00Z", parents=1, verified=True):
    parent_shas = parents if isinstance(parents, list) else ["p%d" % i for i in range(parents)]
    entry = {
        "sha": sha,
        "author": {"id": author, "login": "a"} if author is not None else None,
        "committer": {"id": committer, "login": "c"} if committer is not None else None,
        "parents": [{"sha": parent} for parent in parent_shas],
        "commit": {"author": {"name": "dependabot[bot]"}, "committer": {"date": date}},
    }
    if verified is not None:
        entry["commit"]["verification"] = {"verified": verified, "reason": "valid" if verified else "unsigned"}
    return entry


def pre_commit_commit(**overrides):
    fields = dict(author=PRE_COMMIT_CI, committer=PRE_COMMIT_CI, verified=False)
    fields.update(overrides)
    return commit(**fields)


def update_merge(**overrides):
    """The merge commit GitHub's Update branch creates on top of the bot's commit."""
    fields = dict(sha=MERGE_SHA, author=MAINTAINER, committer=WEB_FLOW, parents=[HEAD, BASE],
                  date="2026-10-26T11:30:00Z", verified=True)
    fields.update(overrides)
    return commit(**fields)


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
                  repo=REPO, expected_head=HEAD, now=NOW)
    kwargs.update(overrides)
    return gate.evaluate(**kwargs)


class AuthorTests(unittest.TestCase):
    def test_green_dependabot_pr_merges(self):
        decision = evaluate()
        self.assertEqual(decision["verdict"], "merge")
        self.assertEqual(decision["reasons"], [])
        self.assertEqual(decision["head_sha"], HEAD)
        self.assertEqual(decision["url"], "https://github.com/acme/widgets/pull/7")
        self.assertFalse(decision["update_branch"])

    def test_trusted_login_with_unknown_id_is_rejected(self):
        decision = evaluate(pr=pull(user=user(uid=424242)))
        self.assertEqual(decision["verdict"], "rejected")
        self.assertIn("not a trusted bot", decision["reasons"][0])

    def test_trusted_id_with_other_login_is_rejected(self):
        decision = evaluate(pr=pull(user=user(login="dependabot-helper[bot]")))
        self.assertEqual(decision["verdict"], "rejected")
        # Report-only: a PR that would otherwise draw Dependabot's rebase hint gets no advice.
        behind = evaluate(pr=pull(user=user(login="dependabot-helper[bot]"), mergeable_state="behind"))
        self.assertEqual(behind["verdict"], "rejected")
        self.assertEqual(behind["hints"], [])

    def test_trusted_id_of_user_type_is_rejected(self):
        self.assertEqual(evaluate(pr=pull(user=user(kind="User")))["verdict"], "rejected")

    def test_pre_commit_ci_commits_itself_unsigned(self):
        decision = evaluate(pr=pull(user=user("pre-commit-ci[bot]", PRE_COMMIT_CI)), commits=[pre_commit_commit()])
        self.assertEqual(decision["verdict"], "merge")

    def test_commits_are_bound_to_the_pull_requests_author(self):
        spoofed = evaluate(commits=[pre_commit_commit()])
        self.assertEqual(spoofed["verdict"], "blocked")
        self.assertIn(f"authored by account {PRE_COMMIT_CI}, not by the pull request's author", spoofed["reasons"][0])
        foreign_committer = evaluate(commits=[commit(committer=PRE_COMMIT_CI)])
        self.assertEqual(foreign_committer["verdict"], "blocked")
        self.assertIn("neither the author nor GitHub", foreign_committer["reasons"][0])
        reverse = evaluate(pr=pull(user=user("pre-commit-ci[bot]", PRE_COMMIT_CI)), commits=[commit()])
        self.assertEqual(reverse["verdict"], "blocked")
        self.assertIn(f"authored by account {DEPENDABOT}, not by the pull request's author", reverse["reasons"][0])
        null_committer = evaluate(commits=[commit(committer=None)])
        self.assertEqual(null_committer["verdict"], "blocked")
        self.assertIn("committed by account unknown", null_committer["reasons"][0])

    def test_other_bots_are_not_trusted(self):
        pr = pull(user=user("renovate[bot]", RENOVATE))
        self.assertEqual(evaluate(pr=pr, commits=[commit(author=RENOVATE, committer=RENOVATE)])["verdict"], "rejected")

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
            pull(number=14, head={"sha": "nope", "ref": "x", "repo": {"full_name": REPO}}),
        ]
        selected, suspicious, other_bots = gate.select_bot_prs(pulls)
        self.assertEqual([entry["number"] for entry in selected], [7, 11])
        self.assertEqual(selected[0]["head_sha"], HEAD)
        self.assertEqual({entry["number"] for entry in suspicious}, {8, 12, 13, 14})
        self.assertEqual([entry["reason"] for entry in suspicious if entry["number"] == 14], ["head commit id is malformed"])
        self.assertEqual(other_bots, 1)

    def test_malformed_entries_are_skipped(self):
        self.assertEqual(gate.select_bot_prs([None, "x", {"user": user()}]), ([], [], 0))

    def test_name_hints(self):
        self.assertEqual(gate.bot_name_hints(), {"dependabot", "pre-commit-ci", "pre-commit"})


class CheckRunTests(unittest.TestCase):
    def test_no_ci_at_all_blocks(self):
        decision = evaluate(check_pages=[runs()], status=status())
        self.assertEqual(decision["verdict"], "blocked")
        self.assertIn("no check run or status finished with success", decision["reasons"][0])

    def test_truncated_list_is_pending(self):
        check_pages = [runs(*[run(name=f"c{i}") for i in range(100)], total=150)]
        decision = evaluate(check_pages=check_pages)
        self.assertEqual(decision["verdict"], "pending")
        self.assertIn("100 of 150", decision["reasons"][0])

    def test_inconsistent_totals_are_pending(self):
        check_pages = [runs(run(name="a"), total=2), runs(run(name="b"), total=3)]
        self.assertEqual(evaluate(check_pages=check_pages)["verdict"], "pending")

    def test_pages_are_merged(self):
        check_pages = [runs(run(name="a"), total=2), runs(run(name="b"), total=2)]
        decision = evaluate(check_pages=check_pages)
        self.assertEqual(decision["verdict"], "merge")
        self.assertEqual(decision["checks"]["passed"], ["a", "b"])

    def test_missing_total_count_is_pending(self):
        self.assertEqual(evaluate(check_pages=[{"check_runs": [run()]}])["verdict"], "pending")

    def test_error_or_empty_payload_is_pending(self):
        for check_pages in ([{"message": "Not Found"}], [], [None], ["oops"]):
            with self.subTest(pages=check_pages):
                self.assertEqual(evaluate(check_pages=check_pages)["verdict"], "pending")

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
        self.assertEqual(decision["hints"], [])

    def test_other_bad_conclusions_block(self):
        for conclusion in ("cancelled", "timed_out", "action_required", "stale", "startup_failure", None, "s\nuccess"):
            with self.subTest(conclusion=conclusion):
                self.assertEqual(evaluate(check_pages=[runs(run(conclusion=conclusion))])["verdict"], "blocked")

    def test_died_jobs_get_a_rerun_hint(self):
        decision = evaluate(check_pages=[runs(run(), run(name="deploy", conclusion="cancelled"))])
        self.assertEqual(decision["verdict"], "blocked")
        self.assertIn("`deploy` ended as cancelled", decision["hints"][0])
        self.assertIn("never re-runs", decision["hints"][0])

    def test_failing_version_guards_get_a_hint(self):
        for name in ("version-check", "Check Version", "bump_version", "Version Guard", "verify-version",
                     "ci_version_check"):
            with self.subTest(name=name):
                decision = evaluate(check_pages=[runs(run(), run(name=name, conclusion="failure"))])
                self.assertEqual(decision["verdict"], "blocked")
                self.assertIn(f"`{name}` looks like a version check", decision["hints"][0])
                self.assertIn("--require-label", decision["hints"][0])
        by_status = evaluate(status=status(context("Check Version", state="failure")))
        self.assertIn("`Check Version` looks like a version check", by_status["hints"][0])
        for name in ("test (python-version 3.9)", "versioning-docs", "diversion", "check-versioning"):
            with self.subTest(name=name):
                self.assertEqual(evaluate(check_pages=[runs(run(name=name, conclusion="failure"))])["hints"], [],
                                 "a version in a check's name is not a version check")
        self.assertEqual(evaluate(check_pages=[runs(run(name="version-check"))])["hints"], [])

    def test_skipped_and_neutral_are_tolerated_unless_strict(self):
        for conclusion in ("skipped", "neutral"):
            with self.subTest(conclusion=conclusion):
                decision = evaluate(check_pages=[runs(run(), run(name="chromatic", conclusion=conclusion))])
                self.assertEqual(decision["verdict"], "merge")
                self.assertEqual(decision["checks"]["tolerated"], ["chromatic"])
                strict = evaluate(check_pages=[runs(run(), run(name="chromatic", conclusion=conclusion))], strict=True)
                self.assertEqual(strict["verdict"], "blocked")
                self.assertIn("--strict refuses", strict["reasons"][0])

    def test_only_skipped_checks_do_not_count_as_ci(self):
        decision = evaluate(check_pages=[runs(run(conclusion="skipped"), run(name="b", conclusion="neutral"))])
        self.assertEqual(decision["verdict"], "blocked")
        self.assertIn("no check run or status finished with success", decision["reasons"][0])
        queued = evaluate(check_pages=[runs(run(conclusion="skipped"), run(name="b", status="queued", conclusion=None))])
        self.assertEqual(queued["verdict"], "pending")

    def test_check_for_another_or_unknown_commit_is_pending(self):
        self.assertEqual(evaluate(check_pages=[runs(run(head=OTHER))])["verdict"], "pending")
        unbound = evaluate(check_pages=[runs(run(head=None))])
        self.assertEqual(unbound["verdict"], "pending")
        self.assertIn("use the REST check-runs endpoint", unbound["reasons"][0])

    def test_untrusted_check_name_is_sanitized(self):
        decision = evaluate(check_pages=[runs(run(name="tests `rm -rf`\n[click](https://x)"))])
        self.assertEqual(decision["checks"]["passed"], ["tests 'rm -rf' [click] (https://x)"])

    def test_required_check_must_succeed(self):
        decision = evaluate(require_checks=("lint",))
        self.assertEqual(decision["verdict"], "blocked")
        self.assertIn("required check `lint` did not finish with success", decision["reasons"][0])
        self.assertEqual(evaluate(require_checks=("lint",), check_pages=[runs(run(), run(name="lint"))])["verdict"], "merge")
        self.assertEqual(evaluate(require_checks=("lint",), status=status(context("lint")))["verdict"], "merge")
        skipped = evaluate(require_checks=("lint",), check_pages=[runs(run(), run(name="lint", conclusion="skipped"))])
        self.assertEqual(skipped["verdict"], "blocked")

    def test_blocked_outranks_pending(self):
        check_pages = [runs(run(conclusion="failure"), run(name="b", status="queued", conclusion=None))]
        self.assertEqual(evaluate(check_pages=check_pages)["verdict"], "blocked")


ACTIONS = 15368  # the GitHub Actions app


def job(run_id, suite, name="label-check", conclusion="success", app=ACTIONS, head=HEAD, status="completed"):
    """A check run as GitHub Actions reports it: its id, app and check suite."""
    entry = run(name=name, conclusion=conclusion, head=head, status=status,
                url=f"https://github.com/acme/widgets/actions/runs/{suite}/job/{run_id}")
    entry.update({"id": run_id, "app": {"id": app, "slug": "github-actions"}, "check_suite": {"id": suite}})
    return entry


def workflow_run(suite, workflow=5, event="pull_request", head=HEAD):
    return {"id": suite * 10, "workflow_id": workflow, "event": event, "check_suite_id": suite, "head_sha": head}


def workflow_runs(*items, total=None):
    return [{"total_count": len(items) if total is None else total, "workflow_runs": list(items)}]


class SupersededRunTests(unittest.TestCase):
    """A workflow run again on the same commit (say, on a label change) replaces its earlier runs."""

    def test_later_run_of_a_workflow_replaces_its_earlier_failure(self):
        checks = [runs(job(1, 10, conclusion="failure"), job(2, 11), job(3, 12, name="tests"))]
        flows = workflow_runs(workflow_run(10), workflow_run(11), workflow_run(12, workflow=6))
        decision = evaluate(check_pages=checks, workflow_runs=flows)
        self.assertEqual(decision["verdict"], "merge")
        self.assertEqual(decision["checks"]["superseded"], ["label-check"])
        self.assertEqual(decision["checks"]["failed"], [])
        self.assertEqual(decision["checks"]["passed"], ["label-check", "tests"])
        # Without the workflow runs every run counts, as before.
        self.assertEqual(evaluate(check_pages=checks)["verdict"], "blocked")
        self.assertEqual(evaluate(check_pages=checks)["checks"]["superseded"], [])

    def test_later_failure_replaces_an_earlier_success(self):
        decision = evaluate(check_pages=[runs(job(1, 10), job(2, 11, conclusion="failure"))],
                            workflow_runs=workflow_runs(workflow_run(10), workflow_run(11)))
        self.assertEqual(decision["verdict"], "blocked")
        self.assertEqual(decision["checks"]["failed"], ["label-check"])

    def test_skipped_or_neutral_rerun_does_not_hide_a_failure(self):
        # A `labeled` re-run whose job an `if:` skips must not replace the failure before it.
        for conclusion in sorted(gate.TOLERATED_CONCLUSIONS):
            with self.subTest(conclusion):
                decision = evaluate(check_pages=[runs(job(1, 10, conclusion="failure"), job(2, 11, conclusion=conclusion),
                                                      job(3, 12, name="tests"))],
                                    workflow_runs=workflow_runs(workflow_run(10), workflow_run(11),
                                                                workflow_run(12, workflow=6)))
                self.assertEqual(decision["verdict"], "blocked")
                self.assertEqual(decision["checks"]["failed"], ["label-check"])
                # The skipped re-run is what drops out: the failure is the newest result that counts.
                self.assertEqual(decision["checks"]["superseded"], ["label-check"])
                self.assertEqual(decision["checks"]["tolerated"], [])
        only_skipped = evaluate(check_pages=[runs(job(1, 10, conclusion="skipped"), job(2, 11, conclusion="skipped"),
                                                  job(3, 12, name="tests"))],
                                workflow_runs=workflow_runs(workflow_run(10), workflow_run(11), workflow_run(12, workflow=6)))
        self.assertEqual(only_skipped["verdict"], "merge")
        self.assertEqual(only_skipped["checks"]["superseded"], [])

    def test_each_superseded_check_is_listed_once(self):
        stale = [job(run_id, 10 + run_id, conclusion="failure") for run_id in range(1, 6)]
        decision = evaluate(check_pages=[runs(*stale, job(6, 16))],
                            workflow_runs=workflow_runs(*(workflow_run(10 + n) for n in range(1, 7))))
        self.assertEqual(decision["verdict"], "merge")
        self.assertEqual(decision["checks"]["superseded"], ["label-check"])

    def test_later_unfinished_run_is_pending(self):
        decision = evaluate(check_pages=[runs(job(1, 10, conclusion="failure"), job(2, 11, status="in_progress",
                                                                                   conclusion=None))],
                            workflow_runs=workflow_runs(workflow_run(10), workflow_run(11)))
        self.assertEqual(decision["verdict"], "pending")
        self.assertEqual(decision["checks"]["unfinished"], ["label-check"])

    def test_same_job_name_in_another_workflow_or_event_still_counts(self):
        checks = [runs(job(1, 10, conclusion="failure"), job(2, 11))]
        for other in (workflow_run(11, workflow=6), workflow_run(11, event="push")):
            with self.subTest(other=other):
                decision = evaluate(check_pages=checks, workflow_runs=workflow_runs(workflow_run(10), other))
                self.assertEqual(decision["verdict"], "blocked")
                self.assertEqual(decision["checks"]["superseded"], [])

    def test_same_job_name_twice_in_one_workflow_run_both_count(self):
        decision = evaluate(check_pages=[runs(job(1, 10, conclusion="failure"), job(2, 10))],
                            workflow_runs=workflow_runs(workflow_run(10)))
        self.assertEqual(decision["verdict"], "blocked")

    def test_runs_the_payload_cannot_place_still_count(self):
        cases = {
            "unknown suite": [job(1, 99, conclusion="failure"), job(2, 11)],
            "other app": [job(1, 10, conclusion="failure", app=57789), job(2, 11)],
            "no id": [{**job(1, 10, conclusion="failure"), "id": None}, job(2, 11)],
        }
        flows = workflow_runs(workflow_run(10), workflow_run(11))
        for label, items in cases.items():
            with self.subTest(label):
                self.assertEqual(evaluate(check_pages=[runs(*items)], workflow_runs=flows)["verdict"], "blocked")
        foreign = workflow_runs(workflow_run(10, head=OTHER), workflow_run(11))
        self.assertEqual(evaluate(check_pages=[runs(job(1, 10, conclusion="failure"), job(2, 11))],
                                  workflow_runs=foreign)["verdict"], "blocked")

    def test_unusable_workflow_runs_replace_nothing(self):
        unusable = {"truncated": workflow_runs(workflow_run(10), workflow_run(11), total=3),
                    "no Actions access": [{"message": "Resource not accessible by integration"}], "empty": []}
        checks = [runs(job(1, 10, conclusion="failure"), job(2, 11))]
        for label, flows in unusable.items():
            with self.subTest(label):
                decision = evaluate(check_pages=checks, workflow_runs=flows)
                self.assertEqual(decision["verdict"], "blocked")
                self.assertEqual(decision["checks"]["superseded"], [])
                self.assertEqual(decision["checks"]["failed"], ["label-check"])
                self.assertTrue(any("every check run counts" in hint for hint in decision["hints"]))
        # The file is optional, so a bad one never holds a green PR (a token without actions:read gets a 403).
        green = [runs(job(1, 10), job(2, 11))]
        for label, flows in unusable.items():
            with self.subTest(f"green, {label}"):
                decision = evaluate(check_pages=green, workflow_runs=flows)
                self.assertEqual(decision["verdict"], "merge")
                self.assertTrue(any("every check run counts" in hint for hint in decision["hints"]))


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

    def test_status_without_sha_is_pending(self):
        payload = status()
        del payload["sha"]
        decision = evaluate(status=payload)
        self.assertEqual(decision["verdict"], "pending")
        self.assertIn("combined status describes commit unknown", decision["reasons"][0])

    def test_incomplete_status_list_is_pending(self):
        self.assertEqual(evaluate(status=status(context(), total=3))["verdict"], "pending")

    def test_missing_status_payload_is_pending(self):
        for payload in ({}, {"message": "Not Found"}, None, []):
            with self.subTest(payload=payload):
                self.assertEqual(evaluate(status=payload)["verdict"], "pending")

    def test_unsafe_target_url_is_dropped(self):
        for url in ("javascript:alert(1)", "https://evil.example/x\n", "https://x.y/<s>"):
            with self.subTest(url=url):
                decision = evaluate(status=status(context(state="failure", url=url)))
                self.assertEqual(decision["reasons"][0], "status `pre-commit.ci - pr` is failure")


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

    def test_labels_match_case_insensitively(self):
        labelled = pull(labels=[{"name": "Internal"}, {"name": "do-not-merge"}])
        self.assertEqual(evaluate(pr=labelled, require_labels=("internal",))["verdict"], "merge")
        missing = evaluate(require_labels=("internal",))
        self.assertEqual(missing["verdict"], "blocked")
        self.assertIn("required label `internal` is missing", missing["reasons"][0])
        forbidden = evaluate(pr=labelled, forbid_labels=("Do-Not-Merge",))
        self.assertEqual(forbidden["verdict"], "blocked")
        self.assertIn("label `Do-Not-Merge` excludes", forbidden["reasons"][0])
        self.assertEqual(evaluate(forbid_labels=("major",))["verdict"], "merge")

    def test_label_options_need_a_well_formed_labels_list(self):
        for labels in (None, "internal", [{"name": 5}], ["internal"], [{"id": 1}]):
            with self.subTest(labels=labels):
                decision = evaluate(pr=pull(labels=labels), forbid_labels=("major",))
                self.assertEqual(decision["verdict"], "pending")
                self.assertIn("labels payload is missing or malformed", decision["reasons"][0])
                self.assertEqual(evaluate(pr=pull(labels=labels), require_labels=("internal",))["verdict"], "pending")
        self.assertEqual(evaluate(pr=pull(labels=None))["verdict"], "pending")

    def test_major_label_is_stripped_before_any_merge(self):
        for name in ("major", "Major", "MAJOR", " major", "major\n"):
            with self.subTest(name=name):
                decision = evaluate(pr=pull(labels=[{"name": "dependencies"}, {"name": name}]))
                self.assertEqual(decision["verdict"], "blocked")
                self.assertEqual(decision["strip_labels"], ["major"], "the canonical name, never the payload's spelling")
                self.assertIn("carries the `major` label", decision["reasons"][0])
                self.assertIn("major release of the application", decision["reasons"][0])
                self.assertIn("remove it unless a person put it there on purpose", decision["hints"][0])
        twice = evaluate(pr=pull(labels=[{"name": "Major"}, {"name": "major "}]))
        self.assertEqual(twice["strip_labels"], ["major"])
        self.assertEqual(len(twice["reasons"]), 1)
        self.assertEqual(len(twice["hints"]), 1)
        clean = evaluate(pr=pull(labels=[{"name": "dependencies"}, {"name": "majority"}]))
        self.assertEqual(clean["verdict"], "merge")
        self.assertEqual(clean["strip_labels"], [])
        behind = evaluate(pr=pull(labels=[{"name": "major"}], mergeable_state="behind"), allow_branch_update=True)
        self.assertFalse(behind["update_branch"])
        rejected = evaluate(pr=pull(labels=[{"name": "Major"}], user=user(uid=1)))
        self.assertEqual(rejected["verdict"], "rejected")
        self.assertEqual(rejected["strip_labels"], [], "a PR the sweep must not touch never gets a label write")
        self.assertEqual(rejected["hints"], [], "and no advice to touch it either")
        missing = evaluate(pr=pull(labels=None))
        self.assertEqual(missing["verdict"], "pending")
        self.assertEqual((missing["strip_labels"], missing["hints"]), ([], []))

    def test_payload_strings_are_sanitized_in_reasons(self):
        pr = pull(state="clo\nsed `x`", mergeable_state="behind", base={"ref": "ma<in>\n`", "repo": {"full_name": REPO}})
        decision = evaluate(pr=pr)
        self.assertEqual(decision["verdict"], "blocked")
        self.assertIn("pull request is clo sed 'x'", decision["reasons"][0])
        self.assertIn("behind `ma‹in> '`", decision["reasons"][1])
        self.assertNotIn("\n", json.dumps(decision))

    def test_unknown_mergeability_is_pending(self):
        self.assertEqual(evaluate(pr=pull(mergeable=None, mergeable_state="unknown"))["verdict"], "pending")
        self.assertEqual(evaluate(pr=pull(mergeable=None, mergeable_state=""))["verdict"], "pending")

    def test_behind_blocks_with_the_bots_rebase_command(self):
        decision = evaluate(pr=pull(mergeable_state="behind"))
        self.assertEqual(decision["verdict"], "blocked")
        self.assertIn("behind `main`", decision["reasons"][0])
        self.assertIn("@dependabot rebase", decision["hints"][0])
        self.assertFalse(decision["update_branch"])

    def test_behind_is_flagged_for_update_only_when_it_is_the_sole_problem(self):
        decision = evaluate(pr=pull(mergeable_state="behind"), allow_branch_update=True)
        self.assertEqual(decision["verdict"], "blocked")
        self.assertTrue(decision["update_branch"])
        self.assertEqual(decision["hints"], [])
        failing = evaluate(pr=pull(mergeable_state="behind"), allow_branch_update=True,
                           check_pages=[runs(run(conclusion="failure"))])
        self.assertFalse(failing["update_branch"])
        queued = evaluate(pr=pull(mergeable_state="behind"), allow_branch_update=True,
                          check_pages=[runs(run(status="queued", conclusion=None))])
        self.assertFalse(queued["update_branch"])
        rejected = evaluate(pr=pull(mergeable_state="behind", user=user(uid=1)), allow_branch_update=True)
        self.assertFalse(rejected["update_branch"])

    def test_conflicts_block(self):
        decision = evaluate(pr=pull(mergeable=False, mergeable_state="dirty"))
        self.assertEqual(decision["verdict"], "blocked")
        self.assertIn("merge conflicts", decision["reasons"][0])

    def test_pre_commit_ci_gets_no_dependabot_hint(self):
        pr = pull(user=user("pre-commit-ci[bot]", PRE_COMMIT_CI), mergeable_state="behind")
        decision = evaluate(pr=pr, commits=[pre_commit_commit()])
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
        bad_sha = {"number": 7, "head": {"sha": "nope"}, "base": {"repo": {"full_name": REPO}}}
        for payload in ({}, [], None, {"number": 7}, bad_sha):
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

    def test_non_object_commit_entries_fail_closed(self):
        for entry in ("not a commit", None, 7, ["nested"]):
            with self.subTest(entry=entry):
                decision = evaluate(commits=[entry])
                self.assertEqual(decision["verdict"], "blocked")
                self.assertIn("no GitHub-linked author", " | ".join(decision["reasons"]))

    def test_dependabot_commit_must_carry_githubs_signature(self):
        for verified in (False, None):
            with self.subTest(verified=verified):
                decision = evaluate(commits=[commit(verified=verified)])
                self.assertEqual(decision["verdict"], "blocked")
                self.assertIn("claims to be by dependabot[bot] but carries no verified GitHub signature",
                              decision["reasons"][0])

    def test_unknown_committer_blocks(self):
        for committer in (999, None):
            with self.subTest(committer=committer):
                self.assertEqual(evaluate(commits=[commit(committer=committer)])["verdict"], "blocked")

    def test_merge_commit_blocks_by_default(self):
        decision = evaluate(pr=pull(commits=2, head={"sha": MERGE_SHA, "ref": "x", "repo": {"full_name": REPO}}),
                            expected_head=MERGE_SHA, commits=[commit(), update_merge()],
                            check_pages=[runs(run(head=MERGE_SHA))], status=status(sha=MERGE_SHA))
        self.assertEqual(decision["verdict"], "blocked")
        self.assertIn("merge commit, so someone updated", decision["reasons"][0])

    def updated(self, merge, **overrides):
        kwargs = dict(pr=pull(commits=2, head={"sha": MERGE_SHA, "ref": "x", "repo": {"full_name": REPO}}),
                      expected_head=MERGE_SHA, commits=[commit(), merge], check_pages=[runs(run(head=MERGE_SHA))],
                      status=status(sha=MERGE_SHA), allow_branch_update=True)
        kwargs.update(overrides)
        return evaluate(**kwargs)

    def test_githubs_update_branch_merge_is_accepted_when_allowed(self):
        decision = self.updated(update_merge())
        self.assertEqual(decision["verdict"], "merge")
        self.assertEqual(decision["reasons"], [])

    def test_update_merge_must_be_githubs_own(self):
        cases = {
            "committer": (update_merge(committer=MAINTAINER), "not committed by GitHub"),
            "unsigned": (update_merge(verified=False), "no valid GitHub signature"),
            "no verification": (update_merge(verified=None), "no valid GitHub signature"),
            "parents": (update_merge(parents=[HEAD, BASE, OTHER]), "merges 3 parents"),
            "chain": (update_merge(parents=[OTHER, BASE]), "does not continue the bot's previous commit"),
        }
        for name, (merge, text) in cases.items():
            with self.subTest(case=name):
                decision = self.updated(merge)
                self.assertEqual(decision["verdict"], "blocked")
                self.assertTrue(any(text in reason for reason in decision["reasons"]), decision["reasons"])

    def test_update_merge_needs_a_previous_commit(self):
        # Missing SHAs must not let an empty "previous" match empty parent SHAs.
        merge = update_merge(parents=["", ""])
        decision = self.updated(merge, pr=pull(commits=1, head={"sha": MERGE_SHA, "ref": "x",
                                                                  "repo": {"full_name": REPO}}), commits=[merge])
        self.assertEqual(decision["verdict"], "blocked")
        self.assertTrue(any("does not continue the bot's previous commit" in reason
                            for reason in decision["reasons"]), decision["reasons"])

    def test_commits_after_an_update_merge_still_need_a_bot_author(self):
        human = commit(sha=OTHER, author=MAINTAINER, committer=MAINTAINER, parents=[MERGE_SHA], date="2026-10-26T11:40:00Z")
        decision = self.updated(update_merge(), pr=pull(commits=3, head={"sha": OTHER, "ref": "x", "repo": {"full_name": REPO}}),
                                expected_head=OTHER, commits=[commit(), update_merge(), human],
                                check_pages=[runs(run(head=OTHER))], status=status(sha=OTHER))
        self.assertEqual(decision["verdict"], "blocked")
        self.assertIn(f"authored by account {MAINTAINER}", decision["reasons"][0])

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


def autofix(**overrides):
    """pre-commit.ci's autofix commit, pushed on top of the bot's own commit."""
    fields = dict(sha=OTHER, parents=[HEAD], date="2026-10-26T11:01:00Z")
    fields.update(overrides)
    return pre_commit_commit(**fields)


class MixedBotTests(unittest.TestCase):
    """--allow-mixed-bots: a later commit by another trusted bot, as pre-commit.ci's autofix on a Dependabot PR."""

    def autofixed(self, *later, **overrides):
        later = later or (autofix(),)
        head = later[-1]["sha"]
        fields = dict(pr=pull(commits=1 + len(later), head={"sha": head, "repo": {"full_name": REPO}}),
                      commits=[commit(), *later], check_pages=[runs(run(head=head))], status=status(sha=head),
                      expected_head=head)
        fields.update(overrides)
        return evaluate(**fields)

    def test_off_by_default_with_one_hint_for_the_maintainer(self):
        decision = self.autofixed(autofix(), autofix(sha="e" * 40, parents=[OTHER], date="2026-10-26T11:02:00Z"))
        self.assertEqual(decision["verdict"], "blocked")
        self.assertIn("authored by account 66853113, not by the pull request's author", " | ".join(decision["reasons"]))
        hints = [hint for hint in decision["hints"] if "--allow-mixed-bots" in hint]
        self.assertEqual(len(hints), 1, decision["hints"])
        self.assertIn("by pre-commit-ci[bot], the other trusted bot", hints[0])
        self.assertIn("the maintainer can opt in", hints[0])

    def test_no_hint_on_a_rejected_pr(self):
        person = pull(commits=2, user=user("someone", MAINTAINER, "User"),
                      head={"sha": OTHER, "repo": {"full_name": REPO}})
        decision = self.autofixed(pr=person, commits=[commit(author=MAINTAINER, committer=MAINTAINER), autofix()])
        self.assertEqual(decision["verdict"], "rejected")
        self.assertFalse(any("--allow-mixed-bots" in hint for hint in decision["hints"]))

    def test_with_githubs_update_branch_merge_in_either_order(self):
        after = update_merge(parents=[OTHER, BASE])
        before = update_merge()
        for name, later in (("autofix, then Update branch", (autofix(), after)),
                            ("Update branch, then autofix", (before, autofix(sha="e" * 40, parents=[MERGE_SHA],
                                                                             date="2026-10-26T11:40:00Z")))):
            with self.subTest(name):
                decision = self.autofixed(*later, allow_mixed_bots=True, allow_branch_update=True)
                self.assertEqual(decision["verdict"], "merge", decision["reasons"])

    def test_an_edited_dependabot_branch_gets_the_recreate_hint(self):
        behind = pull(commits=2, mergeable_state="behind", head={"sha": OTHER, "repo": {"full_name": REPO}})
        edited = self.autofixed(pr=behind, allow_mixed_bots=True)
        self.assertTrue(any("`@dependabot rebase` on the PR, or `@dependabot recreate` if Dependabot refuses" in hint
                            for hint in edited["hints"]), edited["hints"])
        # Untouched, whether GitHub (web-flow) or Dependabot itself is the committer.
        for plain in (evaluate(pr=pull(mergeable_state="behind")),
                      evaluate(pr=pull(mergeable_state="behind"), commits=[commit(committer=DEPENDABOT)])):
            self.assertTrue(any("`@dependabot rebase`" in hint for hint in plain["hints"]))
            self.assertFalse(any("`@dependabot recreate`" in hint for hint in plain["hints"]))

    def test_recreate_hint_covers_update_merges_no_ci_rebases_and_only_dependabot(self):
        at = dict(check_pages=[runs()], status=status(sha=OTHER), expected_head=OTHER)
        head = {"sha": OTHER, "repo": {"full_name": REPO}}
        no_ci = evaluate(pr=pull(commits=2, head=head), commits=[commit(), autofix()], allow_mixed_bots=True, **at)
        self.assertTrue(any("`@dependabot recreate`" in hint for hint in no_ci["hints"]), no_ci["hints"])
        merged = evaluate(pr=pull(commits=2, mergeable=False, mergeable_state="dirty",
                                  head={"sha": MERGE_SHA, "repo": {"full_name": REPO}}),
                          commits=[commit(), update_merge()], check_pages=[runs(run(head=MERGE_SHA))],
                          status=status(sha=MERGE_SHA), expected_head=MERGE_SHA, allow_branch_update=True)
        self.assertTrue(any("`@dependabot recreate`" in hint for hint in merged["hints"]), merged["hints"])
        # GitHub's "Update with rebase" keeps Dependabot as the author and changes only the committer.
        rebased = evaluate(pr=pull(mergeable=False, mergeable_state="dirty"), commits=[commit(committer=MAINTAINER)])
        self.assertTrue(any("`@dependabot recreate`" in hint for hint in rebased["hints"]), rebased["hints"])
        theirs = evaluate(pr=pull(commits=2, head=head, user=user("pre-commit-ci[bot]", PRE_COMMIT_CI)),
                          commits=[pre_commit_commit(), commit(sha=OTHER, parents=[HEAD])], allow_mixed_bots=True, **at)
        self.assertFalse(any("@dependabot" in hint for hint in theirs["hints"]), theirs["hints"])

    def test_pre_commit_ci_autofix_on_a_dependabot_pr_merges(self):
        decision = self.autofixed(allow_mixed_bots=True)
        self.assertEqual(decision["verdict"], "merge", decision["reasons"])
        self.assertEqual(decision["hints"], [])

    def test_the_first_commit_must_be_the_authors(self):
        decision = evaluate(commits=[pre_commit_commit()], allow_mixed_bots=True)
        self.assertEqual(decision["verdict"], "blocked")
        self.assertIn("not by the pull request's author", decision["reasons"][0])
        self.assertFalse(any("--allow-mixed-bots" in hint for hint in decision["hints"]))

    def test_people_and_other_bots_still_block(self):
        for name, uid in (("a person", MAINTAINER), ("an untrusted bot", RENOVATE)):
            with self.subTest(name):
                decision = self.autofixed(commit(sha=OTHER, author=uid, committer=uid, parents=[HEAD], verified=None),
                                          allow_mixed_bots=True)
                self.assertEqual(decision["verdict"], "blocked")
                self.assertIn(f"authored by account {uid}", " | ".join(decision["reasons"]))
                self.assertFalse(any("--allow-mixed-bots" in hint for hint in decision["hints"]))

    def test_a_later_commit_committed_by_someone_else_blocks(self):
        # Its own author or GitHub, as for every commit; not even the bot that opened the PR.
        for committer in (MAINTAINER, DEPENDABOT):
            with self.subTest(committer=committer):
                decision = self.autofixed(autofix(committer=committer), allow_mixed_bots=True)
                self.assertEqual(decision["verdict"], "blocked")
                self.assertIn(f"committed by account {committer}, neither the author nor GitHub",
                              " | ".join(decision["reasons"]))

    def test_the_signature_rule_follows_the_commit_author(self):
        # On a pre-commit.ci PR, a later commit claiming to be Dependabot's still needs GitHub's signature.
        pr = pull(user=user("pre-commit-ci[bot]", PRE_COMMIT_CI), commits=2,
                  head={"sha": OTHER, "repo": {"full_name": REPO}})
        for verified, verdict in ((False, "blocked"), (True, "merge")):
            with self.subTest(verified=verified):
                claimed = commit(sha=OTHER, parents=[HEAD], verified=verified)
                decision = evaluate(pr=pr, commits=[pre_commit_commit(), claimed], check_pages=[runs(run(head=OTHER))],
                                    status=status(sha=OTHER), expected_head=OTHER, allow_mixed_bots=True)
                self.assertEqual(decision["verdict"], verdict, decision["reasons"])
                if not verified:
                    self.assertIn("claims to be by dependabot[bot] but carries no verified GitHub signature",
                                  " | ".join(decision["reasons"]))


class HelperTests(unittest.TestCase):
    def test_sanitize(self):
        self.assertEqual(gate.sanitize("Bump `x`\n[evil](http://e)\x07 now"), "Bump 'x' [evil] (http://e) now")
        self.assertEqual(gate.sanitize("x" * 120, 10), "x" * 9 + "…")
        self.assertEqual(gate.sanitize(None), "")
        self.assertEqual(gate.sanitize(["list"]), "")

    def test_safe_url(self):
        self.assertEqual(gate.safe_url("https://github.com/a/b/pull/1"), "https://github.com/a/b/pull/1")
        for bad in ("javascript:alert(1)", "http://insecure", "https://x.y/<s>", "https://x.y/a b",
                    "https://evil.example/x\n", "\nhttps://evil.example/x", 7, None):
            with self.subTest(bad=bad):
                self.assertEqual(gate.safe_url(bad), "")

    def test_parse_time(self):
        self.assertEqual(gate.parse_time("2026-10-26T11:00:00Z"), datetime(2026, 10, 26, 11, tzinfo=timezone.utc))
        self.assertIsNone(gate.parse_time("yesterday"))
        self.assertIsNone(gate.parse_time(None))

    def test_pages_unnests_slurped_output(self):
        self.assertEqual(gate.pages([[{"n": 1}], [{"n": 2}, {"n": 3}]]), [{"n": 1}, {"n": 2}, {"n": 3}])
        self.assertEqual(gate.pages([{"total_count": 1}, {"total_count": 1}]), [{"total_count": 1}, {"total_count": 1}])
        self.assertEqual(gate.pages([{"n": 1}]), [{"n": 1}])
        self.assertEqual(gate.pages({"n": 1}), [{"n": 1}])
        self.assertEqual(gate.pages([[]]), [])

    def test_skill_version_comes_from_the_frontmatter(self):
        self.assertRegex(gate.skill_version(SKILL_DIR), r"^\d+\.\d+\.\d+$")
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(gate.skill_version(Path(directory)), "unknown")
            (Path(directory) / "SKILL.md").write_text("---\nname: x\n---\nversion: 9.9.9\n", encoding="utf-8")
            self.assertEqual(gate.skill_version(Path(directory)), "unknown")
            (Path(directory) / "SKILL.md").write_text("---\nname: x\nversion: 1.2.3\n---\nbody\n", encoding="utf-8")
            self.assertEqual(gate.skill_version(Path(directory)), "1.2.3")


def review(state="APPROVED", uid=MAINTAINER, sha=HEAD, number=7, repo=REPO, login="maintainer"):
    return {"id": 1, "state": state, "commit_id": sha,
            "user": {"id": uid, "login": login} if uid is not None else None,
            "pull_request_url": f"https://api.github.com/repos/{repo}/pulls/{number}"}


def approve(*reviews, **overrides):
    return evaluate(allow_approve=True, reviews=list(reviews), **overrides)


def held(**overrides):
    """A PR that branch protection holds back, the one case the sweep approves."""
    return pull(**{"mergeable_state": "blocked", **overrides})


class ApproveTests(unittest.TestCase):
    def test_off_by_default(self):
        self.assertFalse(evaluate()["approve"])
        self.assertFalse(evaluate(pr=held())["approve"])

    def test_only_a_pr_held_back_by_protection_is_approved(self):
        clean = approve()
        self.assertEqual(clean["verdict"], "merge")
        self.assertFalse(clean["approve"])
        blocked = approve(pr=held())
        self.assertEqual(blocked["verdict"], "blocked")
        self.assertEqual(len(blocked["reasons"]), 1)
        self.assertIn("branch protection is not satisfied", blocked["reasons"][0])
        self.assertTrue(blocked["approve"])

    def test_no_second_approval_on_the_same_head(self):
        still = approve(review(), pr=held())
        self.assertEqual(still["verdict"], "blocked")
        self.assertFalse(still["approve"])
        self.assertIn("still blocks although the head commit is approved", still["reasons"][0])
        cases = {
            "approval on an older commit": ([review(sha=OTHER)], True),
            "approval on the head, dismissed": ([review(state="DISMISSED")], True),
            "approval on the head, then a comment": ([review(), review(state="COMMENTED")], False),
        }
        for name, (reviews, expected) in cases.items():
            with self.subTest(name):
                self.assertEqual(approve(*reviews, pr=held())["approve"], expected)

    def test_requested_changes_block_approval_and_merge(self):
        decision = approve(review("CHANGES_REQUESTED", login="alice"))
        self.assertEqual(decision["verdict"], "blocked")
        self.assertIn("alice requested changes", decision["reasons"][0])
        self.assertFalse(decision["approve"])
        cases = {
            "then a comment": ([review("CHANGES_REQUESTED"), review("COMMENTED")], "blocked"),
            # A dismissed request shows up as one DISMISSED entry, which is skipped.
            "a dismissed review on its own": ([review("DISMISSED")], "merge"),
            # The approval that followed the request was dismissed: the request stands again.
            "then an approval, dismissed": ([review("CHANGES_REQUESTED"), review("DISMISSED")], "blocked"),
            "then an approval": ([review("CHANGES_REQUESTED", sha=OTHER), review(sha=OTHER)], "merge"),
            "by someone else": ([review("CHANGES_REQUESTED", uid=5, login="bob"), review()], "blocked"),
        }
        for name, (reviews, verdict) in cases.items():
            with self.subTest(name):
                self.assertEqual(approve(*reviews)["verdict"], verdict)
        self.assertTrue(approve(review("CHANGES_REQUESTED", sha=OTHER), review(sha=OTHER),
                                pr=held())["approve"])
        blocked = approve(review("CHANGES_REQUESTED"), pr=held())
        self.assertEqual(blocked["verdict"], "blocked")
        self.assertFalse(blocked["approve"])
        # A's approval sits on the head; B's request outlives B's dismissed approval.
        # A = the default maintainer reviewer, B = bob.
        second = approve(review(), review("CHANGES_REQUESTED", uid=5, login="bob"),
                         review("DISMISSED", uid=5, login="bob"), pr=held())
        self.assertEqual(second["verdict"], "blocked")
        self.assertIn("bob requested changes", second["reasons"][0])
        self.assertFalse(second["approve"])

    def test_deleted_reviewers_do_not_cancel_each_other(self):
        decision = approve(review("CHANGES_REQUESTED", uid=None), review("APPROVED", uid=None))
        self.assertEqual(decision["verdict"], "blocked")
        self.assertIn("a deleted account requested changes", decision["reasons"][0])

    def test_reviews_must_belong_to_this_pull_request(self):
        for reviews in ([review(number=70)], [review(number=17)], [review(repo="acme/other")],
                        [review(), review(number=8)], [{"message": "Not Found"}], ["APPROVED"]):
            with self.subTest(reviews=reviews):
                decision = approve(*reviews)
                self.assertEqual(decision["verdict"], "pending")
                self.assertFalse(decision["approve"])
        upper = approve(review(repo="ACME/Widgets"))
        self.assertEqual(upper["verdict"], "merge")
        for payload in (None, {"message": "Not Found"}):
            decision = evaluate(allow_approve=True, reviews=payload)
            self.assertEqual(decision["verdict"], "pending")
            self.assertIn("not a list of GitHub reviews", decision["reasons"][0])

    def test_only_green_ci_on_the_head_is_approved(self):
        cases = {
            "failed check": dict(check_pages=[runs(run(conclusion="failure"))]),
            "running check": dict(check_pages=[runs(run(status="in_progress", conclusion=None))]),
            "no CI at all": dict(check_pages=[runs()]),
            "head moved": dict(expected_head=OTHER),
            "too fresh": dict(now=datetime(2026, 10, 26, 11, 5, tzinfo=timezone.utc)),
            "behind": dict(pr=pull(mergeable_state="behind")),
            "conflicts": dict(pr=pull(mergeable=False, mergeable_state="dirty")),
            "untrusted author": dict(pr=held(user=user(uid=5))),
            "major label": dict(pr=held(labels=[{"name": "major"}])),
            "mergeability unknown": dict(pr=pull(mergeable=None, mergeable_state="unknown")),
        }
        for name, overrides in cases.items():
            with self.subTest(name):
                # Unless the case is about mergeability itself, protection holds the PR back
                # as well, so only the case can stop the approval.
                self.assertFalse(approve(**{"pr": held(), **overrides})["approve"])
        self.assertTrue(approve(pr=held())["approve"])
        running_and_blocked = approve(pr=held(),
                                      check_pages=[runs(run(status="queued", conclusion=None))])
        self.assertEqual(running_and_blocked["verdict"], "blocked")
        self.assertFalse(running_and_blocked["approve"])


class NoCiTests(unittest.TestCase):
    """A bot PR on whose head no CI reported at all: refresh it once per head, otherwise hint."""

    NO_CI = "no check run or status finished with success"

    def pre_commit(self, **overrides):
        fields = dict(pr=pull(user=user("pre-commit-ci[bot]", PRE_COMMIT_CI), mergeable_state="blocked"),
                      commits=[pre_commit_commit()], check_pages=[runs()], status=status())
        fields.update(overrides)
        return evaluate(**fields)

    def update_merge_head(self, **overrides):
        fields = dict(pr=pull(mergeable_state="blocked", commits=2,
                              head={"sha": MERGE_SHA, "repo": {"full_name": REPO}}),
                      commits=[commit(), update_merge()], check_pages=[runs()], status=status(sha=MERGE_SHA),
                      expected_head=MERGE_SHA)
        fields.update(overrides)
        return evaluate(**fields)

    def test_branch_update_gives_ci_a_new_commit(self):
        for name, decision in (("pre-commit.ci", self.pre_commit(allow_branch_update=True)),
                               ("Dependabot", evaluate(pr=pull(mergeable_state="blocked"), check_pages=[runs()],
                                                       status=status(), allow_branch_update=True))):
            with self.subTest(name):
                self.assertEqual(decision["verdict"], "blocked")
                self.assertTrue(decision["update_branch"])
        self.assertFalse(self.pre_commit()["update_branch"])

    def test_bots_get_their_own_rerun_hint(self):
        self.assertTrue(any("pre-commit.ci run" in hint for hint in self.pre_commit()["hints"]))
        dependabot = evaluate(pr=pull(mergeable_state="blocked"), check_pages=[runs()], status=status())
        self.assertTrue(any("@dependabot rebase" in hint for hint in dependabot["hints"]))

    def test_once_per_head(self):
        for allow in (True, False):
            with self.subTest(allow_branch_update=allow):
                decision = self.update_merge_head(allow_branch_update=allow)
                self.assertEqual(decision["verdict"], "blocked")
                self.assertFalse(decision["update_branch"])
                self.assertTrue(any("even on GitHub's Update branch merge" in hint for hint in decision["hints"]))

    def test_failed_checks_are_not_refreshed_and_get_no_rerun_hint(self):
        decision = self.pre_commit(allow_branch_update=True, check_pages=[runs(run(conclusion="failure"))])
        self.assertFalse(decision["update_branch"])
        self.assertFalse(any("pre-commit.ci run" in hint for hint in decision["hints"]))

    def test_skipped_only_checks_are_not_no_ci(self):
        for strict in (False, True):
            with self.subTest(strict=strict):
                decision = self.pre_commit(allow_branch_update=True, strict=strict,
                                           check_pages=[runs(run(conclusion="skipped"))])
                self.assertIn(self.NO_CI, " ".join(decision["reasons"]))
                self.assertFalse(decision["update_branch"])

    def test_a_behind_update_merge_head_is_updated_again(self):
        behind = pull(mergeable_state="behind", commits=2, head={"sha": MERGE_SHA, "repo": {"full_name": REPO}})
        for name, check_pages in (("green", [runs(run(head=MERGE_SHA))]), ("no CI", [runs()])):
            with self.subTest(name):
                decision = self.update_merge_head(pr=behind, check_pages=check_pages, allow_branch_update=True)
                self.assertIn("branch is behind `main`", " | ".join(decision["reasons"]))
                self.assertTrue(decision["update_branch"])

    def test_other_problems_are_not_refreshed(self):
        cases = {
            "a missing label": dict(require_labels=("internal",)),
            "a missing required check": dict(require_checks=("lint",)),
        }
        for name, overrides in cases.items():
            with self.subTest(name):
                self.assertFalse(self.pre_commit(allow_branch_update=True, **overrides)["update_branch"])

    def test_no_approval_without_ci(self):
        decision = self.pre_commit(allow_branch_update=True, allow_approve=True, reviews=[])
        self.assertFalse(decision["approve"])
        self.assertTrue(decision["update_branch"])

    def test_behind_and_without_ci(self):
        decision = self.pre_commit(pr=pull(user=user("pre-commit-ci[bot]", PRE_COMMIT_CI), mergeable_state="behind"),
                                   allow_branch_update=True)
        reasons = " | ".join(decision["reasons"])
        self.assertIn("branch is behind `main`", reasons)
        self.assertIn(self.NO_CI, reasons)
        self.assertEqual(len(decision["reasons"]), 2)
        self.assertTrue(decision["update_branch"])

    def test_report_after_an_update_a_skip_and_a_failure(self):
        def no_ci_pr(number):
            return self.pre_commit(pr=pull(number=number, user=user("pre-commit-ci[bot]", PRE_COMMIT_CI),
                                           mergeable_state="blocked"), allow_branch_update=True)

        def outcome(number, result, detail):
            return {"event": "outcome", "repo": REPO, "number": number, "result": result, "detail": detail}

        text = gate.render_report([no_ci_pr(7), no_ci_pr(8), no_ci_pr(9),
                                   outcome(7, "branch-updated", "main"),
                                   outcome(8, "update-skipped", "HTTP 422: There are no new commits on the base branch."),
                                   outcome(9, "update-failed", "HTTP 422: expected head sha didn't match current head ref.")],
                                  version="test", now=NOW)
        sections = {part.split("\n", 1)[0].split(" (")[0]: part for part in text.split("\n## ")[1:]}
        line = {number: next(line for line in text.splitlines() if f"/pull/{number})" in line) for number in (7, 8, 9)}
        self.assertIn(line[7], sections["Pending"])
        self.assertIn("branch updated from the base", line[7])
        self.assertNotIn("pre-commit.ci run", line[7])
        self.assertIn(line[8], sections["Blocked"])
        self.assertIn("branch not updated: HTTP 422", line[8])
        self.assertIn("pre-commit.ci run", line[8])
        self.assertIn(line[9], sections["Needs attention"])
        self.assertIn("branch update failed", line[9])
        self.assertIn("## Needs attention (1)", text)


class ReportTests(unittest.TestCase):
    def events(self):
        merged = evaluate()
        blocked = evaluate(pr=pull(number=8, title="Bump x\n[evil](https://e)"), check_pages=[runs(run(conclusion="failure"))])
        behind = evaluate(pr=pull(number=9, mergeable_state="behind"))
        pending = evaluate(pr=pull(number=10), check_pages=[runs(run(status="queued", conclusion=None))])
        rejected = evaluate(pr=pull(number=11, user=user(uid=5)))
        updated = evaluate(pr=pull(number=13, mergeable_state="behind"), allow_branch_update=True)
        return [
            {"event": "selection", "repo": REPO, "open_prs": 9, "bot_prs": [7, 8, 9, 10, 13], "other_bots": 1,
             "suspicious": [{"number": 12, "login": "dependabot[bot]", "id": 1, "reason": "account 1 is not trusted"}]},
            merged, blocked, behind, pending, rejected, updated,
            {"event": "outcome", "repo": REPO, "number": 7, "result": "assigned", "detail": "maintainer"},
            {"event": "outcome", "repo": REPO, "number": 7, "result": "merged", "detail": "c" * 40},
            {"event": "outcome", "repo": REPO, "number": 8, "result": "assigned", "detail": "maintainer"},
            {"event": "outcome", "repo": REPO, "number": 9, "result": "assign-failed", "detail": "HTTP 422"},
            {"event": "outcome", "repo": REPO, "number": 13, "result": "branch-updated", "detail": "main"},
            {"event": "outcome", "repo": REPO, "number": 8, "result": "label-removed", "detail": "major"},
            {"event": "outcome", "repo": "acme/other", "number": None, "result": "repo-error", "detail": "HTTP 403"},
        ]

    def test_report_groups_prs_and_stamps_the_version(self):
        text = gate.render_report(self.events(), version="0.1.0", now=NOW)
        self.assertIn("version 0.1.0", text)
        self.assertIn("Generated 2026-10-26T12:00:00Z", text)
        self.assertIn("- Mode: live", text)
        self.assertIn("## Merged (1)", text)
        self.assertIn("## Blocked (1)", text)
        self.assertIn("## Pending (2)", text)
        self.assertIn("## Needs attention (4)", text)
        self.assertIn("[acme/widgets#7](https://github.com/acme/widgets/pull/7)", text)
        self.assertIn("squash-merged as [`ccccccc`](https://github.com/acme/widgets/commit/cccccccccccccccccccccccccccccccccccccccc); "
                      "assigned to [maintainer](https://github.com/maintainer)", text)
        self.assertIn("`Bump x [evil] (https://e)`", text)
        self.assertNotIn("\n[evil]", text)
        self.assertIn("@dependabot rebase", text)
        self.assertIn("assignment failed: HTTP 422", text)
        self.assertIn("branch updated from the base; the next run re-evaluates it", text)
        self.assertIn("label `major` removed; assigned to [maintainer](https://github.com/maintainer)", text)
        self.assertIn("pull/12) — account 1 is not trusted; not touched", text)
        self.assertIn("- [acme/other](https://github.com/acme/other): HTTP 403", text)
        self.assertIn("- [acme/widgets](https://github.com/acme/widgets/pulls): 9 open PRs, 5 from trusted bots, 1 suspicious, "
                      "1 from other bots", text)

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
        events = [evaluate(pr=pull(labels=[{"name": "major"}])),
                  {"event": "outcome", "repo": REPO, "number": 7, "result": "label-failed", "detail": "re-added after removal"}]
        text = gate.render_report(events, version="0.1.0", now=NOW)
        self.assertIn("## Needs attention (1)", text)
        self.assertIn("label removal failed: re-added after removal", text)
        self.assertIn("## Blocked (0)", text)

    def test_approvals_in_the_report(self):
        merged = approve(review())  # gated again after the approval, now clean
        still_blocked = approve(review(number=8), pr=held(number=8))
        failed = approve(pr=held(number=9))
        declined = approve(pr=held(number=10))
        unasked = approve(pr=held(number=11))
        events = [merged, still_blocked, failed, declined, unasked,
                  {"event": "outcome", "repo": REPO, "number": 7, "result": "approved", "detail": HEAD},
                  {"event": "outcome", "repo": REPO, "number": 7, "result": "merged", "detail": "c" * 40},
                  {"event": "outcome", "repo": REPO, "number": 8, "result": "approved", "detail": HEAD},
                  {"event": "outcome", "repo": REPO, "number": 9, "result": "approve-failed", "detail": "HTTP 403"},
                  {"event": "outcome", "repo": REPO, "number": 10, "result": "approve-skipped",
                   "detail": "declined by the user"},
                  {"event": "outcome", "repo": REPO, "number": 11, "result": "approve-skipped",
                   "detail": "no one to ask (--approve-mode ask)"}]
        text = gate.render_report(events, version="0.2.0", now=NOW)
        self.assertIn("## Merged (1)", text)
        self.assertIn(f"approved by the sweep at [`aaaaaaa`](https://github.com/acme/widgets/commit/{HEAD}); "
                      f"squash-merged as [`ccccccc`](https://github.com/acme/widgets/commit/{'c' * 40})", text)
        # Skipped approvals are a choice, not a failure: the PRs stay under Blocked.
        self.assertIn("## Blocked (3)", text)
        self.assertIn("still blocks although the head commit is approved", text)
        self.assertIn("not approved: declined by the user", text)
        self.assertIn("not approved: no one to ask (--approve-mode ask)", text)
        self.assertIn("## Needs attention (1)", text)
        self.assertIn("approval failed: HTTP 403", text)
        dry = gate.render_report([approve(pr=held())], version="0.2.0", now=NOW, dry_run=True)
        self.assertIn("would approve (dry run)", dry)
        self.assertNotIn("would approve", gate.render_report([approve()], version="0.2.0", now=NOW))

    def test_repositories_without_open_prs_are_counted_not_listed(self):
        def selection(repo, open_prs, **extra):
            return {"event": "selection", "repo": repo, "open_prs": open_prs, "bot_prs": [],
                    "suspicious": [], "other_bots": 0, **extra}

        def report(*selections):
            return gate.render_report(list(selections), version="0.3.0", now=NOW)

        with self.subTest("some quiet"):
            text = report(selection("acme/a", 2), selection("acme/b", 0), selection("acme/c", 0))
            self.assertIn("- [acme/a](https://github.com/acme/a/pulls): 2 open PRs", text)
            self.assertNotIn("acme/b", text)
            self.assertIn("- 2 more repositories with no open PRs\n", text)
            self.assertIn("- Repositories swept: 3;", text)
        with self.subTest("one quiet"):
            self.assertIn("- 1 more repository with no open PRs\n", report(selection("acme/a", 1), selection("acme/b", 0)))
        with self.subTest("all quiet"):
            text = report(selection("acme/a", 0), selection("acme/b", 0))
            self.assertIn("## Repositories\n\n- 2 repositories with no open PRs\n", text)
        with self.subTest("unusable count"):
            text = report(selection("acme/a", None))
            self.assertIn("- [acme/a](https://github.com/acme/a/pulls): ", text)
            self.assertNotIn("no open PRs", text)
        with self.subTest("suspicious PR in a zero count"):
            text = report(selection("acme/a", 0, suspicious=[{"number": 3, "reason": "look-alike"}]))
            self.assertIn("- [acme/a](https://github.com/acme/a/pulls): ", text)

    def test_links_only_well_formed_values(self):
        evil = "[x](https://e.com)"
        html = '<a href="https://e.com">x</a>'
        good = {
            "repository": (gate._repo_link("acme/widgets"), "[acme/widgets](https://github.com/acme/widgets)"),
            "pull request": (gate._pull_link("acme/widgets", 7), "[acme/widgets#7](https://github.com/acme/widgets/pull/7)"),
            "commit": (gate._commit_link("acme/widgets", HEAD), f"[`aaaaaaa`](https://github.com/acme/widgets/commit/{HEAD})"),
            "account": (gate._user_link("jdoe"), "[jdoe](https://github.com/jdoe)"),
        }
        for name, (got, expected) in good.items():
            with self.subTest(name):
                self.assertEqual(got, expected)
        plain = {
            "repository": gate._repo_link(evil),
            "pull request": gate._pull_link(evil, 1),
            "commit in a bad repository": gate._commit_link(evil, HEAD),
            "bad commit": gate._commit_link("acme/widgets", evil),
            "account": gate._user_link(evil),
            "dot-dot repository": gate._repo_link("../.."),
            "dot owner": gate._repo_link(".git/x"),
            "missing number": gate._pull_link("acme/widgets", None),
            "trailing hyphen": gate._user_link("abc-"),
            "raw HTML account": gate._user_link(html),
            "raw HTML repository": gate._repo_link(html),
            "angle-bracket autolink": gate.sanitize("<https://e.com>"),
        }
        for name, got in plain.items():
            with self.subTest(name):
                self.assertNotIn("](", got)
                self.assertNotIn("<", got)
                self.assertNotIn("https://github.com", got)
        with self.subTest("no repository at all"):
            self.assertEqual(gate._repo_link(None), "unknown")
        with self.subTest("good commit in a bad repository keeps its backticks"):
            self.assertEqual(gate._commit_link("../..", HEAD), "`aaaaaaa`")

    def test_outcome_without_a_decision_is_flagged(self):
        events = [{"event": "outcome", "repo": REPO, "number": 99, "result": "merged", "detail": "e" * 40}]
        text = gate.render_report(events, version="0.1.0", now=NOW)
        self.assertIn("## Needs attention (1)", text)
        self.assertIn("- [acme/widgets#99](https://github.com/acme/widgets/pull/99): `merged` recorded without a gate decision", text)

    def test_schedule_line_is_optional_and_sanitized(self):
        text = gate.render_report([], version="0.1.0", now=NOW, schedule="daily at 06:00 UTC\n[evil](https://e)")
        self.assertIn("- Mode: live\n- Schedule: `daily at 06:00 UTC [evil] (https://e)`\n- Repositories swept", text)
        long = gate.render_report([], version="0.1.0", now=NOW, schedule="every " + "x" * 100)
        self.assertRegex(long, r"- Schedule: `every x+…`\n")
        self.assertNotIn("x" * 100, long)
        for text in (gate.render_report([], version="0.1.0", now=NOW),
                     gate.render_report([], version="0.1.0", now=NOW, schedule="")):
            self.assertNotIn("Schedule", text)

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
            "pr": pull(), "commits": [[commit()]], "checks": [runs(run())], "status": status(),
            "pulls": [[pull()], [pull(number=8, user=user("dependabot[bot]", 1))]],
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

    def gate_args(self, *flags, **extra):
        argv = ["gate", "--repo", REPO, "--ledger", str(self.ledger), "--pr", self.path("pr"),
                "--commits", self.path("commits"), "--check-runs", self.path("checks"),
                "--status", self.path("status"), "--now", "2026-10-26T12:00:00Z", "--head-sha", HEAD]
        argv += list(flags)
        for key, value in extra.items():
            argv += [key, value]
        return argv

    def test_init_creates_a_fresh_directory(self):
        code, out, _ = self.main("init")
        self.assertEqual(code, 0)
        work = out.strip()
        self.addCleanup(os.rmdir, work)
        self.assertTrue(Path(work).is_dir())
        self.assertIn("bot-pr-sweep-", Path(work).name)

    def test_gate_exit_codes(self):
        code, out, _ = self.main(*self.gate_args())
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["verdict"], "merge")
        self.assertEqual(json.loads(self.ledger.read_text().splitlines()[0])["event"], "decision")
        (self.root / "checks.json").write_text(json.dumps([runs(run(conclusion="failure"))]), encoding="utf-8")
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

    def test_gate_rejects_bad_arguments(self):
        with self.assertRaises(SystemExit):
            self.main(*[arg for arg in self.gate_args() if arg not in ("--head-sha", HEAD)])
        with self.assertRaises(SystemExit):
            self.main(*self.gate_args(**{"--repo": "acme/widgets/evil"}))
        with self.assertRaises(SystemExit):
            self.main(*self.gate_args(**{"--head-sha": "nope"}))

    def test_gate_options(self):
        (self.root / "checks.json").write_text(json.dumps([runs(run(), run(name="x", conclusion="skipped"))]), encoding="utf-8")
        self.assertEqual(self.main(*self.gate_args())[0], 0)
        self.assertEqual(self.main(*self.gate_args("--strict"))[0], 1)
        self.assertEqual(self.main(*self.gate_args(**{"--require-check": "lint"}))[0], 1)
        self.assertEqual(self.main(*self.gate_args(**{"--require-label": "internal"}))[0], 1)
        self.assertEqual(self.main(*self.gate_args(**{"--forbid-label": "major"}))[0], 0)
        self.assertEqual(self.main(*self.gate_args(**{"--head-sha": OTHER}))[0], 1)
        (self.root / "pr.json").write_text(json.dumps(pull(mergeable_state="behind")), encoding="utf-8")
        code, out, _ = self.main(*self.gate_args("--allow-branch-update"))
        self.assertEqual(code, 1)
        self.assertTrue(json.loads(out)["update_branch"])

    def test_gate_mixed_bots_option(self):
        payloads = {"pr": pull(commits=2, head={"sha": OTHER, "repo": {"full_name": REPO}}),
                    "commits": [[commit(), autofix()]], "checks": [runs(run(head=OTHER))], "status": status(sha=OTHER)}
        for name, payload in payloads.items():
            (self.root / f"{name}.json").write_text(json.dumps(payload), encoding="utf-8")
        self.assertEqual(self.main(*self.gate_args(**{"--head-sha": OTHER}))[0], 1)
        self.assertEqual(self.main(*self.gate_args("--allow-mixed-bots", **{"--head-sha": OTHER}))[0], 0)

    def test_gate_workflow_runs_option(self):
        pages = [runs(job(1, 10, conclusion="failure"), total=2), runs(job(2, 11), total=2)]
        (self.root / "checks.json").write_text(json.dumps(pages), encoding="utf-8")
        (self.root / "flows.json").write_text(json.dumps(workflow_runs(workflow_run(10), workflow_run(11))),
                                              encoding="utf-8")
        self.assertEqual(self.main(*self.gate_args())[0], 1)
        code, out, _ = self.main(*self.gate_args(**{"--workflow-runs": self.path("flows")}))
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["checks"]["superseded"], ["label-check"])

    def test_gate_approve_option(self):
        code, _, err = self.main(*self.gate_args("--allow-approve"))
        self.assertEqual(code, 2)
        self.assertIn("--allow-approve and --reviews go together", err)
        (self.root / "reviews.json").write_text(json.dumps([[], [review(state="COMMENTED")]]), encoding="utf-8")
        (self.root / "pr.json").write_text(json.dumps(held()), encoding="utf-8")
        code, out, _ = self.main(*self.gate_args("--allow-approve", **{"--reviews": self.path("reviews")}))
        self.assertEqual(code, 1)
        self.assertTrue(json.loads(out)["approve"])
        code, _, err = self.main(*self.gate_args(**{"--reviews": self.path("reviews")}))
        self.assertEqual(code, 2)
        self.assertIn("go together", err)
        (self.root / "reviews.json").write_text(json.dumps({"message": "Not Found"}), encoding="utf-8")
        (self.root / "pr.json").write_text(json.dumps(pull()), encoding="utf-8")
        code, out, _ = self.main(*self.gate_args("--allow-approve", **{"--reviews": self.path("reviews")}))
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(out)["verdict"], "pending")
        self.assertFalse(json.loads(out)["approve"])
        for result, detail in (("approved", HEAD), ("approve-skipped", "declined by the user"),
                               ("approve-skipped", "no one to ask (--approve-mode ask)")):
            code, _, _ = self.main("outcome", "--repo", REPO, "--ledger", str(self.ledger), "--number", "7",
                                   "--result", result, "--detail", detail)
            self.assertEqual(code, 0)

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
        self.assertIn(f"squash-merged as [`ddddddd`](https://github.com/acme/widgets/commit/{'d' * 40})", out)
        self.assertIn("pull/8) — login 'dependabot[bot]' resembles a trusted bot but account 1 is not trusted; not touched", out)
        self.assertIn("- [acme/other](https://github.com/acme/other): HTTP 403", out)
        code, _, err = self.main("report", "--ledger", str(self.root / "missing.jsonl"), "--dry-run")
        self.assertEqual(code, 2)
        self.assertIn("does not exist", err)
        code, out, _ = self.main("report", "--ledger", str(self.ledger), "--dry-run")
        self.assertEqual(code, 0)
        self.assertIn("dry run", out)
        code, out, _ = self.main("report", "--ledger", str(self.ledger), "--schedule", "hourly")
        self.assertEqual(code, 0)
        self.assertIn("- Schedule: `hourly`\n", out)
        with self.ledger.open("a", encoding="utf-8") as handle:
            handle.write('{"event": "outcome", "repo": "acme/widgets"\n')
        code, _, err = self.main("report", "--ledger", str(self.ledger))
        self.assertEqual(code, 2)
        self.assertIn("error:", err)

    def test_outcome_rejects_unknown_results(self):
        with self.assertRaises(SystemExit):
            self.main("outcome", "--repo", REPO, "--ledger", str(self.ledger), "--result", "whatever")


if __name__ == "__main__":
    unittest.main()
