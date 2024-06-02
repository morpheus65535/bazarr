# coding=utf-8
from __future__ import absolute_import
import os
from subzero.lib.io import get_viable_encoding
import six


def get_root_path():
    return os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(six.text_type(__file__, get_viable_encoding()))), ".."))
