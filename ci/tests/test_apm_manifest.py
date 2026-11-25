"""Each skill's apm.yml is a valid package manifest and the only place its version and metadata live."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from validate_skills import Result, check_apm_manifest

VALID = ('name: example\nversion: "0.2.0"\ndescription: Short summary for people\n'
         'author: A. Person, B. Person\nlicense: MIT\ntype: skill\n')


def codes(result: Result) -> list[str]:
    return [error.split()[1] for error in result.errors]


class ApmManifestTests(unittest.TestCase):
    def check(self, frontmatter: str, manifest: str | None) -> list[str]:
        with tempfile.TemporaryDirectory() as directory:
            for sibling in ('other', 'empty'):
                (Path(directory) / sibling).mkdir()
            (Path(directory) / 'other' / 'SKILL.md').write_text('---\nname: other\n---\n')
            skill = Path(directory) / 'example'
            skill.mkdir()
            (skill / 'SKILL.md').write_text(f'---\nname: example\ndescription: Example.\n{frontmatter}---\nbody\n')
            if manifest is not None:
                (skill / 'apm.yml').write_text(manifest)
            result = Result()
            check_apm_manifest(skill, result)
            return codes(result)

    def test_valid_manifest(self):
        self.assertEqual(self.check('', VALID), [])
        self.assertEqual(self.check('', VALID + 'dependencies:\n  apm:\n    - path: ../other\n'), [])

    def test_frontmatter_must_not_carry_package_metadata(self):
        for frontmatter in ('version: 0.2.0\n', 'version: 0.3.0\n', 'version:\n',
                            'author: A. Person\n', 'license: MIT\n',
                            'metadata:\n  author: A. Person\n', 'metadata:\n  version: "1.0"\n'):
            with self.subTest(frontmatter=frontmatter):
                self.assertEqual(self.check(frontmatter, VALID), ['E011'])

    def test_invalid_manifests(self):
        for manifest in (None, 'scalar', ': not yaml: [',
                         VALID.replace('name: example', 'name: other'),
                         VALID.replace('"0.2.0"', '1.0'),
                         VALID.replace('"0.2.0"', '"v1.0.0"'),
                         VALID.replace('version: "0.2.0"\n', '')):
            with self.subTest(manifest=manifest):
                self.assertIn('E010', self.check('', manifest))

    def test_invalid_metadata(self):
        for old, new in (('description: Short summary for people\n', ''),
                         ('Short summary for people', 'x' * 101),
                         ('Short summary for people', '|\n  two\n  lines'),
                         ('Short summary for people', 'Example.'),  # copies SKILL.md
                         ('author: A. Person, B. Person\n', ''),
                         ('license: MIT', 'license: Apache-2.0'),
                         ('type: skill', 'type: hybrid')):
            with self.subTest(old=old, new=new):
                self.assertEqual(self.check('', VALID.replace(old, new)), ['E010'])

    def test_invalid_dependencies(self):
        for deps in ('dependencies: [other]\n',
                     'dependencies:\n  mcp: []\n',
                     'dependencies:\n  apm:\n    - con/skills/skills/other\n',
                     'dependencies:\n  apm:\n    - path: ../example\n',
                     'dependencies:\n  apm:\n    - path: ../empty\n',
                     'dependencies:\n  apm:\n    - path: ../missing\n',
                     'dependencies:\n  apm:\n    - path: ../other/sub\n',
                     'dependencies:\n  apm:\n    - path: other\n',
                     'dependencies:\n  apm:\n    - path: ../other\n    - path: ../other\n'):
            with self.subTest(deps=deps):
                self.assertEqual(self.check('', VALID + deps), ['E010'])

