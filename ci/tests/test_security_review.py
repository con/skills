"""Regression tests for the audit process boundary and fail-closed reports."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import security_review as review
import validate_skills as validate


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.skill = Path(self.tmp.name) / 'candidate'
        self.skill.mkdir()
        (self.skill / 'SKILL.md').write_text('untrusted content')
        self.safe = 'SKILL: candidate\nVERDICT: SAFE\nFINDINGS: none\n\nSUMMARY: No findings.\n'

    def run_report(self, stdout, code=0, stderr=''):
        with patch.object(review.subprocess, 'run', return_value=subprocess.CompletedProcess([], code, stdout, stderr)):
            return review.review_skill(self.skill, ['claude'])[0]

    def test_reports_fail_closed(self):
        self.assertEqual(self.run_report(self.safe), 'SAFE')
        for text in ['', 'VERDICT: SAFE', self.safe.replace('SAFE', 'BANANA'),
                     self.safe + 'VERDICT: SAFE\n', self.safe.replace('candidate', 'other'),
                     self.safe.replace('none', '- [HIGH] Bad')]:
            with self.subTest(text=text):
                self.assertEqual(self.run_report(text), 'ERROR')
        self.assertEqual(self.run_report(self.safe, code=1), 'ERROR')
        self.assertEqual(self.run_report('', stderr=self.safe), 'ERROR')
        self.assertEqual(self.run_report(self.safe.replace('SAFE', 'HIGH').replace('none', '\n- [HIGH] Risk')), 'HIGH')

    def test_real_launcher_receives_snapshot_without_secrets(self):
        launcher = Path(self.tmp.name) / 'launcher.py'
        launcher.write_text('''import json, os, sys
from pathlib import Path
args = sys.argv[1:]
assert args[args.index('--tools') + 1] == ''
assert '--bare' in args and '--strict-mcp-config' in args
assert 'GH_TOKEN' not in os.environ
assert not (Path.cwd() / 'SKILL.md').exists()
data = json.load(sys.stdin)
assert data['files'][0]['content'] == 'untrusted content'
print('SKILL: candidate\\nVERDICT: SAFE\\nFINDINGS: none\\n\\nSUMMARY: No findings.')
''')
        with patch.dict(os.environ, {'GH_TOKEN': 'test-only-sentinel'}):
            verdict, output = review.review_skill(self.skill, [sys.executable, str(launcher)])
        self.assertEqual(verdict, 'SAFE', output)

    def test_snapshot_rejects_symlinks_binary_and_limits(self):
        bad = self.skill / 'bad'
        bad.symlink_to(Path(self.tmp.name))
        with self.assertRaises(ValueError):
            review._snapshot(self.skill)
        bad.unlink()
        bad.write_bytes(b'\x00')
        with self.assertRaises(ValueError):
            review._snapshot(self.skill)
        bad.write_text('a' * 20)
        with patch.object(review, 'MAX_SNAPSHOT_BYTES', 10), self.assertRaises(ValueError):
            review._snapshot(self.skill)

    def test_timeout_and_missing_launcher_fail_closed(self):
        for error in [FileNotFoundError("missing"), subprocess.TimeoutExpired('claude', 300)]:
            with self.subTest(error=error), patch.object(review.subprocess, 'run', side_effect=error):
                self.assertEqual(review.review_skill(self.skill, ['claude'])[0], 'ERROR')

    def test_verdict_cannot_understate_findings(self):
        report = self.safe.replace('VERDICT: SAFE', 'VERDICT: LOW').replace(
            'FINDINGS: none', 'FINDINGS:\n- [HIGH] Unsafe operation')
        self.assertEqual(self.run_report(report), 'ERROR')

    def test_validator_handles_scalar_frontmatter_and_nested_python(self):
        (self.skill / 'SKILL.md').write_text('---\nscalar\n---\nbody')
        self.assertTrue(validate.validate_skill(self.skill).errors)
        nested = self.skill / 'scripts'
        nested.mkdir()
        (nested / 'broken.py').write_text('def broken(')
        result = validate.validate_skill(self.skill)
        self.assertTrue(any('E005' in str(error) for error in result.errors))

    def test_discovery_and_prompt_use_canonical_sources(self):
        self.assertEqual(review.find_skill_dirs(Path(self.tmp.name)), [self.skill])
        self.assertEqual(validate.find_skill_dirs(Path(self.tmp.name)), [self.skill])
        self.assertIn('## Checks', review._review_prompt())

    def test_bad_configuration_and_missing_input(self):
        with patch.dict(os.environ, {'FAIL_ON': 'HGIH'}):
            self.assertEqual(review.main([str(self.skill)]), 2)
        with patch.dict(os.environ, {'SECURITY_CMD': ''}):
            self.assertEqual(review.main([str(self.skill)]), 2)
        self.assertEqual(review.review_skill(self.skill / 'missing', ['claude'])[0], 'ERROR')


if __name__ == '__main__':
    unittest.main()
