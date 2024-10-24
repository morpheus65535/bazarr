# coding=utf-8

import os
import sys

from shutil import rmtree


def set_libs():
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), '../custom_libs/'))


set_libs()
