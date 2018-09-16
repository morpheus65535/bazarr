#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Debug tools.

Can be configured by changing values of those variable.

DEBUG = False
Enable this variable to activate debug features (like defined_at parameters). It can slow down Rebulk

LOG_LEVEL = 0
Default log level of generated rebulk logs.
"""

import inspect
import logging
import os
from collections import namedtuple


DEBUG = False
LOG_LEVEL = logging.DEBUG


class Frame(namedtuple('Frame', ['lineno', 'package', 'name', 'filename'])):
    """
    Stack frame representation.
    """
    __slots__ = ()

    def __repr__(self):
        return "%s#L%s" % (os.path.basename(self.filename), self.lineno)


def defined_at():
    """
    Get definition location of a pattern or a match (outside of rebulk package).
    :return:
    :rtype:
    """
    if DEBUG:
        frame = inspect.currentframe()
        while frame:
            try:
                if frame.f_globals['__package__'] != __package__:
                    break
            except KeyError:  # pragma:no cover
                # If package is missing, consider we are in. Workaround for python 3.3.
                break
            frame = frame.f_back
        ret = Frame(frame.f_lineno,
                    frame.f_globals.get('__package__'),
                    frame.f_globals.get('__name__'),
                    frame.f_code.co_filename)
        del frame
        return ret
