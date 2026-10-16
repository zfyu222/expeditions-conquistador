"""Guard against false Chinese-boundary failures without accepting lost/changed keys."""
import re
import sys
import unittest
sys.path.insert(0, r'D:\StaticHanHua\Tools\localization')
from ainiee_bridge import structural_issues

class IdentifierBoundaryTests(unittest.TestCase):
    def check(self, source, target, regex=r'\bXX\b'):
        return structural_issues(source, target, [('exclusion_2', re.compile(regex))])
    def test_name_adjacent_to_chinese(self):
        self.assertEqual(self.check("XX's Turn", 'XX的回合'), [])
    def test_resource_adjacent_to_chinese(self):
        self.assertEqual(self.check('RationsLost rations', '损失RationsLost份口粮', r'\bRationsLost\b'), [])
    def test_missing_key_rejected(self):
        self.assertIn('exclusion_2', self.check("XX's Turn", '的回合'))
    def test_duplicate_key_rejected(self):
        self.assertIn('exclusion_2', self.check("XX's Turn", 'XX的回合XX'))
    def test_changed_key_rejected(self):
        self.assertIn('exclusion_2', self.check("XX's Turn", 'XXX的回合'))
    def test_added_key_rejected(self):
        self.assertIn('exclusion_2', self.check('Your turn', 'XX的回合'))
    def test_unicode_exclusion_unchanged(self):
        self.assertEqual(self.check(' 名字 ', ' 名字 ', r'\b名字\b'), [])
    def test_newline_loss_still_rejected(self):
        self.assertIn('physical_newlines', self.check("XX\nturn", 'XX的回合'))

if __name__ == '__main__':
    unittest.main()
