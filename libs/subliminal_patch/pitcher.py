# coding=utf-8

import os
import time
import logging
import json
from subliminal.cache import region
from dogpile.cache.api import NO_VALUE
from python_anticaptcha import AnticaptchaClient, NoCaptchaTaskProxylessTask, NoCaptchaTask, AnticaptchaException,\
    Proxy
from deathbycaptcha import SocketClient as DBCClient, DEFAULT_TOKEN_TIMEOUT


logger = logging.getLogger(__name__)


class PitcherRegistry(object):
    pitchers = []
    pitchers_by_key = {}

    def register(self, cls):
        idx = len(self.pitchers)
        self.pitchers.append(cls)
        key = "%s_%s" % (cls.name, cls.needs_proxy)
        key_by_source = "%s_%s" % (cls.source, cls.needs_proxy)
        self.pitchers_by_key[key] = idx
        self.pitchers_by_key[key_by_source] = idx
        return cls

    def get_pitcher(self, name_or_site=None, with_proxy=False):
        name_or_site = name_or_site or os.environ.get("ANTICAPTCHA_CLASS")
        if not name_or_site:
            raise Exception("AntiCaptcha class not given, exiting")

        key = "%s_%s" % (name_or_site, with_proxy)

        if key not in self.pitchers_by_key:
            raise Exception("Pitcher %s not found (proxy: %s)" % (name_or_site, with_proxy))

        return self.pitchers[self.pitchers_by_key.get(key)]


registry = pitchers = PitcherRegistry()


class Pitcher(object):
    name = None
    source = None
    needs_proxy = False
    tries = 3
    job = None
    client = None
    client_key = None
    website_url = None
    website_key = None
    website_name = None
    solve_time = None
    success = False

    def __init__(self, website_name, website_url, website_key, tries=3, client_key=None, *args, **kwargs):
        self.tries = tries
        self.client_key = client_key or os.environ.get("ANTICAPTCHA_ACCOUNT_KEY")
        if not self.client_key:
            raise Exception("AntiCaptcha key not given, exiting")

        self.website_name = website_name
        self.website_key = website_key
        self.website_url = website_url
        self.success = False
        self.solve_time = None

    def get_client(self):
        raise NotImplementedError

    def get_job(self):
        raise NotImplementedError

    def _throw(self):
        self.client = self.get_client()
        self.job = self.get_job()

    def throw(self):
        t = time.time()
        data = self._throw()
        if self.success:
            self.solve_time = time.time() - t
            logger.info("%s: Solving took %ss", self.website_name, int(self.solve_time))
        return data


@registry.register
class AntiCaptchaProxyLessPitcher(Pitcher):
    name = "AntiCaptchaProxyLess"
    source = "anti-captcha.com"
    host = "api.anti-captcha.com"
    language_pool = "en"
    tries = 5
    use_ssl = True
    is_invisible = False

    def __init__(self, website_name, website_url, website_key, tries=3, host=None, language_pool=None,
                 use_ssl=True, is_invisible=False, *args, **kwargs):
        super(AntiCaptchaProxyLessPitcher, self).__init__(website_name, website_url, website_key, tries=tries, *args,
                                                          **kwargs)
        self.host = host or self.host
        self.language_pool = language_pool or self.language_pool
        self.use_ssl = use_ssl
        self.is_invisible = is_invisible

    def get_client(self):
        return AnticaptchaClient(self.client_key, self.language_pool, self.host, self.use_ssl)

    def get_job(self):
        task = NoCaptchaTaskProxylessTask(website_url=self.website_url, website_key=self.website_key,
                                          is_invisible=self.is_invisible)
        return self.client.createTask(task)

    def _throw(self):
        for i in range(self.tries):
            try:
                super(AntiCaptchaProxyLessPitcher, self)._throw()
                self.job.join()
                ret = self.job.get_solution_response()
                if ret:
                    self.success = True
                    return ret
            except AnticaptchaException as e:
                if i >= self.tries - 1:
                    logger.error("%s: Captcha solving finally failed. Exiting", self.website_name)
                    return

                if e.error_code == 'ERROR_ZERO_BALANCE':
                    logger.error("%s: No balance left on captcha solving service. Exiting", self.website_name)
                    return

                elif e.error_code == 'ERROR_NO_SLOT_AVAILABLE':
                    logger.info("%s: No captcha solving slot available, retrying", self.website_name)
                    time.sleep(5.0)
                    continue

                elif e.error_code == 'ERROR_KEY_DOES_NOT_EXIST':
                    logger.error("%s: Bad AntiCaptcha API key", self.website_name)
                    return

                elif e.error_id is None and e.error_code == 250:
                    # timeout
                    if i < self.tries:
                        logger.info("%s: Captcha solving timed out, retrying", self.website_name)
                        time.sleep(1.0)
                        continue
                    else:
                        logger.error("%s: Captcha solving timed out three times; bailing out", self.website_name)
                        return
                raise


@registry.register
class AntiCaptchaPitcher(AntiCaptchaProxyLessPitcher):
    name = "AntiCaptcha"
    proxy = None
    needs_proxy = True
    user_agent = None
    cookies = None

    def __init__(self, *args, **kwargs):
        self.proxy = Proxy.parse_url(kwargs.pop("proxy"))
        self.user_agent = kwargs.pop("user_agent")
        cookies = kwargs.pop("cookies", {})
        if isinstance(cookies, dict):
            self.cookies = ";".join(["%s=%s" % (k, v) for k, v in cookies.iteritems()])

        super(AntiCaptchaPitcher, self).__init__(*args, **kwargs)

    def get_job(self):
        task = NoCaptchaTask(website_url=self.website_url, website_key=self.website_key, proxy=self.proxy,
                             user_agent=self.user_agent, cookies=self.cookies, is_invisible=self.is_invisible)
        return self.client.createTask(task)


@registry.register
class DBCProxyLessPitcher(Pitcher):
    name = "DeathByCaptchaProxyLess"
    source = "deathbycaptcha.com"
    username = None
    password = None

    def __init__(self, website_name, website_url, website_key,
                 timeout=DEFAULT_TOKEN_TIMEOUT, tries=3, *args, **kwargs):
        super(DBCProxyLessPitcher, self).__init__(website_name, website_url, website_key, tries=tries)

        self.username, self.password = self.client_key.split(":", 1)
        self.timeout = timeout

    def get_client(self):
        return DBCClient(self.username, self.password)

    def get_job(self):
        pass

    @property
    def payload_dict(self):
        return {
            "googlekey": self.website_key,
            "pageurl": self.website_url
        }

    def _throw(self):
        super(DBCProxyLessPitcher, self)._throw()
        payload = json.dumps(self.payload_dict)
        for i in range(self.tries):
            try:
                #balance = self.client.get_balance()
                data = self.client.decode(timeout=self.timeout, type=4, token_params=payload)
                if data and data["is_correct"] and data["text"]:
                    self.success = True
                    return data["text"]
            except:
                raise


@registry.register
class DBCPitcher(DBCProxyLessPitcher):
    name = "DeathByCaptcha"
    proxy = None
    needs_proxy = True
    proxy_type = "HTTP"

    def __init__(self, *args, **kwargs):
        self.proxy = kwargs.pop("proxy")
        super(DBCPitcher, self).__init__(*args, **kwargs)

    @property
    def payload_dict(self):
        payload = super(DBCPitcher, self).payload_dict
        payload.update({
            "proxytype": self.proxy_type,
            "proxy": self.proxy
        })
        return payload


def load_verification(site_name, session, callback=lambda x: None):
    ccks = region.get("%s_data" % site_name, expiration_time=15552000)  # 6m
    if ccks != NO_VALUE:
        cookies, user_agent = ccks
        logger.debug("%s: Re-using previous user agent: %s", site_name.capitalize(), user_agent)
        session.headers["User-Agent"] = user_agent
        try:
            session.cookies._cookies.update(cookies)
            return callback(region)
        except:
            return False
    return False


def store_verification(site_name, session):
    region.set("%s_data" % site_name, (session.cookies._cookies, session.headers["User-Agent"]))
