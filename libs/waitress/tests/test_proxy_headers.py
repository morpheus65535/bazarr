import unittest

from waitress.compat import tobytes


class TestProxyHeadersMiddleware(unittest.TestCase):
    def _makeOne(self, app, **kw):
        from waitress.proxy_headers import proxy_headers_middleware

        return proxy_headers_middleware(app, **kw)

    def _callFUT(self, app, **kw):
        response = DummyResponse()
        environ = DummyEnviron(**kw)

        def start_response(status, response_headers):
            response.status = status
            response.headers = response_headers

        response.steps = list(app(environ, start_response))
        response.body = b"".join(tobytes(s) for s in response.steps)
        return response

    def test_get_environment_values_w_scheme_override_untrusted(self):
        inner = DummyApp()
        app = self._makeOne(inner)
        response = self._callFUT(
            app, headers={"X_FOO": "BAR", "X_FORWARDED_PROTO": "https",}
        )
        self.assertEqual(response.status, "200 OK")
        self.assertEqual(inner.environ["wsgi.url_scheme"], "http")

    def test_get_environment_values_w_scheme_override_trusted(self):
        inner = DummyApp()
        app = self._makeOne(
            inner,
            trusted_proxy="192.168.1.1",
            trusted_proxy_headers={"x-forwarded-proto"},
        )
        response = self._callFUT(
            app,
            addr=["192.168.1.1", 8080],
            headers={"X_FOO": "BAR", "X_FORWARDED_PROTO": "https",},
        )

        environ = inner.environ
        self.assertEqual(response.status, "200 OK")
        self.assertEqual(environ["SERVER_PORT"], "443")
        self.assertEqual(environ["SERVER_NAME"], "localhost")
        self.assertEqual(environ["REMOTE_ADDR"], "192.168.1.1")
        self.assertEqual(environ["HTTP_X_FOO"], "BAR")

    def test_get_environment_values_w_bogus_scheme_override(self):
        inner = DummyApp()
        app = self._makeOne(
            inner,
            trusted_proxy="192.168.1.1",
            trusted_proxy_headers={"x-forwarded-proto"},
        )
        response = self._callFUT(
            app,
            addr=["192.168.1.1", 80],
            headers={
                "X_FOO": "BAR",
                "X_FORWARDED_PROTO": "http://p02n3e.com?url=http",
            },
        )
        self.assertEqual(response.status, "400 Bad Request")
        self.assertIn(b'Header "X-Forwarded-Proto" malformed', response.body)

    def test_get_environment_warning_other_proxy_headers(self):
        inner = DummyApp()
        logger = DummyLogger()
        app = self._makeOne(
            inner,
            trusted_proxy="192.168.1.1",
            trusted_proxy_count=1,
            trusted_proxy_headers={"forwarded"},
            log_untrusted=True,
            logger=logger,
        )
        response = self._callFUT(
            app,
            addr=["192.168.1.1", 80],
            headers={
                "X_FORWARDED_FOR": "[2001:db8::1]",
                "FORWARDED": "For=198.51.100.2;host=example.com:8080;proto=https",
            },
        )
        self.assertEqual(response.status, "200 OK")

        self.assertEqual(len(logger.logged), 1)

        environ = inner.environ
        self.assertNotIn("HTTP_X_FORWARDED_FOR", environ)
        self.assertEqual(environ["REMOTE_ADDR"], "198.51.100.2")
        self.assertEqual(environ["SERVER_NAME"], "example.com")
        self.assertEqual(environ["HTTP_HOST"], "example.com:8080")
        self.assertEqual(environ["SERVER_PORT"], "8080")
        self.assertEqual(environ["wsgi.url_scheme"], "https")

    def test_get_environment_contains_all_headers_including_untrusted(self):
        inner = DummyApp()
        app = self._makeOne(
            inner,
            trusted_proxy="192.168.1.1",
            trusted_proxy_count=1,
            trusted_proxy_headers={"x-forwarded-by"},
            clear_untrusted=False,
        )
        headers_orig = {
            "X_FORWARDED_FOR": "198.51.100.2",
            "X_FORWARDED_BY": "Waitress",
            "X_FORWARDED_PROTO": "https",
            "X_FORWARDED_HOST": "example.org",
        }
        response = self._callFUT(
            app, addr=["192.168.1.1", 80], headers=headers_orig.copy(),
        )
        self.assertEqual(response.status, "200 OK")
        environ = inner.environ
        for k, expected in headers_orig.items():
            result = environ["HTTP_%s" % k]
            self.assertEqual(result, expected)

    def test_get_environment_contains_only_trusted_headers(self):
        inner = DummyApp()
        app = self._makeOne(
            inner,
            trusted_proxy="192.168.1.1",
            trusted_proxy_count=1,
            trusted_proxy_headers={"x-forwarded-by"},
            clear_untrusted=True,
        )
        response = self._callFUT(
            app,
            addr=["192.168.1.1", 80],
            headers={
                "X_FORWARDED_FOR": "198.51.100.2",
                "X_FORWARDED_BY": "Waitress",
                "X_FORWARDED_PROTO": "https",
                "X_FORWARDED_HOST": "example.org",
            },
        )
        self.assertEqual(response.status, "200 OK")

        environ = inner.environ
        self.assertEqual(environ["HTTP_X_FORWARDED_BY"], "Waitress")
        self.assertNotIn("HTTP_X_FORWARDED_FOR", environ)
        self.assertNotIn("HTTP_X_FORWARDED_PROTO", environ)
        self.assertNotIn("HTTP_X_FORWARDED_HOST", environ)

    def test_get_environment_clears_headers_if_untrusted_proxy(self):
        inner = DummyApp()
        app = self._makeOne(
            inner,
            trusted_proxy="192.168.1.1",
            trusted_proxy_count=1,
            trusted_proxy_headers={"x-forwarded-by"},
            clear_untrusted=True,
        )
        response = self._callFUT(
            app,
            addr=["192.168.1.255", 80],
            headers={
                "X_FORWARDED_FOR": "198.51.100.2",
                "X_FORWARDED_BY": "Waitress",
                "X_FORWARDED_PROTO": "https",
                "X_FORWARDED_HOST": "example.org",
            },
        )
        self.assertEqual(response.status, "200 OK")

        environ = inner.environ
        self.assertNotIn("HTTP_X_FORWARDED_BY", environ)
        self.assertNotIn("HTTP_X_FORWARDED_FOR", environ)
        self.assertNotIn("HTTP_X_FORWARDED_PROTO", environ)
        self.assertNotIn("HTTP_X_FORWARDED_HOST", environ)

    def test_parse_proxy_headers_forwarded_for(self):
        inner = DummyApp()
        app = self._makeOne(
            inner, trusted_proxy="*", trusted_proxy_headers={"x-forwarded-for"},
        )
        response = self._callFUT(app, headers={"X_FORWARDED_FOR": "192.0.2.1"})
        self.assertEqual(response.status, "200 OK")

        environ = inner.environ
        self.assertEqual(environ["REMOTE_ADDR"], "192.0.2.1")

    def test_parse_proxy_headers_forwarded_for_v6_missing_brackets(self):
        inner = DummyApp()
        app = self._makeOne(
            inner, trusted_proxy="*", trusted_proxy_headers={"x-forwarded-for"},
        )
        response = self._callFUT(app, headers={"X_FORWARDED_FOR": "2001:db8::0"})
        self.assertEqual(response.status, "200 OK")

        environ = inner.environ
        self.assertEqual(environ["REMOTE_ADDR"], "2001:db8::0")

    def test_parse_proxy_headers_forwared_for_multiple(self):
        inner = DummyApp()
        app = self._makeOne(
            inner,
            trusted_proxy="*",
            trusted_proxy_count=2,
            trusted_proxy_headers={"x-forwarded-for"},
        )
        response = self._callFUT(
            app, headers={"X_FORWARDED_FOR": "192.0.2.1, 198.51.100.2, 203.0.113.1"}
        )
        self.assertEqual(response.status, "200 OK")

        environ = inner.environ
        self.assertEqual(environ["REMOTE_ADDR"], "198.51.100.2")

    def test_parse_forwarded_multiple_proxies_trust_only_two(self):
        inner = DummyApp()
        app = self._makeOne(
            inner,
            trusted_proxy="*",
            trusted_proxy_count=2,
            trusted_proxy_headers={"forwarded"},
        )
        response = self._callFUT(
            app,
            headers={
                "FORWARDED": (
                    "For=192.0.2.1;host=fake.com, "
                    "For=198.51.100.2;host=example.com:8080, "
                    "For=203.0.113.1"
                ),
            },
        )
        self.assertEqual(response.status, "200 OK")

        environ = inner.environ
        self.assertEqual(environ["REMOTE_ADDR"], "198.51.100.2")
        self.assertEqual(environ["SERVER_NAME"], "example.com")
        self.assertEqual(environ["HTTP_HOST"], "example.com:8080")
        self.assertEqual(environ["SERVER_PORT"], "8080")

    def test_parse_forwarded_multiple_proxies(self):
        inner = DummyApp()
        app = self._makeOne(
            inner,
            trusted_proxy="*",
            trusted_proxy_count=2,
            trusted_proxy_headers={"forwarded"},
        )
        response = self._callFUT(
            app,
            headers={
                "FORWARDED": (
                    'for="[2001:db8::1]:3821";host="example.com:8443";proto="https", '
                    'for=192.0.2.1;host="example.internal:8080"'
                ),
            },
        )
        self.assertEqual(response.status, "200 OK")

        environ = inner.environ
        self.assertEqual(environ["REMOTE_ADDR"], "2001:db8::1")
        self.assertEqual(environ["REMOTE_PORT"], "3821")
        self.assertEqual(environ["SERVER_NAME"], "example.com")
        self.assertEqual(environ["HTTP_HOST"], "example.com:8443")
        self.assertEqual(environ["SERVER_PORT"], "8443")
        self.assertEqual(environ["wsgi.url_scheme"], "https")

    def test_parse_forwarded_multiple_proxies_minimal(self):
        inner = DummyApp()
        app = self._makeOne(
            inner,
            trusted_proxy="*",
            trusted_proxy_count=2,
            trusted_proxy_headers={"forwarded"},
        )
        response = self._callFUT(
            app,
            headers={
                "FORWARDED": (
                    'for="[2001:db8::1]";proto="https", '
                    'for=192.0.2.1;host="example.org"'
                ),
            },
        )
        self.assertEqual(response.status, "200 OK")

        environ = inner.environ
        self.assertEqual(environ["REMOTE_ADDR"], "2001:db8::1")
        self.assertEqual(environ["SERVER_NAME"], "example.org")
        self.assertEqual(environ["HTTP_HOST"], "example.org")
        self.assertEqual(environ["SERVER_PORT"], "443")
        self.assertEqual(environ["wsgi.url_scheme"], "https")

    def test_parse_proxy_headers_forwarded_host_with_port(self):
        inner = DummyApp()
        app = self._makeOne(
            inner,
            trusted_proxy="*",
            trusted_proxy_count=2,
            trusted_proxy_headers={
                "x-forwarded-for",
                "x-forwarded-proto",
                "x-forwarded-host",
            },
        )
        response = self._callFUT(
            app,
            headers={
                "X_FORWARDED_FOR": "192.0.2.1, 198.51.100.2, 203.0.113.1",
                "X_FORWARDED_PROTO": "http",
                "X_FORWARDED_HOST": "example.com:8080",
            },
        )
        self.assertEqual(response.status, "200 OK")

        environ = inner.environ
        self.assertEqual(environ["REMOTE_ADDR"], "198.51.100.2")
        self.assertEqual(environ["SERVER_NAME"], "example.com")
        self.assertEqual(environ["HTTP_HOST"], "example.com:8080")
        self.assertEqual(environ["SERVER_PORT"], "8080")

    def test_parse_proxy_headers_forwarded_host_without_port(self):
        inner = DummyApp()
        app = self._makeOne(
            inner,
            trusted_proxy="*",
            trusted_proxy_count=2,
            trusted_proxy_headers={
                "x-forwarded-for",
                "x-forwarded-proto",
                "x-forwarded-host",
            },
        )
        response = self._callFUT(
            app,
            headers={
                "X_FORWARDED_FOR": "192.0.2.1, 198.51.100.2, 203.0.113.1",
                "X_FORWARDED_PROTO": "http",
                "X_FORWARDED_HOST": "example.com",
            },
        )
        self.assertEqual(response.status, "200 OK")

        environ = inner.environ
        self.assertEqual(environ["REMOTE_ADDR"], "198.51.100.2")
        self.assertEqual(environ["SERVER_NAME"], "example.com")
        self.assertEqual(environ["HTTP_HOST"], "example.com")
        self.assertEqual(environ["SERVER_PORT"], "80")

    def test_parse_proxy_headers_forwarded_host_with_forwarded_port(self):
        inner = DummyApp()
        app = self._makeOne(
            inner,
            trusted_proxy="*",
            trusted_proxy_count=2,
            trusted_proxy_headers={
                "x-forwarded-for",
                "x-forwarded-proto",
                "x-forwarded-host",
                "x-forwarded-port",
            },
        )
        response = self._callFUT(
            app,
            headers={
                "X_FORWARDED_FOR": "192.0.2.1, 198.51.100.2, 203.0.113.1",
                "X_FORWARDED_PROTO": "http",
                "X_FORWARDED_HOST": "example.com",
                "X_FORWARDED_PORT": "8080",
            },
        )
        self.assertEqual(response.status, "200 OK")

        environ = inner.environ
        self.assertEqual(environ["REMOTE_ADDR"], "198.51.100.2")
        self.assertEqual(environ["SERVER_NAME"], "example.com")
        self.assertEqual(environ["HTTP_HOST"], "example.com:8080")
        self.assertEqual(environ["SERVER_PORT"], "8080")

    def test_parse_proxy_headers_forwarded_host_multiple_with_forwarded_port(self):
        inner = DummyApp()
        app = self._makeOne(
            inner,
            trusted_proxy="*",
            trusted_proxy_count=2,
            trusted_proxy_headers={
                "x-forwarded-for",
                "x-forwarded-proto",
                "x-forwarded-host",
                "x-forwarded-port",
            },
        )
        response = self._callFUT(
            app,
            headers={
                "X_FORWARDED_FOR": "192.0.2.1, 198.51.100.2, 203.0.113.1",
                "X_FORWARDED_PROTO": "http",
                "X_FORWARDED_HOST": "example.com, example.org",
                "X_FORWARDED_PORT": "8080",
            },
        )
        self.assertEqual(response.status, "200 OK")

        environ = inner.environ
        self.assertEqual(environ["REMOTE_ADDR"], "198.51.100.2")
        self.assertEqual(environ["SERVER_NAME"], "example.com")
        self.assertEqual(environ["HTTP_HOST"], "example.com:8080")
        self.assertEqual(environ["SERVER_PORT"], "8080")

    def test_parse_proxy_headers_forwarded_host_multiple_with_forwarded_port_limit_one_trusted(
        self,
    ):
        inner = DummyApp()
        app = self._makeOne(
            inner,
            trusted_proxy="*",
            trusted_proxy_count=1,
            trusted_proxy_headers={
                "x-forwarded-for",
                "x-forwarded-proto",
                "x-forwarded-host",
                "x-forwarded-port",
            },
        )
        response = self._callFUT(
            app,
            headers={
                "X_FORWARDED_FOR": "192.0.2.1, 198.51.100.2, 203.0.113.1",
                "X_FORWARDED_PROTO": "http",
                "X_FORWARDED_HOST": "example.com, example.org",
                "X_FORWARDED_PORT": "8080",
            },
        )
        self.assertEqual(response.status, "200 OK")

        environ = inner.environ
        self.assertEqual(environ["REMOTE_ADDR"], "203.0.113.1")
        self.assertEqual(environ["SERVER_NAME"], "example.org")
        self.assertEqual(environ["HTTP_HOST"], "example.org:8080")
        self.assertEqual(environ["SERVER_PORT"], "8080")

    def test_parse_forwarded(self):
        inner = DummyApp()
        app = self._makeOne(
            inner,
            trusted_proxy="*",
            trusted_proxy_count=1,
            trusted_proxy_headers={"forwarded"},
        )
        response = self._callFUT(
            app,
            headers={
                "FORWARDED": "For=198.51.100.2:5858;host=example.com:8080;proto=https",
            },
        )
        self.assertEqual(response.status, "200 OK")

        environ = inner.environ
        self.assertEqual(environ["REMOTE_ADDR"], "198.51.100.2")
        self.assertEqual(environ["REMOTE_PORT"], "5858")
        self.assertEqual(environ["SERVER_NAME"], "example.com")
        self.assertEqual(environ["HTTP_HOST"], "example.com:8080")
        self.assertEqual(environ["SERVER_PORT"], "8080")
        self.assertEqual(environ["wsgi.url_scheme"], "https")

    def test_parse_forwarded_empty_pair(self):
        inner = DummyApp()
        app = self._makeOne(
            inner,
            trusted_proxy="*",
            trusted_proxy_count=1,
            trusted_proxy_headers={"forwarded"},
        )
        response = self._callFUT(
            app, headers={"FORWARDED": "For=198.51.100.2;;proto=https;by=_unused",}
        )
        self.assertEqual(response.status, "200 OK")

        environ = inner.environ
        self.assertEqual(environ["REMOTE_ADDR"], "198.51.100.2")

    def test_parse_forwarded_pair_token_whitespace(self):
        inner = DummyApp()
        app = self._makeOne(
            inner,
            trusted_proxy="*",
            trusted_proxy_count=1,
            trusted_proxy_headers={"forwarded"},
        )
        response = self._callFUT(
            app, headers={"FORWARDED": "For=198.51.100.2; proto =https",}
        )
        self.assertEqual(response.status, "400 Bad Request")
        self.assertIn(b'Header "Forwarded" malformed', response.body)

    def test_parse_forwarded_pair_value_whitespace(self):
        inner = DummyApp()
        app = self._makeOne(
            inner,
            trusted_proxy="*",
            trusted_proxy_count=1,
            trusted_proxy_headers={"forwarded"},
        )
        response = self._callFUT(
            app, headers={"FORWARDED": 'For= "198.51.100.2"; proto =https',}
        )
        self.assertEqual(response.status, "400 Bad Request")
        self.assertIn(b'Header "Forwarded" malformed', response.body)

    def test_parse_forwarded_pair_no_equals(self):
        inner = DummyApp()
        app = self._makeOne(
            inner,
            trusted_proxy="*",
            trusted_proxy_count=1,
            trusted_proxy_headers={"forwarded"},
        )
        response = self._callFUT(app, headers={"FORWARDED": "For"})
        self.assertEqual(response.status, "400 Bad Request")
        self.assertIn(b'Header "Forwarded" malformed', response.body)

    def test_parse_forwarded_warning_unknown_token(self):
        inner = DummyApp()
        logger = DummyLogger()
        app = self._makeOne(
            inner,
            trusted_proxy="*",
            trusted_proxy_count=1,
            trusted_proxy_headers={"forwarded"},
            logger=logger,
        )
        response = self._callFUT(
            app,
            headers={
                "FORWARDED": (
                    "For=198.51.100.2;host=example.com:8080;proto=https;"
                    'unknown="yolo"'
                ),
            },
        )
        self.assertEqual(response.status, "200 OK")

        self.assertEqual(len(logger.logged), 1)
        self.assertIn("Unknown Forwarded token", logger.logged[0])

        environ = inner.environ
        self.assertEqual(environ["REMOTE_ADDR"], "198.51.100.2")
        self.assertEqual(environ["SERVER_NAME"], "example.com")
        self.assertEqual(environ["HTTP_HOST"], "example.com:8080")
        self.assertEqual(environ["SERVER_PORT"], "8080")
        self.assertEqual(environ["wsgi.url_scheme"], "https")

    def test_parse_no_valid_proxy_headers(self):
        inner = DummyApp()
        app = self._makeOne(inner, trusted_proxy="*", trusted_proxy_count=1,)
        response = self._callFUT(
            app,
            headers={
                "X_FORWARDED_FOR": "198.51.100.2",
                "FORWARDED": "For=198.51.100.2;host=example.com:8080;proto=https",
            },
        )
        self.assertEqual(response.status, "200 OK")

        environ = inner.environ
        self.assertEqual(environ["REMOTE_ADDR"], "127.0.0.1")
        self.assertEqual(environ["SERVER_NAME"], "localhost")
        self.assertEqual(environ["HTTP_HOST"], "192.168.1.1:80")
        self.assertEqual(environ["SERVER_PORT"], "8080")
        self.assertEqual(environ["wsgi.url_scheme"], "http")

    def test_parse_multiple_x_forwarded_proto(self):
        inner = DummyApp()
        logger = DummyLogger()
        app = self._makeOne(
            inner,
            trusted_proxy="*",
            trusted_proxy_count=1,
            trusted_proxy_headers={"x-forwarded-proto"},
            logger=logger,
        )
        response = self._callFUT(app, headers={"X_FORWARDED_PROTO": "http, https",})
        self.assertEqual(response.status, "400 Bad Request")
        self.assertIn(b'Header "X-Forwarded-Proto" malformed', response.body)

    def test_parse_multiple_x_forwarded_port(self):
        inner = DummyApp()
        logger = DummyLogger()
        app = self._makeOne(
            inner,
            trusted_proxy="*",
            trusted_proxy_count=1,
            trusted_proxy_headers={"x-forwarded-port"},
            logger=logger,
        )
        response = self._callFUT(app, headers={"X_FORWARDED_PORT": "443, 80",})
        self.assertEqual(response.status, "400 Bad Request")
        self.assertIn(b'Header "X-Forwarded-Port" malformed', response.body)

    def test_parse_forwarded_port_wrong_proto_port_80(self):
        inner = DummyApp()
        app = self._makeOne(
            inner,
            trusted_proxy="*",
            trusted_proxy_count=1,
            trusted_proxy_headers={
                "x-forwarded-port",
                "x-forwarded-host",
                "x-forwarded-proto",
            },
        )
        response = self._callFUT(
            app,
            headers={
                "X_FORWARDED_PORT": "80",
                "X_FORWARDED_PROTO": "https",
                "X_FORWARDED_HOST": "example.com",
            },
        )
        self.assertEqual(response.status, "200 OK")

        environ = inner.environ
        self.assertEqual(environ["SERVER_NAME"], "example.com")
        self.assertEqual(environ["HTTP_HOST"], "example.com:80")
        self.assertEqual(environ["SERVER_PORT"], "80")
        self.assertEqual(environ["wsgi.url_scheme"], "https")

    def test_parse_forwarded_port_wrong_proto_port_443(self):
        inner = DummyApp()
        app = self._makeOne(
            inner,
            trusted_proxy="*",
            trusted_proxy_count=1,
            trusted_proxy_headers={
                "x-forwarded-port",
                "x-forwarded-host",
                "x-forwarded-proto",
            },
        )
        response = self._callFUT(
            app,
            headers={
                "X_FORWARDED_PORT": "443",
                "X_FORWARDED_PROTO": "http",
                "X_FORWARDED_HOST": "example.com",
            },
        )
        self.assertEqual(response.status, "200 OK")

        environ = inner.environ
        self.assertEqual(environ["SERVER_NAME"], "example.com")
        self.assertEqual(environ["HTTP_HOST"], "example.com:443")
        self.assertEqual(environ["SERVER_PORT"], "443")
        self.assertEqual(environ["wsgi.url_scheme"], "http")

    def test_parse_forwarded_for_bad_quote(self):
        inner = DummyApp()
        app = self._makeOne(
            inner,
            trusted_proxy="*",
            trusted_proxy_count=1,
            trusted_proxy_headers={"x-forwarded-for"},
        )
        response = self._callFUT(app, headers={"X_FORWARDED_FOR": '"foo'})
        self.assertEqual(response.status, "400 Bad Request")
        self.assertIn(b'Header "X-Forwarded-For" malformed', response.body)

    def test_parse_forwarded_host_bad_quote(self):
        inner = DummyApp()
        app = self._makeOne(
            inner,
            trusted_proxy="*",
            trusted_proxy_count=1,
            trusted_proxy_headers={"x-forwarded-host"},
        )
        response = self._callFUT(app, headers={"X_FORWARDED_HOST": '"foo'})
        self.assertEqual(response.status, "400 Bad Request")
        self.assertIn(b'Header "X-Forwarded-Host" malformed', response.body)


class DummyLogger(object):
    def __init__(self):
        self.logged = []

    def warning(self, msg, *args):
        self.logged.append(msg % args)


class DummyApp(object):
    def __call__(self, environ, start_response):
        self.environ = environ
        start_response("200 OK", [("Content-Type", "text/plain")])
        yield "hello"


class DummyResponse(object):
    status = None
    headers = None
    body = None


def DummyEnviron(
    addr=("127.0.0.1", 8080), scheme="http", server="localhost", headers=None,
):
    environ = {
        "REMOTE_ADDR": addr[0],
        "REMOTE_HOST": addr[0],
        "REMOTE_PORT": addr[1],
        "SERVER_PORT": str(addr[1]),
        "SERVER_NAME": server,
        "wsgi.url_scheme": scheme,
        "HTTP_HOST": "192.168.1.1:80",
    }
    if headers:
        environ.update(
            {
                "HTTP_" + key.upper().replace("-", "_"): value
                for key, value in headers.items()
            }
        )
    return environ
