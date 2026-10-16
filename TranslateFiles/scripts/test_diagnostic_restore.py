import sys
import unittest
sys.path.insert(0, r'D:\StaticHanHua\Tools\localization')
import ainiee_bridge as bridge
from diagnostic_restore import diagnostic_restore

class DiagnosticTests(unittest.TestCase):
    mapping = [{'original': 'FName1', 'placeholder': '⟪SHH_test_0⟫'},
               {'original': 'FHeShe1', 'placeholder': '⟪SHH_test_1⟫'}]

    def test_valid_matches_strict_restore(self):
        value = '⟪SHH_test_0⟫说，⟪SHH_test_1⟫会回来。'
        restored, issues = diagnostic_restore(value, self.mapping)
        self.assertEqual(issues, [])
        self.assertEqual(restored, bridge.restore(value, self.mapping))

    def test_all_missing_repeated_and_unknown_are_reported(self):
        for value, expected in [('没有姓名或代词', 2),
                                ('⟪SHH_test_0⟫⟪SHH_test_0⟫⟪SHH_fake_2⟫', 3)]:
            _, issues = diagnostic_restore(value, self.mapping)
            self.assertEqual(len(issues), expected)
            with self.assertRaises(ValueError):
                bridge.restore(value, self.mapping)

if __name__ == '__main__':
    unittest.main()
