import unittest

from langdetect.language import Language


class LanguageTest(unittest.TestCase):
    def test_language(self):
        lang = Language(None, 0)
        self.assertTrue(lang.lang is None)
        self.assertEqual(lang.prob, 0.0, 0.0001)
        self.assertEqual(str(lang), '')

        lang2 = Language('en', 1.0)
        self.assertEqual(lang2.lang, 'en')
        self.assertEqual(lang2.prob, 1.0, 0.0001)
        self.assertEqual(str(lang2), 'en:1.0')

    def test_cmp(self):
        lang1 = Language('a', 0.1)
        lang2 = Language('b', 0.5)

        self.assertTrue(lang1 < lang2)
        self.assertFalse(lang1 == lang2)
        self.assertFalse(lang1 > lang1)
