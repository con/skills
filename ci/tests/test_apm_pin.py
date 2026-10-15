"""Reject a matching SHA from the wrong source or malformed lock data."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from check_apm import check_pin


class PinTests(unittest.TestCase):
    def test_repository_and_commit_must_match(self):
        commit = 'a' * 40
        dependency = {'repo_url': 'con/skills', 'resolved_commit': commit}
        check_pin({'dependencies': [dependency]}, f'con/skills#{commit}')
        for invalid in (None, {}, {'dependencies': None},
                        {'dependencies': [None]},
                        {'dependencies': [dict(dependency, repo_url='fork/skills')]},
                        {'dependencies': [dict(dependency, resolved_commit='b' * 40)]},
                        {'dependencies': [dict(dependency, host='example.com')]}):
            with self.subTest(lock=invalid), self.assertRaises(RuntimeError):
                check_pin(invalid, f'con/skills#{commit}')
