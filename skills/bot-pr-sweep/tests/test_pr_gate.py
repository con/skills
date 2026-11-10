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
        self.assertEqual(decision["checks"]["passed"], ["tests 'rm -rf' [click](https://x)"])

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
        self.assertIn("behind `ma<in> '`", decision["reasons"][1])
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


class HelperTests(unittest.TestCase):
    def test_sanitize(self):
        self.assertEqual(gate.sanitize("Bump `x`\n[evil](http://e)\x07 now"), "Bump 'x' [evil](http://e) now")
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
        self.assertIn("squash-merged as `ccccccc`; assigned to maintainer", text)
        self.assertIn("`Bump x [evil](https://e)`", text)
        self.assertNotIn("\n[evil]", text)
        self.assertIn("@dependabot rebase", text)
        self.assertIn("assignment failed: HTTP 422", text)
        self.assertIn("branch updated from the base; the next run re-evaluates it", text)
        self.assertIn("label `major` removed; assigned to maintainer", text)
        self.assertIn("pull/12) — account 1 is not trusted; not touched", text)
        self.assertIn("- acme/other: HTTP 403", text)
        self.assertIn("- acme/widgets: 9 open PRs, 5 from trusted bots, 1 suspicious, 1 from other bots", text)

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

    def test_outcome_without_a_decision_is_flagged(self):
        events = [{"event": "outcome", "repo": REPO, "number": 99, "result": "merged", "detail": "e" * 40}]
        text = gate.render_report(events, version="0.1.0", now=NOW)
        self.assertIn("## Needs attention (1)", text)
        self.assertIn("- acme/widgets#99: `merged` recorded without a gate decision", text)

    def test_schedule_line_is_optional_and_sanitized(self):
        text = gate.render_report([], version="0.1.0", now=NOW, schedule="daily at 06:00 UTC\n[evil](https://e)")
        self.assertIn("- Mode: live\n- Schedule: `daily at 06:00 UTC [evil](https://e)`\n- Repositories swept", text)
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
