# coding=utf-8
import os
from subzero.lib.io import get_viable_encoding


def get_root_path():
    return os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(unicode(__file__, get_viable_encoding()))), ".."))
