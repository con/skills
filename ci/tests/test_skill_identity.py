"""Published identity checks use the same discovery and metadata validator."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from skill_common import find_skill_dirs
from validate_skills import Result, check_skill_md


class IdentityTests(unittest.TestCase):
    def test_discovery_and_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill = root / 'skills' / 'example' / 'SKILL.md'
            skill.parent.mkdir(parents=True)
            skill.write_text('---\nname: example\ndescription: Example.\n---\n')
            (root / 'unrelated').mkdir()
            (root / 'unrelated' / 'SKILL.md').write_text('not a published skill')
            self.assertEqual(find_skill_dirs(root), [skill.parent])
            for name in ('example', 'wrong-name', ''):
                with self.subTest(name=name):
                    skill.write_text(f'---\nname: {name}\ndescription: Example.\n---\n')
                    result = Result()
                    check_skill_md(skill, result)
                    self.assertEqual(bool(result.errors), name != 'example')
