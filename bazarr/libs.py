# coding=utf-8

import os
import sys


def set_libs():
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../libs/'))
    from six import PY3
    if PY3:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../libs3/'))
    else:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../libs2/'))


set_libs()
