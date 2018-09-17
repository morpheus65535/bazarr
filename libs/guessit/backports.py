#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Backports
"""
# pragma: no-cover
# pylint: disabled

def cmp_to_key(mycmp):
    """functools.cmp_to_key backport"""
    class KeyClass(object):
        """Key class"""
        def __init__(self, obj, *args):  # pylint: disable=unused-argument
            self.obj = obj
        def __lt__(self, other):
            return mycmp(self.obj, other.obj) < 0
        def __gt__(self, other):
            return mycmp(self.obj, other.obj) > 0
        def __eq__(self, other):
            return mycmp(self.obj, other.obj) == 0
        def __le__(self, other):
            return mycmp(self.obj, other.obj) <= 0
        def __ge__(self, other):
            return mycmp(self.obj, other.obj) >= 0
        def __ne__(self, other):
            return mycmp(self.obj, other.obj) != 0
    return KeyClass
