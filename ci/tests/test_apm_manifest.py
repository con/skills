"""Each skill's apm.yml is a valid package manifest and agrees with its frontmatter."""
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

    def test_valid_manifest_with_and_without_frontmatter_version(self):
        manifest = 'name: example\nversion: "0.2.0"\ndescription: Example.\ntype: skill\n'
        self.assertEqual(self.check('', manifest), [])
        self.assertEqual(self.check('version: 0.2.0\n', manifest), [])

    def test_frontmatter_and_manifest_versions_must_agree(self):
        manifest = 'name: example\nversion: "0.2.0"\ndescription: Example.\n'
        self.assertEqual(self.check('version: 0.3.0\n', manifest), ['E011'])

    def test_invalid_manifests(self):
        for manifest in (None, 'scalar', ': not yaml: [',
                         'name: other\nversion: "0.1.0"\ndescription: Example.\n',
                         'name: example\nversion: 1.0\ndescription: Example.\n',
                         'name: example\nversion: "v1.0.0"\ndescription: Example.\n',
                         'name: example\ndescription: Example.\n',
                         'name: example\nversion: "0.1.0"\ndescription: ""\n'):
            with self.subTest(manifest=manifest):
                self.assertIn('E010', self.check('version: 0.1.0\n', manifest))


class CollectionTests(unittest.TestCase):
    def test_every_published_skill_has_a_valid_manifest(self):
        from skill_common import find_skill_dirs
        root = Path(__file__).resolve().parents[2]
        for skill in find_skill_dirs(root):
            with self.subTest(skill=skill.name):
                result = Result()
                check_apm_manifest(skill, result)
                self.assertEqual(result.errors, [])
