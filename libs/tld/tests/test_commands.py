# -*- coding: utf-8 -*-

import logging
import subprocess
import unittest

from .base import internet_available_only

__author__ = "Artur Barseghyan"
__copyright__ = "2013-2026 Artur Barseghyan"
__license__ = "MPL-1.1 OR GPL-2.0-only OR LGPL-2.1-or-later"
__all__ = ("TestCommands",)

LOGGER = logging.getLogger(__name__)


class TestCommands(unittest.TestCase):
    """Tld commands tests."""

    def setUp(self):
        """Set up."""

    @internet_available_only
    def test_update_tld_names_command(self):
        """Test updating the tld names (re-fetch mozilla source)."""
        res = subprocess.check_output(["update-tld-names"]).strip()
        self.assertEqual(res, b"")

    @internet_available_only
    def test_update_tld_names_mozilla_command(self):
        """Test updating the tld names (re-fetch mozilla source)."""
        res = subprocess.check_output(["update-tld-names", "mozilla"]).strip()
        self.assertEqual(res, b"")
