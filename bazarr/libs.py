# coding=utf-8

from __future__ import absolute_import
import os
import sys


def set_libs():
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../libs/'))


set_libs()
