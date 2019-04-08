import logging
import random
import time
import re

# based off of https://gist.github.com/doko-desuka/58d9212461f62583f8df9bc6387fade2
# and https://github.com/Anorov/cloudflare-scrape
# and https://github.com/VeNoMouS/cloudflare-scrape-js2py

'''''''''
Disables InsecureRequestWarning: Unverified HTTPS request is being made warnings.
'''''''''
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
''''''
from requests.sessions import Session
from copy import deepcopy

try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

DEFAULT_USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/65.0.3325.181 Chrome/65.0.3325.181 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 7.0; Moto G (5) Build/NPPS25.137-93-8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.137 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 7_0_4 like Mac OS X) AppleWebKit/537.51.1 (KHTML, like Gecko) Version/7.0 Mobile/11B554a Safari/9537.53",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:60.0) Gecko/20100101 Firefox/60.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:59.0) Gecko/20100101 Firefox/59.0",
    "Mozilla/5.0 (Windows NT 6.3; Win64; x64; rv:57.0) Gecko/20100101 Firefox/57.0"
]

DEFAULT_USER_AGENT = random.choice(DEFAULT_USER_AGENTS)

BUG_REPORT = (
    "Cloudflare may have changed their technique, or there may be a bug in the script.\n\nPlease read " "https://github.com/Anorov/cloudflare-scrape#updates, then file a "
    "bug report at https://github.com/Anorov/cloudflare-scrape/issues.")


class CloudflareScraper(Session):
    def __init__(self, *args, **kwargs):
        super(CloudflareScraper, self).__init__(*args, **kwargs)

        if "requests" in self.headers["User-Agent"]:
            # Spoof Firefox on Linux if no custom User-Agent has been set
            self.headers["User-Agent"] = random.choice(DEFAULT_USER_AGENTS)

    def request(self, method, url, *args, **kwargs):
        resp = super(CloudflareScraper, self).request(method, url, *args, **kwargs)

        # Check if Cloudflare anti-bot is on
        if (resp.status_code in (503, 429)
                and resp.headers.get("Server", "").startswith("cloudflare")
                and b"jschl_vc" in resp.content
                and b"jschl_answer" in resp.content
        ):
            return self.solve_cf_challenge(resp, **kwargs)

        # Otherwise, no Cloudflare anti-bot detected
        return resp

    def solve_cf_challenge(self, resp, **original_kwargs):
        body = resp.text
        parsed_url = urlparse(resp.url)
        domain = parsed_url.netloc
        submit_url = "%s://%s/cdn-cgi/l/chk_jschl" % (parsed_url.scheme, domain)

        cloudflare_kwargs = deepcopy(original_kwargs)
        params = cloudflare_kwargs.setdefault("params", {})
        headers = cloudflare_kwargs.setdefault("headers", {})
        headers["Referer"] = resp.url

        try:
            cf_delay = float(re.search('submit.*?(\d+)', body, re.DOTALL).group(1)) / 1000.0

            form_index = body.find('id="challenge-form"')
            if form_index == -1:
                raise Exception('CF form not found')
            sub_body = body[form_index:]

            s_match = re.search('name="s" value="(.+?)"', sub_body)
            if s_match:
                params["s"] = s_match.group(1)  # On older variants this parameter is absent.
            params["jschl_vc"] = re.search(r'name="jschl_vc" value="(\w+)"', sub_body).group(1)
            params["pass"] = re.search(r'name="pass" value="(.+?)"', sub_body).group(1)

            if body.find('id="cf-dn-', form_index) != -1:
                extra_div_expression = re.search('id="cf-dn-.*?>(.+?)<', sub_body).group(1)

            # Initial value.
            js_answer = self.cf_parse_expression(
                re.search('setTimeout\(function\(.*?:(.*?)}', body, re.DOTALL).group(1)
            )
            # Extract the arithmetic operations.
            builder = re.search("challenge-form'\);\s*;(.*);a.value", body, re.DOTALL).group(1)
            # Remove a function semicolon before splitting on semicolons, else it messes the order.
            lines = builder.replace(' return +(p)}();', '', 1).split(';')

            for line in lines:
                if len(line) and '=' in line:
                    heading, expression = line.split('=', 1)
                    if 'eval(eval(atob' in expression:
                        # Uses the expression in an external <div>.
                        expression_value = self.cf_parse_expression(extra_div_expression)
                    elif '(function(p' in expression:
                        # Expression + domain sampling function.
                        expression_value = self.cf_parse_expression(expression, domain)
                    else:
                        expression_value = self.cf_parse_expression(expression)
                    js_answer = self.cf_arithmetic_op(heading[-1], js_answer, expression_value)

            if '+ t.length' in body:
                js_answer += len(domain)  # Only older variants add the domain length.

            params["jschl_answer"] = '%.10f' % js_answer

        except Exception as e:
            # Something is wrong with the page.
            # This may indicate Cloudflare has changed their anti-bot
            # technique. If you see this and are running the latest version,
            # please open a GitHub issue so I can update the code accordingly.
            logging.error("[!] %s Unable to parse Cloudflare anti-bots page. "
                          "Try upgrading cloudflare-scrape, or submit a bug report "
                          "if you are running the latest version. Please read "
                          "https://github.com/Anorov/cloudflare-scrape#updates "
                          "before submitting a bug report." % e)
            raise

        # Cloudflare requires a delay before solving the challenge.
        # Always wait the full delay + 1s because of 'time.sleep()' imprecision.
        time.sleep(cf_delay + 1.0)

        # Requests transforms any request into a GET after a redirect,
        # so the redirect has to be handled manually here to allow for
        # performing other types of requests even as the first request.
        method = resp.request.method
        cloudflare_kwargs["allow_redirects"] = False

        redirect = self.request(method, submit_url, **cloudflare_kwargs)

        if 'Location' in redirect.headers:
            redirect_location = urlparse(redirect.headers["Location"])
            if not redirect_location.netloc:
                redirect_url = "%s://%s%s" % (parsed_url.scheme, domain, redirect_location.path)
                return self.request(method, redirect_url, **original_kwargs)
            return self.request(method, redirect.headers["Location"], **original_kwargs)
        else:
            return redirect

    def cf_sample_domain_function(self, func_expression, domain):
        parameter_start_index = func_expression.find('}(') + 2
        # Send the expression with the "+" char and enclosing parenthesis included, as they are
        # stripped inside ".cf_parse_expression()'.
        sample_index = self.cf_parse_expression(
            func_expression[parameter_start_index: func_expression.rfind(')))')]
        )
        return ord(domain[int(sample_index)])

    def cf_arithmetic_op(self, op, a, b):
        if op == '+':
            return a + b
        elif op == '/':
            return a / float(b)
        elif op == '*':
            return a * float(b)
        elif op == '-':
            return a - b
        else:
            raise Exception('Unknown operation')

    def cf_parse_expression(self, expression, domain=None):

        def _get_jsfuck_number(section):
            digit_expressions = section.replace('!+[]', '1').replace('+!![]', '1').replace('+[]', '0').split('+')
            return int(
                # Form a number string, with each digit as the sum of the values inside each parenthesis block.
                ''.join(
                    str(sum(int(digit_char) for digit_char in digit_expression[1:-1]))  # Strip the parenthesis.
                    for digit_expression in digit_expressions
                )
            )

        if '/' in expression:
            dividend, divisor = expression.split('/')
            dividend = dividend[2:-1]  # Strip the leading '+' char and the enclosing parenthesis.

            if domain:
                # 2019-04-02: At this moment, this extra domain sampling function always appears on the
                # divisor side, at the end.
                divisor_a, divisor_b = divisor.split('))+(')
                divisor_a = _get_jsfuck_number(divisor_a[5:])  # Left-strip the sequence of "(+(+(".
                divisor_b = self.cf_sample_domain_function(divisor_b, domain)
                return _get_jsfuck_number(dividend) / float(divisor_a + divisor_b)
            else:
                divisor = divisor[2:-1]
                return _get_jsfuck_number(dividend) / float(_get_jsfuck_number(divisor))
        else:
            return _get_jsfuck_number(expression[2:-1])

    @classmethod
    def create_scraper(cls, sess=None, **kwargs):
        """
        Convenience function for creating a ready-to-go requests.Session (subclass) object.
        """
        scraper = cls()

        if sess:
            attrs = ["auth", "cert", "cookies", "headers", "hooks", "params", "proxies", "data"]
            for attr in attrs:
                val = getattr(sess, attr, None)
                if val:
                    setattr(scraper, attr, val)

        return scraper

    ## Functions for integrating cloudflare-scrape with other applications and scripts

    @classmethod
    def get_tokens(cls, url, user_agent=None, **kwargs):
        scraper = cls.create_scraper()
        if user_agent:
            scraper.headers["User-Agent"] = user_agent

        try:
            resp = scraper.get(url, **kwargs)
            resp.raise_for_status()
        except Exception as e:
            logging.error("'%s' returned an error. Could not collect tokens." % url)
            raise

        domain = urlparse(resp.url).netloc
        cookie_domain = None

        for d in scraper.cookies.list_domains():
            if d.startswith(".") and d in ("." + domain):
                cookie_domain = d
                break
        else:
            raise ValueError(
                "Unable to find Cloudflare cookies. Does the site actually have Cloudflare IUAM (\"I'm Under Attack Mode\") enabled?")

        return ({
                    "__cfduid": scraper.cookies.get("__cfduid", "", domain=cookie_domain),
                    "cf_clearance": scraper.cookies.get("cf_clearance", "", domain=cookie_domain)
                },
                scraper.headers["User-Agent"]
        )

    def get_live_tokens(self, domain):
        for d in self.cookies.list_domains():
            if d.startswith(".") and d in ("." + domain):
                cookie_domain = d
                break
        else:
            raise ValueError(
                "Unable to find Cloudflare cookies. Does the site actually have Cloudflare IUAM (\"I'm Under Attack Mode\") enabled?")

        return ({
                    "__cfduid": self.cookies.get("__cfduid", "", domain=cookie_domain),
                    "cf_clearance": self.cookies.get("cf_clearance", "", domain=cookie_domain)
                },
                self.headers["User-Agent"]
        )

    @classmethod
    def get_cookie_string(cls, url, user_agent=None, **kwargs):
        """
        Convenience function for building a Cookie HTTP header value.
        """
        tokens, user_agent = cls.get_tokens(url, user_agent=user_agent, **kwargs)
        return "; ".join("=".join(pair) for pair in tokens.items()), user_agent


create_scraper = CloudflareScraper.create_scraper
get_tokens = CloudflareScraper.get_tokens
get_cookie_string = CloudflareScraper.get_cookie_string
