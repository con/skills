"""Reject a matching SHA from the wrong source, path, version or malformed lock data."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from check_apm import check_local_versions, check_pin


class PinTests(unittest.TestCase):
    def test_repository_commit_path_and_version_must_match(self):
        commit = 'a' * 40
        dependency = {'repo_url': 'con/skills', 'resolved_commit': commit,
                      'virtual_path': 'skills/example', 'version': '0.2.0'}
        source = f'con/skills#{commit}'
        check_pin({'dependencies': [dependency]}, source, {'example': '0.2.0'})
        for invalid in (None, {}, {'dependencies': None},
                        {'dependencies': [None]},
                        {'dependencies': [dict(dependency, repo_url='fork/skills')]},
                        {'dependencies': [dict(dependency, resolved_commit='b' * 40)]},
                        {'dependencies': [dict(dependency, host='example.com')]},
                        {'dependencies': [dict(dependency, virtual_path=None)]},
                        {'dependencies': [dict(dependency, virtual_path='skills/other')]},
                        {'dependencies': [dict(dependency, version='0.1.0')]}):
            with self.subTest(lock=invalid), self.assertRaises(RuntimeError):
                check_pin(invalid, source, {'example': '0.2.0'})

    def test_local_versions(self):
        lock = {'dependencies': [{'name': 'example', 'version': '0.2.0'}]}
        check_local_versions(lock, {'example': '0.2.0'})
        for versions in ({'example': '0.1.0'}, {'missing': '0.2.0'}):
            with self.subTest(versions=versions), self.assertRaises(RuntimeError):
                check_local_versions(lock, versions)
