from __future__ import unicode_literals

import unittest

import six

import nose

from cherrypy import _cpcompat as compat


class StringTester(unittest.TestCase):

    def test_ntob_non_native(self):
        """
        ntob should raise an Exception on unicode.
        (Python 2 only)

        See #1132 for discussion.
        """
        if six.PY3:
            raise nose.SkipTest('Only useful on Python 2')
        self.assertRaises(Exception, compat.ntob, 'fight')


class EscapeTester(unittest.TestCase):
    """Class to test escape_html function from _cpcompat."""

    def test_escape_quote(self):
        """test_escape_quote - Verify the output for &<>"' chars."""
        self.assertEqual("""xx&amp;&lt;&gt;"aa'""", compat.escape_html("""xx&<>"aa'"""))
