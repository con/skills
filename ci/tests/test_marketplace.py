"""The Claude Code marketplace must publish every skill in exactly one plugin."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from validate_skills import MARKETPLACE, check_marketplace


class MarketplaceTests(unittest.TestCase):
    def check(self, plugins, skills=('a', 'b')):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for skill in skills:
                (root / 'skills' / skill).mkdir(parents=True)
                (root / 'skills' / skill / 'SKILL.md').write_text('')
            if plugins is not None:
                (root / MARKETPLACE).parent.mkdir()
                text = plugins if isinstance(plugins, str) else json.dumps({'plugins': plugins})
                (root / MARKETPLACE).write_text(text)
            return [e for e in check_marketplace(root).errors if 'E012' in e]

    def test_valid(self):
        self.assertEqual(self.check(None), [])
        self.assertEqual(self.check([
            {'name': 'one', 'skills': ['./skills/a']},
            {'name': 'two', 'skills': ['./skills/b'], 'dependencies': ['one', 'x@other']},
        ]), [])

    def test_invalid(self):
        both = ['./skills/a', './skills/b']
        for plugins, message in (
            ('not json', 'cannot read'),
            ({'name': 'one'}, 'cannot read'),
            ([{'skills': both}], 'cannot read'),
            ([{'name': 'one', 'skills': both}, {'name': 'one', 'skills': []}], 'more than once'),
            ([{'name': 'one', 'skills': ['./skills/a']}], "'b' is in 0 plugins"),
            ([{'name': 'one', 'skills': both}, {'name': 'two', 'skills': ['./skills/b']}],
             "'b' is in 2 plugins"),
            ([{'name': 'one', 'skills': both + ['./skills/c']}], "lists './skills/c'"),
            ([{'name': 'one', 'skills': ['./skills/a', 'skills/b']}], "lists 'skills/b'"),
            ([{'name': 'one', 'skills': './skills/'}], 'as lists'),
            ([{'name': 'one', 'skills': both, 'dependencies': ['two']}], "depends on 'two'"),
        ):
            with self.subTest(plugins=plugins):
                errors = self.check(plugins)
                self.assertTrue(any(message in e for e in errors), errors)


if __name__ == '__main__':
    unittest.main()
