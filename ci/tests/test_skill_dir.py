"""SKILL_DIR references must resolve inside the skill that uses them."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from validate_skills import SKILL_DIR_DEFINITION, Result, check_skill_md


class SkillDirTests(unittest.TestCase):
    def check(self, body):
        with tempfile.TemporaryDirectory() as directory:
            skill = Path(directory) / 'example'
            (skill / 'scripts').mkdir(parents=True)
            (skill / 'scripts' / 'run.py').write_text('')
            (Path(directory) / 'other').mkdir()
            (Path(directory) / 'other' / 'run.py').write_text('')
            (skill / 'scripts' / 'outside.py').symlink_to(Path(directory) / 'other' / 'run.py')
            (skill / 'SKILL.md').write_text(
                f'---\nname: example\ndescription: Example.\n---\n{body}\n')
            result = Result()
            check_skill_md(skill / 'SKILL.md', result)
            return [e for e in result.errors if 'E009' in e]

    def test_references(self):
        defined = SKILL_DIR_DEFINITION + '.\n'
        self.assertEqual(self.check('No bundled files.'), [])
        self.assertEqual(self.check(defined + 'python3 SKILL_DIR/scripts/run.py --x'), [])
        self.assertEqual(self.check(defined + 'Run `SKILL_DIR/scripts/run.py`.'), [])
        for body in ('python3 SKILL_DIR/scripts/run.py',
                     defined + 'python3 SKILL_DIR/missing.py',
                     defined + 'python3 SKILL_DIR/scripts',
                     defined + 'python3 SKILL_DIR/../other/run.py',
                     defined + 'python3 SKILL_DIR/scripts/outside.py'):
            with self.subTest(body=body):
                self.assertEqual(len(self.check(body)), 1)
