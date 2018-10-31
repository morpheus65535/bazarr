# -*- coding: utf-8 -*-
from . import test_mkv, test_parsers, test_subtitle
import unittest


suite = unittest.TestSuite([test_mkv.suite(), test_parsers.suite(), test_subtitle.suite()])




if __name__ == '__main__':
    unittest.TextTestRunner().run(suite)
