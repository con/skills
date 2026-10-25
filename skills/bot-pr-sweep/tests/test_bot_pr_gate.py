"""Unit tests for bot_pr_gate.py. Run with: python3 -m unittest discover -s tests -v"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import bot_pr_gate as gate  # noqa: E402


def _run(conclusion="success", status="completed", name="ci"):
    return {"name": name, "status": status, "conclusion": conclusion}


def _runs(*items, total=None):
    """Build a get_check_runs payload; total_count defaults to the number returned."""
    return {"total_count": len(items) if total is None else total, "check_runs": list(items)}


def _status(state="success", contexts=()):
    return {"state": state, "statuses": list(contexts)}


class AuthorTest(unittest.TestCase):
    def test_dependabot_id_and_login_match(self):
        pr = {"user": {"login": "dependabot[bot]", "id": 49699333}}
        self.assertTrue(gate.check_author(pr)[0])

    def test_pre_commit_ci_id_and_login_match(self):
        pr = {"user": {"login": "pre-commit-ci[bot]", "id": 66853113}}
        self.assertTrue(gate.check_author(pr)[0])

    def test_login_spoof_with_unknown_id_is_rejected(self):
        pr = {"user": {"login": "dependabot[bot]", "id": 1234}}
        self.assertFalse(gate.check_author(pr)[0])

    def test_trusted_id_with_wrong_login_is_rejected(self):
        pr = {"user": {"login": "someone-else", "id": 49699333}}
        self.assertFalse(gate.check_author(pr)[0])

    def test_missing_user_is_rejected(self):
        self.assertFalse(gate.check_author({})[0])

    def test_non_object_payload_is_rejected_not_raised(self):
        self.assertFalse(gate.check_author([])[0])
        self.assertFalse(gate.check_author(None)[0])

    def test_boolean_id_is_rejected(self):
        pr = {"user": {"login": "dependabot[bot]", "id": True}}
        self.assertFalse(gate.check_author(pr)[0])


class ChecksTest(unittest.TestCase):
    def test_all_passing_is_green(self):
        runs = _runs(_run(), _run("skipped"), _run("neutral"))
        status = _status(contexts=[{"state": "success", "context": "x"}])
        self.assertEqual(gate.check_head(runs, status)[0], "GREEN")

    def test_actions_only_repo_with_empty_combined_pending_is_green(self):
        # GitHub reports combined state "pending" with no contexts for commits
        # that have no commit statuses at all; the check runs decide.
        self.assertEqual(gate.check_head(_runs(_run()), _status("pending"))[0], "GREEN")

    def test_failed_check_is_red(self):
        self.assertEqual(gate.check_head(_runs(_run("failure")), _status())[0], "RED")

    def test_cancelled_check_is_red(self):
        self.assertEqual(gate.check_head(_runs(_run("cancelled")), _status())[0], "RED")

    def test_in_progress_check_is_pending(self):
        runs = _runs(_run(conclusion=None, status="in_progress"))
        self.assertEqual(gate.check_head(runs, _status())[0], "PENDING")

    def test_pending_status_context_is_pending(self):
        status = _status("pending", [{"state": "pending", "context": "ui"}])
        self.assertEqual(gate.check_head(_runs(_run()), status)[0], "PENDING")

    def test_failed_status_context_is_red(self):
        status = _status("failure", [{"state": "failure", "context": "ui"}])
        self.assertEqual(gate.check_head(_runs(_run()), status)[0], "RED")

    def test_red_outranks_pending(self):
        runs = _runs(_run("failure"), _run(conclusion=None, status="queued"))
        self.assertEqual(gate.check_head(runs, _status("pending"))[0], "RED")

    # Fail-closed regressions: none of these may be GREEN.

    def test_empty_inputs_are_not_green(self):
        self.assertNotEqual(gate.check_head({}, {})[0], "GREEN")

    def test_empty_check_list_and_no_statuses_is_not_green(self):
        self.assertNotEqual(gate.check_head({"total_count": 0, "check_runs": []}, {"statuses": []})[0], "GREEN")

    def test_null_check_list_is_not_green_and_does_not_raise(self):
        self.assertNotEqual(gate.check_head({"check_runs": None}, {})[0], "GREEN")

    def test_non_list_payload_is_not_green_and_does_not_raise(self):
        self.assertNotEqual(gate.check_head({"check_runs": "oops"}, {})[0], "GREEN")

    def test_mcp_error_payload_is_not_green(self):
        self.assertNotEqual(gate.check_head({"error": "not found"}, {"error": "not found"})[0], "GREEN")

    def test_truncated_check_list_is_not_green(self):
        # total_count says 150 but only 100 runs came back: a partial page.
        runs = {"total_count": 150, "check_runs": [_run() for _ in range(100)]}
        self.assertNotEqual(gate.check_head(runs, _status())[0], "GREEN")

    def test_missing_total_count_is_not_green(self):
        runs = {"check_runs": [_run()]}
        self.assertNotEqual(gate.check_head(runs, _status())[0], "GREEN")


class CliTest(unittest.TestCase):
    def _write(self, obj):
        f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        json.dump(obj, f)
        f.close()
        return f.name

    def test_author_cli_exit_codes(self):
        ok = self._write({"user": {"login": "dependabot[bot]", "id": 49699333}})
        bad = self._write({"user": {"login": "dependabot[bot]", "id": 1}})
        self.assertEqual(gate.main(["author", ok]), 0)
        self.assertEqual(gate.main(["author", bad]), 1)

    def test_checks_cli_exit_codes(self):
        runs = self._write(_runs(_run()))
        green = self._write(_status())
        red = self._write(_status("failure"))
        empty = self._write({})
        self.assertEqual(gate.main(["checks", runs, green]), 0)
        self.assertEqual(gate.main(["checks", runs, red]), 1)
        self.assertEqual(gate.main(["checks", empty, empty]), 1)


if __name__ == "__main__":
    unittest.main()
