"""Regression coverage for malformed metadata and nested Python scripts."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import validate_skills as validate


class ValidatorTests(unittest.TestCase):
    def test_scalar_frontmatter(self):
        with tempfile.TemporaryDirectory() as directory:
            skill = Path(directory)
            (skill / "SKILL.md").write_text("---\nscalar\n---\nbody")
            result = validate.validate_skill(skill)
            self.assertTrue(any("E001" in str(error) for error in result.errors))

    def test_nested_python(self):
        with tempfile.TemporaryDirectory() as directory:
            skill = Path(directory)
            (skill / "SKILL.md").write_text("---\nname: example\ndescription: Example\n---\nbody")
            scripts = skill / "scripts"
            scripts.mkdir()
            (scripts / "broken.py").write_text("def broken(")
            result = validate.validate_skill(skill)
            self.assertTrue(any("E005" in str(error) for error in result.errors))
