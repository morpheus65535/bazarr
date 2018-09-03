import unittest

import six

from langdetect.detector_factory import DetectorFactory
from langdetect.utils.lang_profile import LangProfile


class DetectorTest(unittest.TestCase):
    TRAINING_EN = 'a a a b b c c d e'
    TRAINING_FR = 'a b b c c c d d d'
    TRAINING_JA = six.u('\u3042 \u3042 \u3042 \u3044 \u3046 \u3048 \u3048')
    JSON_LANG1 = '{"freq":{"A":3,"B":6,"C":3,"AB":2,"BC":1,"ABC":2,"BBC":1,"CBA":1},"n_words":[12,3,4],"name":"lang1"}'
    JSON_LANG2 = '{"freq":{"A":6,"B":3,"C":3,"AA":3,"AB":2,"ABC":1,"ABA":1,"CAA":1},"n_words":[12,5,3],"name":"lang2"}'

    def setUp(self):
        self.factory = DetectorFactory()

        profile_en = LangProfile('en')
        for w in self.TRAINING_EN.split():
            profile_en.add(w)
        self.factory.add_profile(profile_en, 0, 3)

        profile_fr = LangProfile('fr')
        for w in self.TRAINING_FR.split():
            profile_fr.add(w)
        self.factory.add_profile(profile_fr, 1, 3)

        profile_ja = LangProfile('ja')
        for w in self.TRAINING_JA.split():
            profile_ja.add(w)
        self.factory.add_profile(profile_ja, 2, 3)

    def test_detector1(self):
        detect = self.factory.create()
        detect.append('a')
        self.assertEqual(detect.detect(), 'en')

    def test_detector2(self):
        detect = self.factory.create()
        detect.append('b d')
        self.assertEqual(detect.detect(), 'fr')

    def test_detector3(self):
        detect = self.factory.create()
        detect.append('d e')
        self.assertEqual(detect.detect(), 'en')

    def test_detector4(self):
        detect = self.factory.create()
        detect.append(six.u('\u3042\u3042\u3042\u3042a'))
        self.assertEqual(detect.detect(), 'ja')

    def test_lang_list(self):
        langlist = self.factory.get_lang_list()
        self.assertEqual(len(langlist), 3)
        self.assertEqual(langlist[0], 'en')
        self.assertEqual(langlist[1], 'fr')
        self.assertEqual(langlist[2], 'ja')

    def test_factory_from_json_string(self):
        self.factory.clear()
        profiles = [self.JSON_LANG1, self.JSON_LANG2]
        self.factory.load_json_profile(profiles)
        langlist = self.factory.get_lang_list()
        self.assertEqual(len(langlist), 2)
        self.assertEqual(langlist[0], 'lang1')
        self.assertEqual(langlist[1], 'lang2')
