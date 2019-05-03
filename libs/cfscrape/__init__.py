# coding=utf-8

import logging
import random
import re
import os
import json
import base64

from copy import deepcopy
from time import sleep
from collections import OrderedDict
from .jsfuck import jsunfuck

import js2py
from requests.sessions import Session
from subliminal_patch.pitcher import pitchers

try:
    from requests_toolbelt.utils import dump
except ImportError:
    pass

try:
    from urlparse import urlparse
    from urlparse import urlunparse
except ImportError:
    from urllib.parse import urlparse
    from urllib.parse import urlunparse

brotli_available = True

try:
    from brotli import decompress as brdec
except:
    brotli_available = False

logger = logging.getLogger(__name__)

__version__ = "2.0.3"

# Orignally written by https://github.com/Anorov/cloudflare-scrape
# Rewritten by VeNoMouS - <venom@gen-x.co.nz> for https://github.com/VeNoMouS/Sick-Beard - 24/3/2018 NZDT

DEFAULT_USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/65.0.3325.181 Chrome/65.0.3325.181 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 7.0; Moto G (5) Build/NPPS25.137-93-8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.137 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 7_0_4 like Mac OS X) AppleWebKit/537.51.1 (KHTML, like Gecko) Version/7.0 Mobile/11B554a Safari/9537.53",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:60.0) Gecko/20100101 Firefox/60.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:59.0) Gecko/20100101 Firefox/59.0",
    "Mozilla/5.0 (Windows NT 6.3; Win64; x64; rv:57.0) Gecko/20100101 Firefox/57.0",
]

BUG_REPORT = """\
Cloudflare may have changed their technique, or there may be a bug in the script.
"""


cur_path = os.path.abspath(os.path.dirname(__file__))

if brotli_available:
    brwsrs = os.path.join(cur_path, "browsers_br.json")
    with open(brwsrs, "r") as f:
        UA_COMBO = json.load(f, object_pairs_hook=OrderedDict)["chrome"]

else:
    brwsrs = os.path.join(cur_path, "browsers.json")
    UA_COMBO = []
    with open(brwsrs, "r") as f:
        _brwsrs = json.load(f, object_pairs_hook=OrderedDict)
        for entry in _brwsrs:
            _entry = OrderedDict(("-".join(a.capitalize() for a in key.split("-")), value)
                                 for key, value in entry.iteritems())
            _entry["User-Agent"] = None
            UA_COMBO.append({"User-Agent": [entry["user-agent"]], "headers": _entry})


class NeedsCaptchaException(Exception):
    pass


class CloudflareScraper(Session):
    def __init__(self, *args, **kwargs):
        self.delay = kwargs.pop('delay', 8)
        self.debug = False
        self._was_cf = False
        self._ua = None
        self._hdrs = None

        super(CloudflareScraper, self).__init__(*args, **kwargs)

        if not self._ua:
            # Set a random User-Agent if no custom User-Agent has been set
            ua_combo = random.choice(UA_COMBO)
            self._ua = random.choice(ua_combo["User-Agent"])
            self._hdrs = ua_combo["headers"].copy()
            self._hdrs["User-Agent"] = self._ua
            self.headers['User-Agent'] = self._ua

    def set_cloudflare_challenge_delay(self, delay):
        if isinstance(delay, (int, float)) and delay > 0:
            self.delay = delay

    def is_cloudflare_challenge(self, resp):
        if resp.headers.get('Server', '').startswith('cloudflare'):
            if b'why_captcha' in resp.content or b'/cdn-cgi/l/chk_captcha' in resp.content:
                raise NeedsCaptchaException

            return (
                resp.status_code in [429, 503]
                and b"jschl_vc" in resp.content
                and b"jschl_answer" in resp.content
            )
        return False

    def debugRequest(self, req):
        try:
            print (dump.dump_all(req).decode('utf-8'))
        except:
            pass

    def request(self, method, url, *args, **kwargs):
        # self.headers = (
        #     OrderedDict(
        #         [
        #             ('User-Agent', self.headers['User-Agent']),
        #             ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
        #             ('Accept-Language', 'en-US,en;q=0.5'),
        #             ('Accept-Encoding', 'gzip, deflate'),
        #             ('Connection',  'close'),
        #             ('Upgrade-Insecure-Requests', '1')
        #         ]
        #     )
        # )
        self.headers = self._hdrs.copy()

        resp = super(CloudflareScraper, self).request(method, url, *args, **kwargs)
        if resp.headers.get('content-encoding') == 'br' and brotli_available:
            resp._content = brdec(resp._content)

        # Debug request
        if self.debug:
            self.debugRequest(resp)

        # Check if Cloudflare anti-bot is on
        try:
            if self.is_cloudflare_challenge(resp):
                self._was_cf = True
                # Work around if the initial request is not a GET,
                # Superseed with a GET then re-request the orignal METHOD.
                if resp.request.method != 'GET':
                    self.request('GET', resp.url)
                    resp = self.request(method, url, *args, **kwargs)
                else:
                    resp = self.solve_cf_challenge(resp, **kwargs)
        except NeedsCaptchaException:
            # solve the captcha
            self._was_cf = True
            site_key = re.search(r'data-sitekey="(.+?)"', resp.content).group(1)
            challenge_s = re.search(r'type="hidden" name="s" value="(.+?)"', resp.content).group(1)
            challenge_ray = re.search(r'data-ray="(.+?)"', resp.content).group(1)
            if not all([site_key, challenge_s, challenge_ray]):
                raise Exception("cf: Captcha site-key not found!")

            pitcher = pitchers.get_pitcher()("cf", resp.request.url, site_key,
                                             user_agent=self.headers["User-Agent"],
                                             cookies=self.cookies.get_dict(),
                                             is_invisible=True)

            parsed_url = urlparse(resp.url)
            domain = parsed_url.netloc
            logger.info("cf: %s: Solving captcha", domain)
            result = pitcher.throw()
            if not result:
                raise Exception("cf: Couldn't solve captcha!")

            submit_url = '{}://{}/cdn-cgi/l/chk_captcha'.format(parsed_url.scheme, domain)
            method = resp.request.method

            cloudflare_kwargs = {
                'allow_redirects': False,
                'headers': {'Referer': resp.url},
                'params': OrderedDict(
                    [
                        ('s', challenge_s),
                        ('g-recaptcha-response', result)
                    ]
                )
            }

            return self.request(method, submit_url, **cloudflare_kwargs)

        return resp

    def solve_cf_challenge(self, resp, **original_kwargs):
        body = resp.text

        # Cloudflare requires a delay before solving the challenge
        if self.delay == 8:
            try:
                delay = float(re.search(r'submit\(\);\r?\n\s*},\s*([0-9]+)', body).group(1)) / float(1000)
                if isinstance(delay, (int, float)):
                    self.delay = delay
            except:
                pass

        sleep(self.delay)

        parsed_url = urlparse(resp.url)
        domain = parsed_url.netloc
        submit_url = '{}://{}/cdn-cgi/l/chk_jschl'.format(parsed_url.scheme, domain)

        cloudflare_kwargs = deepcopy(original_kwargs)
        headers = cloudflare_kwargs.setdefault('headers', {'Referer': resp.url})

        try:
            params = cloudflare_kwargs.setdefault(
                'params', OrderedDict(
                    [
                        ('s', re.search(r'name="s"\svalue="(?P<s_value>[^"]+)', body).group('s_value')),
                        ('jschl_vc', re.search(r'name="jschl_vc" value="(\w+)"', body).group(1)),
                        ('pass', re.search(r'name="pass" value="(.+?)"', body).group(1)),
                    ]
                )
            )

        except Exception as e:
            # Something is wrong with the page.
            # This may indicate Cloudflare has changed their anti-bot
            # technique. If you see this and are running the latest version,
            # please open a GitHub issue so I can update the code accordingly.
            raise ValueError("Unable to parse Cloudflare anti-bots page: {} {}".format(e.message, BUG_REPORT))

        # Solve the Javascript challenge
        params['jschl_answer'] = self.solve_challenge(body, domain)

        # Requests transforms any request into a GET after a redirect,
        # so the redirect has to be handled manually here to allow for
        # performing other types of requests even as the first request.
        method = resp.request.method

        cloudflare_kwargs['allow_redirects'] = False

        redirect = self.request(method, submit_url, **cloudflare_kwargs)
        redirect_location = urlparse(redirect.headers['Location'])
        if not redirect_location.netloc:
            redirect_url = urlunparse(
                (
                    parsed_url.scheme,
                    domain,
                    redirect_location.path,
                    redirect_location.params,
                    redirect_location.query,
                    redirect_location.fragment
                )
            )
            return self.request(method, redirect_url, **original_kwargs)

        return self.request(method, redirect.headers['Location'], **original_kwargs)

    def solve_challenge(self, body, domain):
        try:
            js = re.search(
                r"setTimeout\(function\(\){\s+(var s,t,o,p,b,r,e,a,k,i,n,g,f.+?\r?\n[\s\S]+?a\.value =.+?)\r?\n",
                body
            ).group(1)
        except Exception:
            raise ValueError("Unable to identify Cloudflare IUAM Javascript on website. {}".format(BUG_REPORT))

        js = re.sub(r"a\.value = ((.+).toFixed\(10\))?", r"\1", js)
        js = re.sub(r'(e\s=\sfunction\(s\)\s{.*?};)', '', js, flags=re.DOTALL|re.MULTILINE)
        js = re.sub(r"\s{3,}[a-z](?: = |\.).+", "", js).replace("t.length", str(len(domain)))

        js = js.replace('; 121', '')

        # Strip characters that could be used to exit the string context
        # These characters are not currently used in Cloudflare's arithmetic snippet
        js = re.sub(r"[\n\\']", "", js)

        if 'toFixed' not in js:
            raise ValueError("Error parsing Cloudflare IUAM Javascript challenge. {}".format(BUG_REPORT))

        try:
            jsEnv = """
            var t = "{domain}";
            var g = String.fromCharCode;

            o = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=";
            e = function(s) {{
                s += "==".slice(2 - (s.length & 3));
                var bm, r = "", r1, r2, i = 0;
                for (; i < s.length;) {{
                    bm = o.indexOf(s.charAt(i++)) << 18 | o.indexOf(s.charAt(i++)) << 12 | (r1 = o.indexOf(s.charAt(i++))) << 6 | (r2 = o.indexOf(s.charAt(i++)));
                    r += r1 === 64 ? g(bm >> 16 & 255) : r2 === 64 ? g(bm >> 16 & 255, bm >> 8 & 255) : g(bm >> 16 & 255, bm >> 8 & 255, bm & 255);
                }}
                return r;
            }};

            function italics (str) {{ return '<i>' + this + '</i>'; }};
            var document = {{
                getElementById: function () {{
                    return {{'innerHTML': '{innerHTML}'}};
                }}
            }};
            {js}
            """

            innerHTML = re.search(
                '<div(?: [^<>]*)? id="([^<>]*?)">([^<>]*?)<\/div>',
                body,
                re.MULTILINE | re.DOTALL
            )
            innerHTML = innerHTML.group(2).replace("'", r"\'") if innerHTML else ""

            js = jsunfuck(jsEnv.format(domain=domain, innerHTML=innerHTML, js=js))

            def atob(s):
                return base64.b64decode('{}'.format(s)).decode('utf-8')

            js2py.disable_pyimport()
            context = js2py.EvalJs({'atob': atob})
            result = context.eval(js)
        except Exception:
            logging.error("Error executing Cloudflare IUAM Javascript. {}".format(BUG_REPORT))
            raise

        try:
            float(result)
        except Exception:
            raise ValueError("Cloudflare IUAM challenge returned unexpected answer. {}".format(BUG_REPORT))

        return result

    @classmethod
    def create_scraper(cls, sess=None, **kwargs):
        """
        Convenience function for creating a ready-to-go CloudflareScraper object.
        """
        scraper = cls(**kwargs)

        if sess:
            attrs = ['auth', 'cert', 'cookies', 'headers', 'hooks', 'params', 'proxies', 'data']
            for attr in attrs:
                val = getattr(sess, attr, None)
                if val:
                    setattr(scraper, attr, val)

        return scraper

    # Functions for integrating cloudflare-scrape with other applications and scripts
    @classmethod
    def get_tokens(cls, url, user_agent=None, debug=False, **kwargs):
        scraper = cls.create_scraper()
        scraper.debug = debug

        if user_agent:
            scraper.headers['User-Agent'] = user_agent

        try:
            resp = scraper.get(url, **kwargs)
            resp.raise_for_status()
        except Exception as e:
            logging.error("'{}' returned an error. Could not collect tokens.".format(url))
            raise

        domain = urlparse(resp.url).netloc
        cookie_domain = None

        for d in scraper.cookies.list_domains():
            if d.startswith('.') and d in ('.{}'.format(domain)):
                cookie_domain = d
                break
        else:
            raise ValueError("Unable to find Cloudflare cookies. Does the site actually have Cloudflare IUAM (\"I'm Under Attack Mode\") enabled?")

        return (
            {
                '__cfduid': scraper.cookies.get('__cfduid', '', domain=cookie_domain),
                'cf_clearance': scraper.cookies.get('cf_clearance', '', domain=cookie_domain)
            },
            scraper.headers['User-Agent']
        )

    @classmethod
    def get_cookie_string(cls, url, user_agent=None, debug=False, **kwargs):
        """
        Convenience function for building a Cookie HTTP header value.
        """
        tokens, user_agent = cls.get_tokens(url, user_agent=user_agent, debug=debug, **kwargs)
        return "; ".join("=".join(pair) for pair in tokens.items()), user_agent

create_scraper = CloudflareScraper.create_scraper
get_tokens = CloudflareScraper.get_tokens
get_cookie_string = CloudflareScraper.get_cookie_string
