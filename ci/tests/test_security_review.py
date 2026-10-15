"""Focused tests for the review runner restrictions and failure handling."""
from pathlib import Path
import os
import subprocess
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import security_review as review


class ReviewTests(unittest.TestCase):
    def test_restricted_invocation(self):
        report = "SKILL: candidate\nVERDICT: SAFE\nFINDINGS: none\n\nSUMMARY: No findings.\n"
        with patch.dict(os.environ, {"GH_TOKEN": "test-only-sentinel"}), patch.object(
            review.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, report, "")
        ) as run:
            self.assertEqual(review.review_skill(Path("candidate"), ["claude"])[0], "SAFE")
        args = run.call_args.args[0]
        self.assertIn("--restricted", args)
        self.assertIn("--bare", args)
        self.assertNotIn("--dangerously-skip-permissions", args)
        self.assertEqual(args[args.index("--tools") + 1], "Read,Glob,Grep")
        self.assertIn("--strict-mcp-config", args)
        self.assertNotIn("GH_TOKEN", run.call_args.kwargs["env"])

    def test_process_failure_cannot_pass(self):
        with patch.object(review.subprocess, "run", return_value=subprocess.CompletedProcess(
            [], 1, "VERDICT: SAFE", "failure"
        )):
            self.assertEqual(review.review_skill(Path("candidate"), ["claude"])[0], "ERROR")

    def test_invalid_reports_cannot_pass(self):
        for report in ["VERDICT: SAFE", "VERDICT: UNKNOWN", "VERDICT: SAFE\nVERDICT: HIGH"]:
            with self.subTest(report=report):
                self.assertEqual(review._parse_report("candidate", report), "ERROR")
