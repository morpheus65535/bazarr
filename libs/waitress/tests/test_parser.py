##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""HTTP Request Parser tests
"""
import unittest

from waitress.compat import text_, tobytes


class TestHTTPRequestParser(unittest.TestCase):
    def setUp(self):
        from waitress.parser import HTTPRequestParser
        from waitress.adjustments import Adjustments

        my_adj = Adjustments()
        self.parser = HTTPRequestParser(my_adj)

    def test_get_body_stream_None(self):
        self.parser.body_recv = None
        result = self.parser.get_body_stream()
        self.assertEqual(result.getvalue(), b"")

    def test_get_body_stream_nonNone(self):
        body_rcv = DummyBodyStream()
        self.parser.body_rcv = body_rcv
        result = self.parser.get_body_stream()
        self.assertEqual(result, body_rcv)

    def test_received_get_no_headers(self):
        data = b"HTTP/1.0 GET /foobar\r\n\r\n"
        result = self.parser.received(data)
        self.assertEqual(result, 24)
        self.assertTrue(self.parser.completed)
        self.assertEqual(self.parser.headers, {})

    def test_received_bad_host_header(self):
        from waitress.utilities import BadRequest

        data = b"HTTP/1.0 GET /foobar\r\n Host: foo\r\n\r\n"
        result = self.parser.received(data)
        self.assertEqual(result, 36)
        self.assertTrue(self.parser.completed)
        self.assertEqual(self.parser.error.__class__, BadRequest)

    def test_received_bad_transfer_encoding(self):
        from waitress.utilities import ServerNotImplemented

        data = (
            b"GET /foobar HTTP/1.1\r\n"
            b"Transfer-Encoding: foo\r\n"
            b"\r\n"
            b"1d;\r\n"
            b"This string has 29 characters\r\n"
            b"0\r\n\r\n"
        )
        result = self.parser.received(data)
        self.assertEqual(result, 48)
        self.assertTrue(self.parser.completed)
        self.assertEqual(self.parser.error.__class__, ServerNotImplemented)

    def test_received_nonsense_nothing(self):
        data = b"\r\n\r\n"
        result = self.parser.received(data)
        self.assertEqual(result, 4)
        self.assertTrue(self.parser.completed)
        self.assertEqual(self.parser.headers, {})

    def test_received_no_doublecr(self):
        data = b"GET /foobar HTTP/8.4\r\n"
        result = self.parser.received(data)
        self.assertEqual(result, 22)
        self.assertFalse(self.parser.completed)
        self.assertEqual(self.parser.headers, {})

    def test_received_already_completed(self):
        self.parser.completed = True
        result = self.parser.received(b"a")
        self.assertEqual(result, 0)

    def test_received_cl_too_large(self):
        from waitress.utilities import RequestEntityTooLarge

        self.parser.adj.max_request_body_size = 2
        data = b"GET /foobar HTTP/8.4\r\nContent-Length: 10\r\n\r\n"
        result = self.parser.received(data)
        self.assertEqual(result, 44)
        self.assertTrue(self.parser.completed)
        self.assertTrue(isinstance(self.parser.error, RequestEntityTooLarge))

    def test_received_headers_too_large(self):
        from waitress.utilities import RequestHeaderFieldsTooLarge

        self.parser.adj.max_request_header_size = 2
        data = b"GET /foobar HTTP/8.4\r\nX-Foo: 1\r\n\r\n"
        result = self.parser.received(data)
        self.assertEqual(result, 34)
        self.assertTrue(self.parser.completed)
        self.assertTrue(isinstance(self.parser.error, RequestHeaderFieldsTooLarge))

    def test_received_body_too_large(self):
        from waitress.utilities import RequestEntityTooLarge

        self.parser.adj.max_request_body_size = 2
        data = (
            b"GET /foobar HTTP/1.1\r\n"
            b"Transfer-Encoding: chunked\r\n"
            b"X-Foo: 1\r\n"
            b"\r\n"
            b"1d;\r\n"
            b"This string has 29 characters\r\n"
            b"0\r\n\r\n"
        )

        result = self.parser.received(data)
        self.assertEqual(result, 62)
        self.parser.received(data[result:])
        self.assertTrue(self.parser.completed)
        self.assertTrue(isinstance(self.parser.error, RequestEntityTooLarge))

    def test_received_error_from_parser(self):
        from waitress.utilities import BadRequest

        data = (
            b"GET /foobar HTTP/1.1\r\n"
            b"Transfer-Encoding: chunked\r\n"
            b"X-Foo: 1\r\n"
            b"\r\n"
            b"garbage\r\n"
        )
        # header
        result = self.parser.received(data)
        # body
        result = self.parser.received(data[result:])
        self.assertEqual(result, 9)
        self.assertTrue(self.parser.completed)
        self.assertTrue(isinstance(self.parser.error, BadRequest))

    def test_received_chunked_completed_sets_content_length(self):
        data = (
            b"GET /foobar HTTP/1.1\r\n"
            b"Transfer-Encoding: chunked\r\n"
            b"X-Foo: 1\r\n"
            b"\r\n"
            b"1d;\r\n"
            b"This string has 29 characters\r\n"
            b"0\r\n\r\n"
        )
        result = self.parser.received(data)
        self.assertEqual(result, 62)
        data = data[result:]
        result = self.parser.received(data)
        self.assertTrue(self.parser.completed)
        self.assertTrue(self.parser.error is None)
        self.assertEqual(self.parser.headers["CONTENT_LENGTH"], "29")

    def test_parse_header_gardenpath(self):
        data = b"GET /foobar HTTP/8.4\r\nfoo: bar\r\n"
        self.parser.parse_header(data)
        self.assertEqual(self.parser.first_line, b"GET /foobar HTTP/8.4")
        self.assertEqual(self.parser.headers["FOO"], "bar")

    def test_parse_header_no_cr_in_headerplus(self):
        from waitress.parser import ParsingError

        data = b"GET /foobar HTTP/8.4"

        try:
            self.parser.parse_header(data)
        except ParsingError:
            pass
        else:  # pragma: nocover
            self.assertTrue(False)

    def test_parse_header_bad_content_length(self):
        from waitress.parser import ParsingError

        data = b"GET /foobar HTTP/8.4\r\ncontent-length: abc\r\n"

        try:
            self.parser.parse_header(data)
        except ParsingError as e:
            self.assertIn("Content-Length is invalid", e.args[0])
        else:  # pragma: nocover
            self.assertTrue(False)

    def test_parse_header_multiple_content_length(self):
        from waitress.parser import ParsingError

        data = b"GET /foobar HTTP/8.4\r\ncontent-length: 10\r\ncontent-length: 20\r\n"

        try:
            self.parser.parse_header(data)
        except ParsingError as e:
            self.assertIn("Content-Length is invalid", e.args[0])
        else:  # pragma: nocover
            self.assertTrue(False)

    def test_parse_header_11_te_chunked(self):
        # NB: test that capitalization of header value is unimportant
        data = b"GET /foobar HTTP/1.1\r\ntransfer-encoding: ChUnKed\r\n"
        self.parser.parse_header(data)
        self.assertEqual(self.parser.body_rcv.__class__.__name__, "ChunkedReceiver")

    def test_parse_header_transfer_encoding_invalid(self):
        from waitress.parser import TransferEncodingNotImplemented

        data = b"GET /foobar HTTP/1.1\r\ntransfer-encoding: gzip\r\n"

        try:
            self.parser.parse_header(data)
        except TransferEncodingNotImplemented as e:
            self.assertIn("Transfer-Encoding requested is not supported.", e.args[0])
        else:  # pragma: nocover
            self.assertTrue(False)

    def test_parse_header_transfer_encoding_invalid_multiple(self):
        from waitress.parser import TransferEncodingNotImplemented

        data = b"GET /foobar HTTP/1.1\r\ntransfer-encoding: gzip\r\ntransfer-encoding: chunked\r\n"

        try:
            self.parser.parse_header(data)
        except TransferEncodingNotImplemented as e:
            self.assertIn("Transfer-Encoding requested is not supported.", e.args[0])
        else:  # pragma: nocover
            self.assertTrue(False)

    def test_parse_header_transfer_encoding_invalid_whitespace(self):
        from waitress.parser import TransferEncodingNotImplemented

        data = b"GET /foobar HTTP/1.1\r\nTransfer-Encoding:\x85chunked\r\n"

        try:
            self.parser.parse_header(data)
        except TransferEncodingNotImplemented as e:
            self.assertIn("Transfer-Encoding requested is not supported.", e.args[0])
        else:  # pragma: nocover
            self.assertTrue(False)

    def test_parse_header_transfer_encoding_invalid_unicode(self):
        from waitress.parser import TransferEncodingNotImplemented

        # This is the binary encoding for the UTF-8 character
        # https://www.compart.com/en/unicode/U+212A "unicode character "K""
        # which if waitress were to accidentally do the wrong thing get
        # lowercased to just the ascii "k" due to unicode collisions during
        # transformation
        data = b"GET /foobar HTTP/1.1\r\nTransfer-Encoding: chun\xe2\x84\xaaed\r\n"

        try:
            self.parser.parse_header(data)
        except TransferEncodingNotImplemented as e:
            self.assertIn("Transfer-Encoding requested is not supported.", e.args[0])
        else:  # pragma: nocover
            self.assertTrue(False)

    def test_parse_header_11_expect_continue(self):
        data = b"GET /foobar HTTP/1.1\r\nexpect: 100-continue\r\n"
        self.parser.parse_header(data)
        self.assertEqual(self.parser.expect_continue, True)

    def test_parse_header_connection_close(self):
        data = b"GET /foobar HTTP/1.1\r\nConnection: close\r\n"
        self.parser.parse_header(data)
        self.assertEqual(self.parser.connection_close, True)

    def test_close_with_body_rcv(self):
        body_rcv = DummyBodyStream()
        self.parser.body_rcv = body_rcv
        self.parser.close()
        self.assertTrue(body_rcv.closed)

    def test_close_with_no_body_rcv(self):
        self.parser.body_rcv = None
        self.parser.close()  # doesn't raise

    def test_parse_header_lf_only(self):
        from waitress.parser import ParsingError

        data = b"GET /foobar HTTP/8.4\nfoo: bar"

        try:
            self.parser.parse_header(data)
        except ParsingError:
            pass
        else:  # pragma: nocover
            self.assertTrue(False)

    def test_parse_header_cr_only(self):
        from waitress.parser import ParsingError

        data = b"GET /foobar HTTP/8.4\rfoo: bar"
        try:
            self.parser.parse_header(data)
        except ParsingError:
            pass
        else:  # pragma: nocover
            self.assertTrue(False)

    def test_parse_header_extra_lf_in_header(self):
        from waitress.parser import ParsingError

        data = b"GET /foobar HTTP/8.4\r\nfoo: \nbar\r\n"
        try:
            self.parser.parse_header(data)
        except ParsingError as e:
            self.assertIn("Bare CR or LF found in header line", e.args[0])
        else:  # pragma: nocover
            self.assertTrue(False)

    def test_parse_header_extra_lf_in_first_line(self):
        from waitress.parser import ParsingError

        data = b"GET /foobar\n HTTP/8.4\r\n"
        try:
            self.parser.parse_header(data)
        except ParsingError as e:
            self.assertIn("Bare CR or LF found in HTTP message", e.args[0])
        else:  # pragma: nocover
            self.assertTrue(False)

    def test_parse_header_invalid_whitespace(self):
        from waitress.parser import ParsingError

        data = b"GET /foobar HTTP/8.4\r\nfoo : bar\r\n"
        try:
            self.parser.parse_header(data)
        except ParsingError as e:
            self.assertIn("Invalid header", e.args[0])
        else:  # pragma: nocover
            self.assertTrue(False)

    def test_parse_header_invalid_whitespace_vtab(self):
        from waitress.parser import ParsingError

        data = b"GET /foobar HTTP/1.1\r\nfoo:\x0bbar\r\n"
        try:
            self.parser.parse_header(data)
        except ParsingError as e:
            self.assertIn("Invalid header", e.args[0])
        else:  # pragma: nocover
            self.assertTrue(False)

    def test_parse_header_invalid_no_colon(self):
        from waitress.parser import ParsingError

        data = b"GET /foobar HTTP/1.1\r\nfoo: bar\r\nnotvalid\r\n"
        try:
            self.parser.parse_header(data)
        except ParsingError as e:
            self.assertIn("Invalid header", e.args[0])
        else:  # pragma: nocover
            self.assertTrue(False)

    def test_parse_header_invalid_folding_spacing(self):
        from waitress.parser import ParsingError

        data = b"GET /foobar HTTP/1.1\r\nfoo: bar\r\n\t\x0bbaz\r\n"
        try:
            self.parser.parse_header(data)
        except ParsingError as e:
            self.assertIn("Invalid header", e.args[0])
        else:  # pragma: nocover
            self.assertTrue(False)

    def test_parse_header_invalid_chars(self):
        from waitress.parser import ParsingError

        data = b"GET /foobar HTTP/1.1\r\nfoo: bar\r\nfoo: \x0bbaz\r\n"
        try:
            self.parser.parse_header(data)
        except ParsingError as e:
            self.assertIn("Invalid header", e.args[0])
        else:  # pragma: nocover
            self.assertTrue(False)

    def test_parse_header_empty(self):
        from waitress.parser import ParsingError

        data = b"GET /foobar HTTP/1.1\r\nfoo: bar\r\nempty:\r\n"
        self.parser.parse_header(data)

        self.assertIn("EMPTY", self.parser.headers)
        self.assertIn("FOO", self.parser.headers)
        self.assertEqual(self.parser.headers["EMPTY"], "")
        self.assertEqual(self.parser.headers["FOO"], "bar")

    def test_parse_header_multiple_values(self):
        from waitress.parser import ParsingError

        data = b"GET /foobar HTTP/1.1\r\nfoo: bar, whatever, more, please, yes\r\n"
        self.parser.parse_header(data)

        self.assertIn("FOO", self.parser.headers)
        self.assertEqual(self.parser.headers["FOO"], "bar, whatever, more, please, yes")

    def test_parse_header_multiple_values_header_folded(self):
        from waitress.parser import ParsingError

        data = b"GET /foobar HTTP/1.1\r\nfoo: bar, whatever,\r\n more, please, yes\r\n"
        self.parser.parse_header(data)

        self.assertIn("FOO", self.parser.headers)
        self.assertEqual(self.parser.headers["FOO"], "bar, whatever, more, please, yes")

    def test_parse_header_multiple_values_header_folded_multiple(self):
        from waitress.parser import ParsingError

        data = b"GET /foobar HTTP/1.1\r\nfoo: bar, whatever,\r\n more\r\nfoo: please, yes\r\n"
        self.parser.parse_header(data)

        self.assertIn("FOO", self.parser.headers)
        self.assertEqual(self.parser.headers["FOO"], "bar, whatever, more, please, yes")

    def test_parse_header_multiple_values_extra_space(self):
        # Tests errata from: https://www.rfc-editor.org/errata_search.php?rfc=7230&eid=4189
        from waitress.parser import ParsingError

        data = b"GET /foobar HTTP/1.1\r\nfoo: abrowser/0.001 (C O M M E N T)\r\n"
        self.parser.parse_header(data)

        self.assertIn("FOO", self.parser.headers)
        self.assertEqual(self.parser.headers["FOO"], "abrowser/0.001 (C O M M E N T)")

    def test_parse_header_invalid_backtrack_bad(self):
        from waitress.parser import ParsingError

        data = b"GET /foobar HTTP/1.1\r\nfoo: bar\r\nfoo: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx\x10\r\n"
        try:
            self.parser.parse_header(data)
        except ParsingError as e:
            self.assertIn("Invalid header", e.args[0])
        else:  # pragma: nocover
            self.assertTrue(False)

    def test_parse_header_short_values(self):
        from waitress.parser import ParsingError

        data = b"GET /foobar HTTP/1.1\r\none: 1\r\ntwo: 22\r\n"
        self.parser.parse_header(data)

        self.assertIn("ONE", self.parser.headers)
        self.assertIn("TWO", self.parser.headers)
        self.assertEqual(self.parser.headers["ONE"], "1")
        self.assertEqual(self.parser.headers["TWO"], "22")


class Test_split_uri(unittest.TestCase):
    def _callFUT(self, uri):
        from waitress.parser import split_uri

        (
            self.proxy_scheme,
            self.proxy_netloc,
            self.path,
            self.query,
            self.fragment,
        ) = split_uri(uri)

    def test_split_uri_unquoting_unneeded(self):
        self._callFUT(b"http://localhost:8080/abc def")
        self.assertEqual(self.path, "/abc def")

    def test_split_uri_unquoting_needed(self):
        self._callFUT(b"http://localhost:8080/abc%20def")
        self.assertEqual(self.path, "/abc def")

    def test_split_url_with_query(self):
        self._callFUT(b"http://localhost:8080/abc?a=1&b=2")
        self.assertEqual(self.path, "/abc")
        self.assertEqual(self.query, "a=1&b=2")

    def test_split_url_with_query_empty(self):
        self._callFUT(b"http://localhost:8080/abc?")
        self.assertEqual(self.path, "/abc")
        self.assertEqual(self.query, "")

    def test_split_url_with_fragment(self):
        self._callFUT(b"http://localhost:8080/#foo")
        self.assertEqual(self.path, "/")
        self.assertEqual(self.fragment, "foo")

    def test_split_url_https(self):
        self._callFUT(b"https://localhost:8080/")
        self.assertEqual(self.path, "/")
        self.assertEqual(self.proxy_scheme, "https")
        self.assertEqual(self.proxy_netloc, "localhost:8080")

    def test_split_uri_unicode_error_raises_parsing_error(self):
        # See https://github.com/Pylons/waitress/issues/64
        from waitress.parser import ParsingError

        # Either pass or throw a ParsingError, just don't throw another type of
        # exception as that will cause the connection to close badly:
        try:
            self._callFUT(b"/\xd0")
        except ParsingError:
            pass

    def test_split_uri_path(self):
        self._callFUT(b"//testing/whatever")
        self.assertEqual(self.path, "//testing/whatever")
        self.assertEqual(self.proxy_scheme, "")
        self.assertEqual(self.proxy_netloc, "")
        self.assertEqual(self.query, "")
        self.assertEqual(self.fragment, "")

    def test_split_uri_path_query(self):
        self._callFUT(b"//testing/whatever?a=1&b=2")
        self.assertEqual(self.path, "//testing/whatever")
        self.assertEqual(self.proxy_scheme, "")
        self.assertEqual(self.proxy_netloc, "")
        self.assertEqual(self.query, "a=1&b=2")
        self.assertEqual(self.fragment, "")

    def test_split_uri_path_query_fragment(self):
        self._callFUT(b"//testing/whatever?a=1&b=2#fragment")
        self.assertEqual(self.path, "//testing/whatever")
        self.assertEqual(self.proxy_scheme, "")
        self.assertEqual(self.proxy_netloc, "")
        self.assertEqual(self.query, "a=1&b=2")
        self.assertEqual(self.fragment, "fragment")


class Test_get_header_lines(unittest.TestCase):
    def _callFUT(self, data):
        from waitress.parser import get_header_lines

        return get_header_lines(data)

    def test_get_header_lines(self):
        result = self._callFUT(b"slam\r\nslim")
        self.assertEqual(result, [b"slam", b"slim"])

    def test_get_header_lines_folded(self):
        # From RFC2616:
        # HTTP/1.1 header field values can be folded onto multiple lines if the
        # continuation line begins with a space or horizontal tab. All linear
        # white space, including folding, has the same semantics as SP. A
        # recipient MAY replace any linear white space with a single SP before
        # interpreting the field value or forwarding the message downstream.

        # We are just preserving the whitespace that indicates folding.
        result = self._callFUT(b"slim\r\n slam")
        self.assertEqual(result, [b"slim slam"])

    def test_get_header_lines_tabbed(self):
        result = self._callFUT(b"slam\r\n\tslim")
        self.assertEqual(result, [b"slam\tslim"])

    def test_get_header_lines_malformed(self):
        # https://corte.si/posts/code/pathod/pythonservers/index.html
        from waitress.parser import ParsingError

        self.assertRaises(ParsingError, self._callFUT, b" Host: localhost\r\n\r\n")


class Test_crack_first_line(unittest.TestCase):
    def _callFUT(self, line):
        from waitress.parser import crack_first_line

        return crack_first_line(line)

    def test_crack_first_line_matchok(self):
        result = self._callFUT(b"GET / HTTP/1.0")
        self.assertEqual(result, (b"GET", b"/", b"1.0"))

    def test_crack_first_line_lowercase_method(self):
        from waitress.parser import ParsingError

        self.assertRaises(ParsingError, self._callFUT, b"get / HTTP/1.0")

    def test_crack_first_line_nomatch(self):
        result = self._callFUT(b"GET / bleh")
        self.assertEqual(result, (b"", b"", b""))

        result = self._callFUT(b"GET /info?txtAirPlay&txtRAOP RTSP/1.0")
        self.assertEqual(result, (b"", b"", b""))

    def test_crack_first_line_missing_version(self):
        result = self._callFUT(b"GET /")
        self.assertEqual(result, (b"GET", b"/", b""))


class TestHTTPRequestParserIntegration(unittest.TestCase):
    def setUp(self):
        from waitress.parser import HTTPRequestParser
        from waitress.adjustments import Adjustments

        my_adj = Adjustments()
        self.parser = HTTPRequestParser(my_adj)

    def feed(self, data):
        parser = self.parser

        for n in range(100):  # make sure we never loop forever
            consumed = parser.received(data)
            data = data[consumed:]

            if parser.completed:
                return
        raise ValueError("Looping")  # pragma: no cover

    def testSimpleGET(self):
        data = (
            b"GET /foobar HTTP/8.4\r\n"
            b"FirstName: mickey\r\n"
            b"lastname: Mouse\r\n"
            b"content-length: 6\r\n"
            b"\r\n"
            b"Hello."
        )
        parser = self.parser
        self.feed(data)
        self.assertTrue(parser.completed)
        self.assertEqual(parser.version, "8.4")
        self.assertFalse(parser.empty)
        self.assertEqual(
            parser.headers,
            {"FIRSTNAME": "mickey", "LASTNAME": "Mouse", "CONTENT_LENGTH": "6",},
        )
        self.assertEqual(parser.path, "/foobar")
        self.assertEqual(parser.command, "GET")
        self.assertEqual(parser.query, "")
        self.assertEqual(parser.proxy_scheme, "")
        self.assertEqual(parser.proxy_netloc, "")
        self.assertEqual(parser.get_body_stream().getvalue(), b"Hello.")

    def testComplexGET(self):
        data = (
            b"GET /foo/a+%2B%2F%C3%A4%3D%26a%3Aint?d=b+%2B%2F%3D%26b%3Aint&c+%2B%2F%3D%26c%3Aint=6 HTTP/8.4\r\n"
            b"FirstName: mickey\r\n"
            b"lastname: Mouse\r\n"
            b"content-length: 10\r\n"
            b"\r\n"
            b"Hello mickey."
        )
        parser = self.parser
        self.feed(data)
        self.assertEqual(parser.command, "GET")
        self.assertEqual(parser.version, "8.4")
        self.assertFalse(parser.empty)
        self.assertEqual(
            parser.headers,
            {"FIRSTNAME": "mickey", "LASTNAME": "Mouse", "CONTENT_LENGTH": "10"},
        )
        # path should be utf-8 encoded
        self.assertEqual(
            tobytes(parser.path).decode("utf-8"),
            text_(b"/foo/a++/\xc3\xa4=&a:int", "utf-8"),
        )
        self.assertEqual(
            parser.query, "d=b+%2B%2F%3D%26b%3Aint&c+%2B%2F%3D%26c%3Aint=6"
        )
        self.assertEqual(parser.get_body_stream().getvalue(), b"Hello mick")

    def testProxyGET(self):
        data = (
            b"GET https://example.com:8080/foobar HTTP/8.4\r\n"
            b"content-length: 6\r\n"
            b"\r\n"
            b"Hello."
        )
        parser = self.parser
        self.feed(data)
        self.assertTrue(parser.completed)
        self.assertEqual(parser.version, "8.4")
        self.assertFalse(parser.empty)
        self.assertEqual(parser.headers, {"CONTENT_LENGTH": "6"})
        self.assertEqual(parser.path, "/foobar")
        self.assertEqual(parser.command, "GET")
        self.assertEqual(parser.proxy_scheme, "https")
        self.assertEqual(parser.proxy_netloc, "example.com:8080")
        self.assertEqual(parser.command, "GET")
        self.assertEqual(parser.query, "")
        self.assertEqual(parser.get_body_stream().getvalue(), b"Hello.")

    def testDuplicateHeaders(self):
        # Ensure that headers with the same key get concatenated as per
        # RFC2616.
        data = (
            b"GET /foobar HTTP/8.4\r\n"
            b"x-forwarded-for: 10.11.12.13\r\n"
            b"x-forwarded-for: unknown,127.0.0.1\r\n"
            b"X-Forwarded_for: 255.255.255.255\r\n"
            b"content-length: 6\r\n"
            b"\r\n"
            b"Hello."
        )
        self.feed(data)
        self.assertTrue(self.parser.completed)
        self.assertEqual(
            self.parser.headers,
            {
                "CONTENT_LENGTH": "6",
                "X_FORWARDED_FOR": "10.11.12.13, unknown,127.0.0.1",
            },
        )

    def testSpoofedHeadersDropped(self):
        data = (
            b"GET /foobar HTTP/8.4\r\n"
            b"x-auth_user: bob\r\n"
            b"content-length: 6\r\n"
            b"\r\n"
            b"Hello."
        )
        self.feed(data)
        self.assertTrue(self.parser.completed)
        self.assertEqual(self.parser.headers, {"CONTENT_LENGTH": "6",})


class DummyBodyStream(object):
    def getfile(self):
        return self

    def getbuf(self):
        return self

    def close(self):
        self.closed = True
