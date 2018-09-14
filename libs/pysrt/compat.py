
import sys

# Syntax sugar.
_ver = sys.version_info

#: Python 2.x?
is_py2 = (_ver[0] == 2)

#: Python 3.x?
is_py3 = (_ver[0] == 3)

from io import open as io_open

if is_py2:
    basestring = basestring
    str = unicode
    open = io_open
elif is_py3:
    basestring = (str, bytes)
    str = str
    open = open
