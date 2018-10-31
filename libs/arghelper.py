#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2014-2016 The arghelper developers. All rights reserved.
# Project site: https://github.com/questrail/arghelper
# Use of this source code is governed by a MIT-style license that
# can be found in the LICENSE.txt file for the project.
"""Provide helper functions for argparse

"""

# Try to future proof code so that it's Python 3.x ready
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import

# Standard module imports
import argparse
import sys
import os


def extant_file(arg):
    """Facade for extant_item(arg, arg_type="file")
    """
    return extant_item(arg, "file")


def extant_dir(arg):
    """Facade for extant_item(arg, arg_type="directory")
    """
    return extant_item(arg, "directory")


def extant_item(arg, arg_type):
    """Determine if parser argument is an existing file or directory.

    This technique comes from http://stackoverflow.com/a/11541450/95592
    and from http://stackoverflow.com/a/11541495/95592

    Args:
        arg: parser argument containing filename to be checked
        arg_type: string of either "file" or "directory"

    Returns:
        If the file exists, return the filename or directory.

    Raises:
        If the file does not exist, raise a parser error.
    """
    if arg_type == "file":
        if not os.path.isfile(arg):
            raise argparse.ArgumentError(
                None,
                "The file {arg} does not exist.".format(arg=arg))
        else:
            # File exists so return the filename
            return arg
    elif arg_type == "directory":
        if not os.path.isdir(arg):
            raise argparse.ArgumentError(
                None,
                "The directory {arg} does not exist.".format(arg=arg))
        else:
            # Directory exists so return the directory name
            return arg


def parse_config_input_output(args=sys.argv):
    """Parse the args using the config_file, input_dir, output_dir pattern

    Args:
        args: sys.argv

    Returns:
        The populated namespace object from parser.parse_args().

    Raises:
        TBD
    """
    parser = argparse.ArgumentParser(
        description='Process the input files using the given config')
    parser.add_argument(
        'config_file',
        help='Configuration file.',
        metavar='FILE', type=extant_file)
    parser.add_argument(
        'input_dir',
        help='Directory containing the input files.',
        metavar='DIR', type=extant_dir)
    parser.add_argument(
        'output_dir',
        help='Directory where the output files should be saved.',
        metavar='DIR', type=extant_dir)
    return parser.parse_args(args[1:])


def parse_config(args=sys.argv):
    """Parse the args using the config_file pattern

    Args:
        args: sys.argv

    Returns:
        The populated namespace object from parser.parse_args().

    Raises:
        TBD
    """
    parser = argparse.ArgumentParser(
        description='Read in the config file')
    parser.add_argument(
        'config_file',
        help='Configuration file.',
        metavar='FILE', type=extant_file)
    return parser.parse_args(args[1:])
