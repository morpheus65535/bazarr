#!/usr/bin/python -u
#
# p7zr library
#
# Copyright (c) 2020 Hiroshi Miura <miurahr@linux.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

from abc import ABC, abstractmethod


class Callback(ABC):
    """Abstrat base class for progress callbacks."""

    @abstractmethod
    def report_start_preparation(self):
        """report a start of preparation event such as making list of files and looking into its properties."""
        pass

    @abstractmethod
    def report_start(self, processing_file_path, processing_bytes):
        """report a start event of specified archive file and its input bytes."""
        pass

    @abstractmethod
    def report_end(self, processing_file_path, wrote_bytes):
        """report an end event of specified archive file and its output bytes."""
        pass

    @abstractmethod
    def report_warning(self, message):
        """report an warning event with its message"""
        pass

    @abstractmethod
    def report_postprocess(self):
        """report a start of post processing event such as set file properties and permissions or creating symlinks."""
        pass


class ExtractCallback(Callback):
    """Abstrat base class for extraction progress callbacks."""
    pass


class ArchiveCallback(Callback):
    """Abstrat base class for progress callbacks."""
    pass
