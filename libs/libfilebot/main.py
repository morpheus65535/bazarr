# coding=utf-8

import subprocess
import sys
import traceback
import logging
import re
import binascii
import types
import os

from pipes import quote
from lib import find_executable

mswindows = False
if sys.platform == "win32":
    mswindows = True
    from pyads import ADS

logger = logging.getLogger(__name__)


def quote_args(seq):
    return ' '.join(quote(arg) for arg in seq)


def win32_xattr(fn):
    handler = ADS(fn)
    try:
        return handler.get_stream_content("net.filebot.filename")
    except IOError:
        pass


def default_xattr(fn):
    if not default_xattr_bin:
        raise Exception("Neither getfattr, attr nor filebot were found")

    if "getfattr" in default_xattr_bin:
        return ["getfattr", "-n", "user.net.filebot.filename", fn]

    elif "attr" in default_xattr_bin:
        return ["attr", "-g", "net.filebot.filename", fn]

    return ["filebot", "-script", "fn:xattr", fn]


XATTR_MAP = {
    "default": (
        default_xattr,
        lambda result: re.search('(?um)(net\.filebot\.filename(?=="|: )[=:" ]+|Attribute.+:\s)([^"\n\r\0]+)',
                                 result).group(2)
    ),
    # "darwin": (
    #     lambda fn: ["xattr", "-p", "net.filebot.filename", fn],
    #     lambda result: binascii.unhexlify(result.strip().replace(' ', '').replace('\r\n', '').replace('\r', '')
    #                                       .replace('\n', '')).strip("\x00")
    # ),
    "darwin": (
        lambda fn: ["filebot", "-script", "fn:xattr", fn],
        lambda result: re.search('(?um)(net\.filebot\.filename(?=="|: )[=:" ]+|Attribute.+:\s)([^"\n\r\0]+)',
                                 result).group(2)
    ),
    "win32": (
        lambda fn: fn,
        win32_xattr,
    )
}

if sys.platform not in XATTR_MAP:
    default_xattr_bin = find_executable("getfattr") or find_executable("attr") or find_executable("filebot") \
                        or "filebot"


def get_filebot_attrs(fn):
    """
    Currently only supports the filebot filename attrs
    :param fn: filename
    :return:
    """

    if sys.platform in XATTR_MAP:
        logger.debug("Using native xattr calls for %s", sys.platform)
    else:
        logger.debug("Using %s for %s", default_xattr_bin, sys.platform)

    args_func, match_func = XATTR_MAP.get(sys.platform, XATTR_MAP["default"])

    args = args_func(fn)
    if isinstance(args, types.ListType):
        try:
            env = dict(os.environ)
            if not mswindows:
                env_path = {"PATH": os.pathsep.join(
                    [
                        "/usr/local/bin",
                        "/usr/bin",
                        "/usr/local/sbin",
                        "/usr/sbin",
                        os.environ.get("PATH", "")
                    ]
                )
                }
                env = dict(os.environ, **env_path)

            env.pop("LD_LIBRARY_PATH", None)

            proc = subprocess.Popen(quote_args(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True,
                                    env=env)
            output, errors = proc.communicate()

            if proc.returncode == 1:
                logger.info(u"%s: Couldn't get filebot original filename, args: %r, output: %r, error: %r", fn, args,
                            output, errors)
                return

            output = output.decode()

        except:
            logger.error(u"%s: Unexpected error while getting filebot original filename: %s", fn,
                             traceback.format_exc())
            return
    else:
        output = args

    try:
        orig_fn = match_func(output)
        return orig_fn.strip()
    except:
        logger.info(u"%s: Couldn't get filebot original filename" % fn)
        logger.debug(u"%s: Result: %r" % (fn, output))


if __name__ == "__main__":
    print get_filebot_attrs(sys.argv[1])
