import logging
import urllib.parse as parse
import urllib
import urllib.request
import ssl
from typing import Tuple
import json


class RequestHelpers:
    @staticmethod
    def post(
            url: str,
            headers: dict = {},
            proxies: dict = {},
            verify_ssl: bool = False) -> Tuple[int, dict]:
        return RequestHelpers.request(
            url,
            "POST",
            headers=headers,
            proxies=proxies,
            verify_ssl=verify_ssl
        )

    @staticmethod
    def request(
            url: str,
            method: str,
            headers: dict = {},
            proxies: dict = {},
            verify_ssl: bool = False) -> Tuple[int, dict]:
        context = ssl.create_default_context()
        if not verify_ssl:
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        headers.update({'Content-Type': 'application/json'})
        proxy_handler = None

        if len(proxies.keys()) > 0:
            proxy_handler = urllib.request.ProxyHandler(proxies)
            # pragma: no cover

        req = urllib.request.Request(
            url,
            method=method,
            headers=headers)

        opener = urllib.request.build_opener(proxy_handler)\
            if proxy_handler is not None else\
            urllib.request.urlopen

        with opener(
                req,
                context=context) as response:
            status_code = response.getcode()
            response_body = response.read().decode('utf-8')

            try:
                json_data = json.loads(response_body)
            except json.JSONDecodeError:  # pragma: no cover
                json_data = None  # pragma: no cover

            return status_code, json_data


class Helpers:

    @staticmethod
    def configure_logger(level=logging.INFO, handler=None):
        logger = Helpers.get_logger()
        if handler is None:
            handler = logging.StreamHandler()
            debug_formatter = ""\
                if level != logging.DEBUG else\
                "- %(filename)s:%(lineno)d "
            handler.setFormatter(
                logging.Formatter(
                    '%(asctime)s - %(name)s '
                    + debug_formatter +
                    '- %(levelname)s - %(message)s'))
            handler.setLevel(level)
        logger.addHandler(handler)
        logger.setLevel(level)

    @staticmethod
    def get_logger():
        return logging.getLogger("SignalRCoreClient")

    @staticmethod
    def has_querystring(url):
        return "?" in url

    @staticmethod
    def split_querystring(url):
        parts = url.split("?")
        return parts[0], parts[1]

    @staticmethod
    def replace_scheme(
            url,
            root_scheme,
            source,
            secure_source,
            destination,
            secure_destination):
        url_parts = parse.urlsplit(url)

        if root_scheme not in url_parts.scheme:
            if url_parts.scheme == secure_source:
                url_parts = url_parts._replace(scheme=secure_destination)
            if url_parts.scheme == source:
                url_parts = url_parts._replace(scheme=destination)

        return parse.urlunsplit(url_parts)

    @staticmethod
    def websocket_to_http(url):
        return Helpers.replace_scheme(
            url,
            "http",
            "ws",
            "wss",
            "http",
            "https")

    @staticmethod
    def http_to_websocket(url):
        return Helpers.replace_scheme(
            url,
            "ws",
            "http",
            "https",
            "ws",
            "wss"
        )

    @staticmethod
    def get_negotiate_url(url):
        querystring = ""
        if Helpers.has_querystring(url):
            url, querystring = Helpers.split_querystring(url)

        url_parts = parse.urlsplit(Helpers.websocket_to_http(url))

        negotiate_suffix = "negotiate"\
            if url_parts.path.endswith('/')\
            else "/negotiate"

        url_parts = url_parts._replace(path=url_parts.path + negotiate_suffix)

        return parse.urlunsplit(url_parts) \
            if querystring == "" else\
            parse.urlunsplit(url_parts) + "?" + querystring

    @staticmethod
    def encode_connection_id(url, id):
        url_parts = parse.urlsplit(url)
        query_string_parts = parse.parse_qs(url_parts.query)
        query_string_parts["id"] = id

        url_parts = url_parts._replace(
            query=parse.urlencode(
                query_string_parts,
                doseq=True))

        return Helpers.http_to_websocket(parse.urlunsplit(url_parts))
