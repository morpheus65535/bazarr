# -*- coding: utf-8 -*-
from . import test_mkv, test_parsers
import unittest


suite = unittest.TestSuite([test_mkv.suite(), test_parsers.suite()])


if __name__ == '__main__':
    unittest.TextTestRunner().run(suite)
