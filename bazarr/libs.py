# coding=utf-8

import os
import sys


def set_libs():
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../libs/'))


set_libs()
