# -*- coding: utf-8 -*-

"""
binaryornot.check
-----------------

Main code for checking if a file is binary or text.
"""

import logging
import argparse

from binaryornot.helpers import get_starting_chunk, is_binary_string


logger = logging.getLogger(__name__)


def is_binary(filename):
    """
    :param filename: File to check.
    :returns: True if it's a binary file, otherwise False.
    """
    logger.debug('is_binary: %(filename)r', locals())

    # Check if the file extension is in a list of known binary types
#     binary_extensions = ['.pyc', ]
#     for ext in binary_extensions:
#         if filename.endswith(ext):
#             return True

    # Check if the starting chunk is a binary string
    chunk = get_starting_chunk(filename)
    return is_binary_string(chunk)


def main():
    parser = argparse.ArgumentParser(description="Check if a "
                                                 "file passed as argument is "
                                                 "binary or not")

    parser.add_argument("filename", help="File name to check for. If "
                                         "the file is not in the same folder, "
                                         "include full path")

    args = parser.parse_args()

    print(is_binary(**vars(args)))


if __name__ == "__main__":
    main()
