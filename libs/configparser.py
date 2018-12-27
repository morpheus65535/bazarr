#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Convenience module importing everything from backports.configparser."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


from backports.configparser2 import (
    RawConfigParser,
    ConfigParser,
    SafeConfigParser,
    SectionProxy,

    Interpolation,
    BasicInterpolation,
    ExtendedInterpolation,
    LegacyInterpolation,

    Error,
    NoSectionError,
    DuplicateSectionError,
    DuplicateOptionError,
    NoOptionError,
    InterpolationError,
    InterpolationMissingOptionError,
    InterpolationSyntaxError,
    InterpolationDepthError,
    ParsingError,
    MissingSectionHeaderError,

    _UNSET,
    DEFAULTSECT,
    MAX_INTERPOLATION_DEPTH,
    _default_dict,
    _ChainMap,
)
