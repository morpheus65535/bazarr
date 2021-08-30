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
        rmtree(module_path, ignore_errors=True)


def set_libs():
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../libs/'))


clean_libs()
set_libs()
