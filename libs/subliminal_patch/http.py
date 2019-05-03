# coding=utf-8
import json
from collections import OrderedDict

import certifi
import ssl
import os
import socket
import logging
import requests
import xmlrpclib
import dns.resolver

from requests import exceptions
from urllib3.util import connection
from retry.api import retry_call
from exceptions import APIThrottled
from dogpile.cache.api import NO_VALUE
from subliminal.cache import region
from cfscrape import CloudflareScraper

try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

from subzero.lib.io import get_viable_encoding

logger = logging.getLogger(__name__)
pem_file = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(unicode(__file__, get_viable_encoding()))), "..", certifi.where()))
try:
    default_ssl_context = ssl.create_default_context(cafile=pem_file)
except AttributeError:
    # < Python 2.7.9
    default_ssl_context = None


class TimeoutSession(requests.Session):
    timeout = 10

    def __init__(self, timeout=None):
        super(TimeoutSession, self).__init__()
        self.timeout = timeout or self.timeout

    def request(self, method, url, *args, **kwargs):
        if kwargs.get('timeout') is None:
            kwargs['timeout'] = self.timeout

        return super(TimeoutSession, self).request(method, url, *args, **kwargs)


class CertifiSession(TimeoutSession):
    def __init__(self):
        super(CertifiSession, self).__init__()
        self.verify = pem_file


class CFSession(CloudflareScraper):
    def __init__(self):
        super(CFSession, self).__init__()
        self.debug = os.environ.get("CF_DEBUG", False)

    def request(self, method, url, *args, **kwargs):
        parsed_url = urlparse(url)
        domain = parsed_url.netloc

        cache_key = "cf_data2_%s" % domain

        if not self.cookies.get("cf_clearance", "", domain=domain):
            cf_data = region.get(cache_key)
            if cf_data is not NO_VALUE:
                cf_cookies, user_agent, hdrs = cf_data
                logger.debug("Trying to use old cf data for %s: %s", domain, cf_data)
                for cookie, value in cf_cookies.iteritems():
                    self.cookies.set(cookie, value, domain=domain)

                self._hdrs = hdrs
                self._ua = user_agent
                self.headers['User-Agent'] = self._ua

        ret = super(CFSession, self).request(method, url, *args, **kwargs)

        if self._was_cf:
            self._was_cf = False
            logger.debug("We've hit CF, trying to store previous data")
            try:
                cf_data = self.get_cf_live_tokens(domain)
            except:
                logger.debug("Couldn't get CF live tokens for re-use. Cookies: %r", self.cookies)
                pass
            else:
                if cf_data != region.get(cache_key) and cf_data[0]["cf_clearance"]:
                    logger.debug("Storing cf data for %s: %s", domain, cf_data)
                    region.set(cache_key, cf_data)

        return ret

    def get_cf_live_tokens(self, domain):
        for d in self.cookies.list_domains():
            if d.startswith(".") and d in ("." + domain):
                cookie_domain = d
                break
        else:
            raise ValueError(
                "Unable to find Cloudflare cookies. Does the site actually have "
                "Cloudflare IUAM (\"I'm Under Attack Mode\") enabled?")

        return (OrderedDict(filter(lambda x: x[1], [
                    ("__cfduid", self.cookies.get("__cfduid", "", domain=cookie_domain)),
                    ("cf_clearance", self.cookies.get("cf_clearance", "", domain=cookie_domain))
                ])),
                self._ua, self._hdrs
        )


class RetryingSession(CertifiSession):
    proxied_functions = ("get", "post")

    def __init__(self):
        super(RetryingSession, self).__init__()

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

        return retry_call(getattr(super(RetryingSession, self), method), fargs=args, fkwargs=kwargs, tries=3, delay=5,
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


class RetryingCFSession(RetryingSession, CFSession):
    pass


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


_custom_resolver = None
_custom_resolver_ips = None


def patch_create_connection():
    if hasattr(connection.create_connection, "_sz_patched"):
        return

    def patched_create_connection(address, *args, **kwargs):
        """Wrap urllib3's create_connection to resolve the name elsewhere"""
        # resolve hostname to an ip address; use your own
        # resolver here, as otherwise the system resolver will be used.
        global _custom_resolver, _custom_resolver_ips, dns_cache
        host, port = address

        __custom_resolver_ips = os.environ.get("dns_resolvers", None)

        # resolver ips changed in the meantime?
        if __custom_resolver_ips != _custom_resolver_ips:
            _custom_resolver = None
            _custom_resolver_ips = __custom_resolver_ips
            dns_cache = {}

        custom_resolver = _custom_resolver

        if not custom_resolver:
            if _custom_resolver_ips:
                logger.debug("DNS: Trying to use custom DNS resolvers: %s", _custom_resolver_ips)
                custom_resolver = dns.resolver.Resolver(configure=False)
                custom_resolver.lifetime = 8.0
                try:
                    custom_resolver.nameservers = json.loads(_custom_resolver_ips)
                except:
                    logger.debug("DNS: Couldn't load custom DNS resolvers: %s", _custom_resolver_ips)
                else:
                    _custom_resolver = custom_resolver

        if custom_resolver:
            if host in dns_cache:
                ip = dns_cache[host]
                logger.debug("DNS: Using %s=%s from cache", host, ip)
                return _orig_create_connection((ip, port), *args, **kwargs)
            else:
                try:
                    ip = custom_resolver.query(host)[0].address
                    logger.debug("DNS: Resolved %s to %s using %s", host, ip, custom_resolver.nameservers)
                    dns_cache[host] = ip
                except dns.exception.DNSException:
                    logger.warning("DNS: Couldn't resolve %s with DNS: %s", host, custom_resolver.nameservers)
                    raise

        return _orig_create_connection((host, port), *args, **kwargs)

    patch_create_connection._sz_patched = True
    connection.create_connection = patched_create_connection


patch_create_connection()

