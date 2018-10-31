# -*- coding: utf-8 -*-
from enzyme.subtitle import Subtitle, _print_time_range, _print_time
import unittest
import os
import io
import requests
import zipfile
import glob

# Test directory
TEST_DIR = os.path.join(os.path.dirname(__file__), os.path.splitext(__file__)[0])

def setUpModule():
    if not os.path.exists(TEST_DIR):
        r = requests.get('http://downloads.sourceforge.net/project/matroska/test_files/matroska_test_w1_1.zip')
        with zipfile.ZipFile(io.BytesIO(r.content), 'r') as f:
            f.extractall(TEST_DIR)

class SubtitleTestCase(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):

        file = 'test5.mkv'
        stream = io.open(os.path.join(TEST_DIR, file), 'rb')
        cls.subtitle = Subtitle(stream)
    
    def test_subtitles_found(self):
        
        subtitles = self.subtitle._subtitles
        self.assertTrue('eng' in subtitles)
        self.assertTrue('hun' in subtitles)
        self.assertTrue('ger' in subtitles)
        self.assertTrue('fre' in subtitles)
        self.assertTrue('spa' in subtitles)
        self.assertTrue('ita' in subtitles)
        self.assertTrue('jpn' in subtitles)
        self.assertTrue('und' in subtitles)

    def test_write_subtitle_to_stream(self):

        subtitle_stream = self.subtitle.write_subtitle_to_stream("eng")
        self.assertIsInstance(subtitle_stream,io.StringIO,"Expecting a StringIO stream")

    def test_write_subtitle_to_stream(self):
        
        subtitle_streams = self.subtitle.write_subtitles_to_stream()
        
        self.assertIn("eng", subtitle_streams, "Expecting a subtitle stream for language eng")
        self.assertIsInstance(subtitle_streams["eng"],io.StringIO,"Expecting a StringIO stream")
        self.assertIn("hun", subtitle_streams, "Expecting a subtitle stream for language hun")
        self.assertIsInstance(subtitle_streams["hun"],io.StringIO,"Expecting a StringIO stream")
        self.assertIn("ger", subtitle_streams, "Expecting a subtitle stream for language ger")
        self.assertIsInstance(subtitle_streams["ger"],io.StringIO,"Expecting a StringIO stream")
        self.assertIn("fre", subtitle_streams, "Expecting a subtitle stream for language fre")
        self.assertIsInstance(subtitle_streams["fre"],io.StringIO,"Expecting a StringIO stream")
        self.assertIn("spa", subtitle_streams, "Expecting a subtitle stream for language spa")
        self.assertIsInstance(subtitle_streams["spa"],io.StringIO,"Expecting a StringIO stream")
        self.assertIn("ita", subtitle_streams, "Expecting a subtitle stream for language ita")
        self.assertIsInstance(subtitle_streams["ita"],io.StringIO,"Expecting a StringIO stream")
        self.assertIn("jpn", subtitle_streams, "Expecting a subtitle stream for language jpn")
        self.assertIsInstance(subtitle_streams["jpn"],io.StringIO,"Expecting a StringIO stream")
        
    def test_print_time(self):
        
        self.assertEqual('0:00:00,0',_print_time(0))
        self.assertEqual('0:00:00,1',_print_time(1))
        self.assertEqual('0:00:00,999',_print_time(999))
        self.assertEqual('0:00:01,0',_print_time(1000))
        self.assertEqual('0:00:59,999',_print_time(1000*60-1))
        self.assertEqual('0:01:00,0',_print_time(1000*60))
        self.assertEqual('0:59:59,999',_print_time(1000*60*60-1))
        self.assertEqual('1:00:00,0',_print_time(1000*60*60))

    def test_print_time_range(self):
        
        self.assertEqual('0:00:00,0 --> 0:00:00,0',_print_time_range(1000000,0,0,0))
        self.assertEqual('0:01:00,0 --> 0:01:01,0',_print_time_range(1000000,0,60000,1000))

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(SubtitleTestCase))
    return suite

if __name__ == '__main__':
    unittest.TextTestRunner().run(suite())
