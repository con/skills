"""Each skill's apm.yml is a valid package manifest and the only place its version lives."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from validate_skills import Result, check_apm_manifest


def codes(result: Result) -> list[str]:
    return [error.split()[1] for error in result.errors]


class ApmManifestTests(unittest.TestCase):
    def check(self, frontmatter: str, manifest: str | None) -> list[str]:
        with tempfile.TemporaryDirectory() as directory:
            skill = Path(directory) / 'example'
            skill.mkdir()
            (skill / 'SKILL.md').write_text(f'---\nname: example\ndescription: Example.\n{frontmatter}---\nbody\n')
            if manifest is not None:
                (skill / 'apm.yml').write_text(manifest)
            result = Result()
            check_apm_manifest(skill, result)
            return codes(result)

    def test_valid_manifest(self):
        self.assertEqual(self.check('', 'name: example\nversion: "0.2.0"\n'), [])

    def test_frontmatter_must_not_carry_a_version(self):
        manifest = 'name: example\nversion: "0.2.0"\n'
        for frontmatter in ('version: 0.2.0\n', 'version: 0.3.0\n', 'version:\n'):
            with self.subTest(frontmatter=frontmatter):
                self.assertEqual(self.check(frontmatter, manifest), ['E011'])

    def test_invalid_manifests(self):
        for manifest in (None, 'scalar', ': not yaml: [',
                         'name: other\nversion: "0.1.0"\ndescription: Example.\n',
                         'name: example\nversion: 1.0\ndescription: Example.\n',
                         'name: example\nversion: "v1.0.0"\ndescription: Example.\n',
                         'name: example\ndescription: Example.\n',
                         ):
            with self.subTest(manifest=manifest):
                self.assertIn('E010', self.check('', manifest))

