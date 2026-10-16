"""Budget tests use no model, primary DB, source changes or leases."""
import json
import sys
import unittest
sys.path.insert(0, r'D:\StaticHanHua\Tools\localization')
from workflow_quality import QualityMixin

class Budget(QualityMixin):
    def meta(self, db, key, default=None):
        return db.get(key, default)

class ScopedBudgetTests(unittest.TestCase):
    def setUp(self):
        self.flow = Budget()
        self.db = {'pilot_repair_grant': {'task_ids': ['repair'], 'record_ids': ['a','b'],
            'baseline_spent': 6, 'additional_calls': 2, 'authorization': {'human_answer': 'explicit human approval'}}}
    def test_ordinary_budget_stays_six(self):
        self.assertEqual(self.flow.pilot_claim_limit(self.db, {'id':'ordinary','ids':'["a","b"]'},6),6)
    def test_only_authorized_task_has_eight(self):
        self.assertEqual(self.flow.pilot_claim_limit(self.db, {'id':'repair','ids':'["a","b"]'},6),8)
    def test_scope_cannot_expand(self):
        with self.assertRaises(ValueError):
            self.flow.pilot_claim_limit(self.db, {'id':'repair','ids':'["a","b","c"]'},6)
    def test_grant_cannot_add_third_call(self):
        self.db['pilot_repair_grant']['additional_calls'] = 3
        with self.assertRaises(ValueError):
            self.flow.pilot_claim_limit(self.db, {'id':'repair','ids':'["a","b"]'},6)
    def test_no_approval_keeps_six(self):
        self.assertEqual(self.flow.pilot_claim_limit({}, {'id':'repair','ids':'["a","b"]'},6),6)

if __name__ == '__main__':
    unittest.main()
