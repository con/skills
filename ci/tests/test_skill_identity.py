"""Published identity checks use the same discovery and metadata validator."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from skill_common import find_skill_dirs
from validate_skills import Result, check_collection_layout, check_skill_md


class IdentityTests(unittest.TestCase):
    def test_root_level_skill_cannot_silently_escape_packaging_and_scans(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            published = root / 'skills' / 'published' / 'SKILL.md'
            published.parent.mkdir(parents=True)
            published.write_text('---\nname: published\ndescription: Example.\n---\n')
            self.assertEqual(check_collection_layout(root).errors, [])

            misplaced = root / 'new-skill' / 'SKILL.md'
            misplaced.parent.mkdir()
            misplaced.write_text('---\nname: new-skill\ndescription: Example.\n---\n')
            errors = check_collection_layout(root).errors
            self.assertEqual(len(errors), 1)
            self.assertIn('E008', errors[0])
            self.assertIn(str(misplaced), errors[0])

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
