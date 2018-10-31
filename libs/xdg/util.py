import sys

PY3 = sys.version_info[0] >= 3

if PY3:
    def u(s):
        return s
else:
    # Unicode-like literals
    def u(s):
        return s.decode('utf-8')
