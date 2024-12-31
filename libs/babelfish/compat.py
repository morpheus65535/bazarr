# -*- coding: utf-8 -*-
#
# Copyright (c) 2013 the BabelFish authors. All rights reserved.
# Use of this source code is governed by the 3-clause BSD license
# that can be found in the LICENSE file.
#
from sys import version_info as _python

if _python >= (3, 9):
    # introduced in python 3.9
    from importlib.resources import files
else:
    from importlib_resources import files


if _python >= (3, 10):
    # .select() was introduced in 3.10
    from importlib.metadata import entry_points, EntryPoint as _EntryPoint
else:
    from importlib_metadata import entry_points, EntryPoint as _EntryPoint


def resource_stream(pkg, path):
    return files(pkg).joinpath(f'{path}').open('rb')


def iter_entry_points(group, **kwargs):
    return entry_points().select(group=group, **kwargs)


class EntryPoint(_EntryPoint):
    @staticmethod
    def parse(eps):
        return EntryPoint(*map(str.strip, eps.split('=')), None)

    def resolve(self):
        return self.load()
