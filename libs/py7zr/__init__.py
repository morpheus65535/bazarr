#!/usr/bin/env python
#
#    Pure python p7zr implementation
#    Copyright (C) 2019 Hiroshi Miura
#
#    This library is free software; you can redistribute it and/or
#    modify it under the terms of the GNU Lesser General Public
#    License as published by the Free Software Foundation; either
#    version 2.1 of the License, or (at your option) any later version.
#
#    This library is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public
#    License along with this library; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

from pkg_resources import DistributionNotFound, get_distribution

from py7zr.cli import Cli
from py7zr.exceptions import Bad7zFile, DecompressionError, UnsupportedCompressionMethodError
from py7zr.py7zr import ArchiveInfo, FileInfo, SevenZipFile, is_7zfile, pack_7zarchive, unpack_7zarchive

__copyright__ = 'Copyright (C) 2019 Hiroshi Miura'

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    # package is not installed
    __version__ = "unknown"

__all__ = ['__version__', 'ArchiveInfo', 'FileInfo', 'SevenZipFile', 'is_7zfile',
           'UnsupportedCompressionMethodError', 'Bad7zFile', 'DecompressionError',
           'pack_7zarchive', 'unpack_7zarchive']


def main():
    cli = Cli()
    return cli.run()
