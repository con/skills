"""Unit tests for bot_pr_gate.py. Run with: python3 -m unittest discover -s tests"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import bot_pr_gate as gate  # noqa: E402


def _run(conclusion="success", status="completed", name="ci"):
    return {"name": name, "status": status, "conclusion": conclusion}


class AuthorTest(unittest.TestCase):
    def test_dependabot_id_and_login_match(self):
        pr = {"user": {"login": "dependabot[bot]", "id": 49699333}}
        self.assertEqual(gate.check_author(pr)[0], True)

    def test_pre_commit_ci_id_and_login_match(self):
        pr = {"user": {"login": "pre-commit-ci[bot]", "id": 66853113}}
        self.assertEqual(gate.check_author(pr)[0], True)

    def test_login_spoof_with_unknown_id_is_rejected(self):
        pr = {"user": {"login": "dependabot[bot]", "id": 1234}}
        self.assertEqual(gate.check_author(pr)[0], False)

    def test_trusted_id_with_wrong_login_is_rejected(self):
        pr = {"user": {"login": "someone-else", "id": 49699333}}
        self.assertEqual(gate.check_author(pr)[0], False)

    def test_missing_user_is_rejected(self):
        self.assertEqual(gate.check_author({})[0], False)


class ChecksTest(unittest.TestCase):
    def test_all_passing_is_green(self):
        runs = {"check_runs": [_run(), _run("skipped"), _run("neutral")]}
        status = {"state": "success", "statuses": [{"state": "success", "context": "x"}]}
        self.assertEqual(gate.check_head(runs, status)[0], "GREEN")

    def test_failed_check_is_red(self):
        runs = {"check_runs": [_run("failure")]}
        status = {"state": "success", "statuses": []}
        self.assertEqual(gate.check_head(runs, status)[0], "RED")

    def test_cancelled_check_is_red(self):
        runs = {"check_runs": [_run("cancelled")]}
        status = {"state": "success", "statuses": []}
        self.assertEqual(gate.check_head(runs, status)[0], "RED")

    def test_in_progress_check_is_pending(self):
        runs = {"check_runs": [_run(conclusion=None, status="in_progress")]}
        status = {"state": "success", "statuses": []}
        self.assertEqual(gate.check_head(runs, status)[0], "PENDING")

    def test_pending_status_with_no_contexts_is_pending(self):
        runs = {"check_runs": [_run()]}
        status = {"state": "pending", "statuses": []}
        self.assertEqual(gate.check_head(runs, status)[0], "PENDING")

    def test_failed_status_context_is_red(self):
        runs = {"check_runs": [_run()]}
        status = {"state": "failure", "statuses": [{"state": "failure", "context": "ui"}]}
        self.assertEqual(gate.check_head(runs, status)[0], "RED")

    def test_red_outranks_pending(self):
        runs = {"check_runs": [_run("failure"), _run(conclusion=None, status="queued")]}
        status = {"state": "pending", "statuses": []}
        self.assertEqual(gate.check_head(runs, status)[0], "RED")


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
        runs = self._write({"check_runs": [_run()]})
        green = self._write({"state": "success", "statuses": []})
        red = self._write({"state": "failure", "statuses": []})
        self.assertEqual(gate.main(["checks", runs, green]), 0)
        self.assertEqual(gate.main(["checks", runs, red]), 1)


if __name__ == "__main__":
    unittest.main()
