# coding=utf-8

import os
import sys
from shutil import rmtree


def clean_libs():
    libs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'libs')

    # Delete the old module almost empty directory compatible only with Python 2.7.x that cause bad magic number error
    # if they are present in Python 3.x.
    module_list = ['enum', 'concurrent']
    for module in module_list:
        module_path = os.path.join(libs_dir, module)
        if os.path.isdir(module_path):
            rmtree(module_path)


def set_libs():
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../libs/'))
    from six import PY3
    if PY3:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../libs3/'))
    else:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../libs2/'))


clean_libs()
set_libs()
