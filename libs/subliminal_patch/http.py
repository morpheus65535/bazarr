# coding=utf-8
import certifi
import ssl
import os
import socket
import logging
import requests
import xmlrpclib
import dns.resolver

from requests import Session, exceptions
from urllib3.util import connection
from retry.api import retry_call
from exceptions import APIThrottled

from subzero.lib.io import get_viable_encoding

logger = logging.getLogger(__name__)
pem_file = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(unicode(__file__, get_viable_encoding()))), "..", certifi.where()))
try:
    default_ssl_context = ssl.create_default_context(cafile=pem_file)
except AttributeError:
    # < Python 2.7.9
    default_ssl_context = None


custom_resolver = dns.resolver.Resolver(configure=False)

# 8.8.8.8 is Google's public DNS server
custom_resolver.nameservers = ['8.8.8.8', '1.1.1.1']


class CertifiSession(Session):
    timeout = 10

    def __init__(self):
        super(CertifiSession, self).__init__()
        self.verify = pem_file

    def request(self, *args, **kwargs):
        if kwargs.get('timeout') is None:
            kwargs['timeout'] = self.timeout
        return super(CertifiSession, self).request(*args, **kwargs)


class RetryingSession(CertifiSession):
    proxied_functions = ("get", "post")

    def __init__(self):
        super(CertifiSession, self).__init__()
        self.verify = pem_file

        proxy = os.environ.get('SZ_HTTP_PROXY')
        if proxy:
            self.proxies = {
                "http": proxy,
                "https": proxy
            }

    def retry_method(self, method, *args, **kwargs):
        if self.proxies:
            # fixme: may be a little loud
            logger.debug("Using proxy %s for: %s", self.proxies["http"], args[0])

        return retry_call(getattr(super(CertifiSession, self), method), fargs=args, fkwargs=kwargs, tries=3, delay=5,
                          exceptions=(exceptions.ConnectionError,
                                      exceptions.ProxyError,
                                      exceptions.SSLError,
                                      exceptions.Timeout,
                                      exceptions.ConnectTimeout,
                                      exceptions.ReadTimeout,
                                      socket.timeout))

    def get(self, *args, **kwargs):
        if self.proxies and "timeout" in kwargs and kwargs["timeout"]:
            kwargs["timeout"] = kwargs["timeout"] * 3
        return self.retry_method("get", *args, **kwargs)

    def post(self, *args, **kwargs):
        if self.proxies and "timeout" in kwargs and kwargs["timeout"]:
            kwargs["timeout"] = kwargs["timeout"] * 3
        return self.retry_method("post", *args, **kwargs)


class SubZeroRequestsTransport(xmlrpclib.SafeTransport):
    """
    Drop in Transport for xmlrpclib that uses Requests instead of httplib

    Based on: https://gist.github.com/chrisguitarguy/2354951#gistcomment-2388906

    """
    # change our user agent to reflect Requests
    user_agent = "Python XMLRPC with Requests (python-requests.org)"
    proxies = None

    def __init__(self, use_https=True, verify=None, user_agent=None, timeout=10, *args, **kwargs):
        self.verify = pem_file if verify is None else verify
        self.use_https = use_https
        self.user_agent = user_agent if user_agent is not None else self.user_agent
        self.timeout = timeout
        proxy = os.environ.get('SZ_HTTP_PROXY')
        if proxy:
            self.proxies = {
                "http": proxy,
                "https": proxy
            }

        xmlrpclib.SafeTransport.__init__(self, *args, **kwargs)

    def request(self, host, handler, request_body, verbose=0):
        """
        Make an xmlrpc request.
        """
        headers = {'User-Agent': self.user_agent}
        url = self._build_url(host, handler)
        try:
            resp = requests.post(url, data=request_body, headers=headers,
                                 stream=True, timeout=self.timeout, proxies=self.proxies,
                                 verify=self.verify)
        except ValueError:
            raise
        except Exception:
            raise  # something went wrong
        else:
            resp.raise_for_status()

            try:
                if 'x-ratelimit-remaining' in resp.headers and int(resp.headers['x-ratelimit-remaining']) <= 2:
                    raise APIThrottled()
            except ValueError:
                logger.info('Couldn\'t parse "x-ratelimit-remaining": %r' % resp.headers['x-ratelimit-remaining'])

            self.verbose = verbose
            try:
                return self.parse_response(resp.raw)
            except:
                logger.debug("Bad response data: %r", resp.raw)

    def _build_url(self, host, handler):
        """
        Build a url for our request based on the host, handler and use_http
        property
        """
        scheme = 'https' if self.use_https else 'http'
        handler = handler[1:] if handler and handler[0] == "/" else handler
        return '%s://%s/%s' % (scheme, host, handler)


_orig_create_connection = connection.create_connection


dns_cache = {}


def set_custom_resolver():
    def patched_create_connection(address, *args, **kwargs):
        """Wrap urllib3's create_connection to resolve the name elsewhere"""
        # resolve hostname to an ip address; use your own
        # resolver here, as otherwise the system resolver will be used.
        host, port = address
        if host in dns_cache:
            ip = dns_cache[host]
            logger.debug("Using %s=%s from cache", host, ip)
        else:
            try:
                ip = custom_resolver.query(host)[0].address
                dns_cache[host] = ip
            except dns.exception.DNSException:
                logger.warning("Couldn't resolve %s with DNS: %s", host, custom_resolver.nameservers)
                return _orig_create_connection((host, port), *args, **kwargs)

            logger.debug("Resolved %s to %s using %s", host, ip, custom_resolver.nameservers)

        return _orig_create_connection((ip, port), *args, **kwargs)

    connection.create_connection = patched_create_connection
