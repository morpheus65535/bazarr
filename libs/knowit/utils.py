# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import sys
from collections import OrderedDict

from six import PY2, string_types, text_type

from . import VIDEO_EXTENSIONS


def recurse_paths(paths):
    """Return a file system encoded list of videofiles.

    :param paths:
    :type paths: string or list
    :return:
    :rtype: list
    """
    enc_paths = []

    if isinstance(paths, (string_types, text_type)):
        paths = [p.strip() for p in paths.split(',')] if ',' in paths else paths.split()

    encoding = sys.getfilesystemencoding()
    for path in paths:
        if os.path.isfile(path):
            enc_paths.append(path.decode(encoding) if PY2 else path)
        if os.path.isdir(path):
            for root, directories, filenames in os.walk(path):
                for filename in filenames:
                    if os.path.splitext(filename)[1] in VIDEO_EXTENSIONS:
                        if PY2 and os.name == 'nt':
                            fullpath = os.path.join(root, filename.decode(encoding))
                        else:
                            fullpath = os.path.join(root, filename).decode(encoding)
                        enc_paths.append(fullpath)

    # Lets remove any dupes since mediainfo is rather slow.
    seen = set()
    seen_add = seen.add
    return [f for f in enc_paths if not (f in seen or seen_add(f))]


def todict(obj, classkey=None):
    """Transform an object to dict."""
    if isinstance(obj, string_types):
        return obj
    elif isinstance(obj, dict):
        data = {}
        for (k, v) in obj.items():
            data[k] = todict(v, classkey)
        return data
    elif hasattr(obj, '_ast'):
        return todict(obj._ast())
    elif hasattr(obj, '__iter__'):
        return [todict(v, classkey) for v in obj]
    elif hasattr(obj, '__dict__'):
        values = [(key, todict(value, classkey))
                  for key, value in obj.__dict__.items() if not callable(value) and not key.startswith('_')]
        data = OrderedDict([(k, v) for k, v in values if v is not None])
        if classkey is not None and hasattr(obj, '__class__'):
            data[classkey] = obj.__class__.__name__
        return data
    return obj


def detect_os():
    """Detect os family: windows, macos or unix."""
    if os.name in ('nt', 'dos', 'os2', 'ce'):
        return 'windows'
    if sys.platform == 'darwin':
        return 'macos'

    return 'unix'


def define_candidate(locations, names, os_family=None, suggested_path=None):
    """Generate candidate list for the given parameters."""
    os_family = os_family or detect_os()
    for location in (suggested_path, ) + locations[os_family]:
        if not location:
            continue

        if location == '__PATH__':
            for name in names[os_family]:
                yield name
        elif os.path.isfile(location):
            yield location
        elif os.path.isdir(location):
            for name in names[os_family]:
                cmd = os.path.join(location, name)
                if os.path.isfile(cmd):
                    yield cmd
