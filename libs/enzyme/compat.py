# -*- coding: utf-8 -*-
import sys


_ver = sys.version_info
is_py3 = _ver[0] == 3
is_py2 = _ver[0] == 2


if is_py2:
    bytes = lambda x: chr(x[0])  # @ReservedAssignment
elif is_py3:
    bytes = bytes  # @ReservedAssignment
