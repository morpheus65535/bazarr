# coding=utf-8
import sys


def fix_environment_stuff(module, base):
    # restore builtins
    module.__builtins__ = [x for x in base.__class__.__base__.__subclasses__() if x.__name__ == 'catch_warnings'][0]()._module.__builtins__

    # patch getfilesystemencoding for NVIDIA Shield
    getfilesystemencoding_orig = sys.getfilesystemencoding

    def getfilesystemencoding():
        return getfilesystemencoding_orig() or "utf-8"

    sys.getfilesystemencoding = getfilesystemencoding
