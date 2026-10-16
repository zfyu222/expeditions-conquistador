import sys
import unittest
sys.path.insert(0, r'D:\StaticHanHua\Tools\localization')
from ainiee_bridge import normalize_exception_sources

class ExceptionKeysTests(unittest.TestCase):
    def test_case_only_maps_to_matched_key(self):
        src = [{'source':'Waves','reason':'ordinary verb'}]
        out = normalize_exception_sources(src,[{'src':'waves'}],False)
        self.assertEqual(out,[{'source':'waves','reason':'ordinary verb'}])
        self.assertEqual(src[0]['source'],'Waves')
    def test_unrelated_key_not_exempted(self):
        self.assertEqual(normalize_exception_sources([{'source':'charge'}],[{'src':'waves'}],False)[0]['source'],'charge')
    def test_case_sensitive_mode_unchanged(self):
        self.assertEqual(normalize_exception_sources([{'source':'Waves'}],[{'src':'waves'}],True)[0]['source'],'Waves')
    def test_ambiguous_key_not_guessed(self):
        self.assertEqual(normalize_exception_sources([{'source':'WAVES'}],[{'src':'waves'},{'src':'Waves'}],False)[0]['source'],'WAVES')
    def test_non_ascii_not_folded(self):
        self.assertEqual(normalize_exception_sources([{'source':'ß'}],[{'src':'ss'}],False)[0]['source'],'ß')

if __name__ == '__main__':
    unittest.main()
