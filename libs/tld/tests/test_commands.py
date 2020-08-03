# -*- coding: utf-8 -*-

import logging
import unittest

import subprocess

from .base import log_info, internet_available_only

__author__ = 'Artur Barseghyan'
__copyright__ = '2013-2020 Artur Barseghyan'
__license__ = 'GPL 2.0/LGPL 2.1'
__all__ = ('TestCommands',)

LOGGER = logging.getLogger(__name__)


class TestCommands(unittest.TestCase):
    """Tld commands tests."""

    def setUp(self):
        """Set up."""

    @internet_available_only
    @log_info
    def test_1_update_tld_names_command(self):
        """Test updating the tld names (re-fetch mozilla source)."""
        res = subprocess.check_output(['update-tld-names']).strip()
        self.assertEqual(res, b'')
        return res

    @internet_available_only
    @log_info
    def test_1_update_tld_names_mozilla_command(self):
        """Test updating the tld names (re-fetch mozilla source)."""
        res = subprocess.check_output(['update-tld-names', 'mozilla']).strip()
        self.assertEqual(res, b'')
        return res


if __name__ == '__main__':
    unittest.main()
