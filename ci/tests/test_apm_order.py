"""The local consumer lists each skill before the skills it depends on."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from check_apm import ROOT, dependency_order, sibling_dependencies
from skill_common import find_skill_dirs


class DependencyOrderTests(unittest.TestCase):
    def test_dependents_come_first(self):
        names = [p.name for p in find_skill_dirs(ROOT)]
        ordered = dependency_order(names)
        self.assertEqual(sorted(ordered), sorted(names))
        position = {name: index for index, name in enumerate(ordered)}
        for name in names:
            for dependency in sibling_dependencies(ROOT / 'skills' / name):
                with self.subTest(skill=name, dependency=dependency):
                    self.assertLess(position[name], position[dependency])

    def test_skills_outside_the_selection_are_left_out(self):
        selection = ['ts-vuetify-practices', 'ts-practices']
        self.assertEqual(dependency_order(selection), selection)


if __name__ == '__main__':
    unittest.main()
