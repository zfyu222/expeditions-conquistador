import copy
import sys
import unittest
sys.path.insert(0, r'D:\StaticHanHua\Tools\localization')
from ainiee_bridge import matched_terms

class FrozenMatcherTests(unittest.TestCase):
    def match(self, terms, text):
        return matched_terms({'terms':terms},[text],{'case_sensitive':False,'whole_word':True})
    def test_plural_role_does_not_overwrite_singular_skill(self):
        terms=[{'source':'Guards','recommended_translation':'卫兵'}, {'source':'Guard','recommended_translation':'防守'}]
        original=copy.deepcopy(terms)
        rows=self.match(terms,'Guards use Guard.')
        self.assertEqual({r['src']:r['dst'] for r in rows},{'Guards':'卫兵','Guard':'防守'})
        self.assertEqual(terms,original)
    def test_article_name_does_not_rewrite_other_entry(self):
        terms=[{'source':'The Red','recommended_translation':'红毛'}, {'source':'Red','recommended_translation':'红色'}]
        self.assertEqual({r['src']:r['dst'] for r in self.match(terms,'The Red chose Red.')}, {'The Red':'红毛','Red':'红色'})
    def test_keep_original_family_does_not_suppress_translated_plural(self):
        terms=[{'source':'Attack','recommended_translation':'保留原文'}, {'source':'Attacks','recommended_translation':'多次攻击'}]
        self.assertEqual({r['src']:r['dst'] for r in self.match(terms,'Attack Attacks')}, {'Attack':'保留原文','Attacks':'多次攻击'})
    def test_longer_overlap_still_wins(self):
        terms=[{'source':'Red','recommended_translation':'红色'}, {'source':'The Red','recommended_translation':'红毛'}]
        self.assertEqual([(r['src'],r['dst']) for r in self.match(terms,'The Red')],[('The Red','红毛')])

if __name__ == '__main__':
    unittest.main()
