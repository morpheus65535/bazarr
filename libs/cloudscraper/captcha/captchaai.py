from __future__ import absolute_import

import requests
try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

from ..exceptions import (
    CaptchaServiceUnavailable,
    CaptchaAPIError,
    CaptchaTimeout,
    CaptchaParameter,
    CaptchaBadJobID,
    CaptchaReportError
)

try:
    import polling2
except ImportError:
    raise ImportError("Please install the python module 'polling2' via pip")

from . import Captcha


class captchaSolver(Captcha):

    def __init__(self):
        super(captchaSolver, self).__init__('captchaai')
        self.host = 'https://ocr.captchaai.com'
        self.session = requests.Session()

    # ------------------------------------------------------------------------------- #

    @staticmethod
    def checkErrorStatus(response, request_type):
        if response.status_code in [500, 502]:
            raise CaptchaServiceUnavailable(f'CaptchaAI: Server Side Error {response.status_code}')

        errors = {
            'in.php': {
                "ERROR_WRONG_USER_KEY": "You've provided api_key parameter value in incorrect format.",
                "ERROR_KEY_DOES_NOT_EXIST": "The api_key you've provided does not exists.",
                "ERROR_ZERO_BALANCE": "You don't have sufficient funds on your account.",
                "ERROR_PAGEURL": "pageurl parameter is missing in your request.",
                "ERROR_NO_SLOT_AVAILABLE": "No Slots Available.",
                "ERROR_IP_NOT_ALLOWED": "The request is sent from the IP that is not on the list of your allowed IPs.",
                "IP_BANNED": "Your IP address is banned due to many frequent attempts to access the server.",
                "ERROR_BAD_TOKEN_OR_PAGEURL":
                    "Invalid pair of googlekey and pageurl when sending ReCaptcha V2.",
                "ERROR_GOOGLEKEY": "The sitekey value provided in your request is incorrect: blank or malformed.",
                "MAX_USER_TURN": "You made more than 60 requests within 3 seconds."
            },
            'res.php': {
                "ERROR_CAPTCHA_UNSOLVABLE": "We are unable to solve your captcha. We will not charge you for that request.",
                "ERROR_WRONG_USER_KEY": "You've provided api_key parameter value in incorrect format.",
                "ERROR_KEY_DOES_NOT_EXIST": "The api_key you've provided does not exists.",
                "ERROR_WRONG_ID_FORMAT": "You've provided captcha ID in wrong format. The ID can contain numbers only.",
                "ERROR_WRONG_CAPTCHA_ID": "You've provided incorrect captcha ID.",
                "REPORT_NOT_RECORDED": "Error is returned to your complain request if you already complained lots of correctly solved captchas.",
                "ERROR_TOKEN_EXPIRED": "The challenge value you provided is expired.",
                "ERROR_EMPTY_ACTION": "Action parameter is missing or no value is provided for action parameter."
            }
        }

        rPayload = response.json()
        if rPayload.get('status') == 0 and rPayload.get('request') in errors.get(request_type):
            raise CaptchaAPIError(
                f"{rPayload['request']} {errors.get(request_type).get(rPayload['request'])}"
            )

    # ------------------------------------------------------------------------------- #

    def reportJob(self, jobID):
        if not jobID:
            raise CaptchaBadJobID(
                "CaptchaAI: Error bad job id to request Captcha."
            )

        def _checkRequest(response):
            self.checkErrorStatus(response, 'res.php')
            if response.ok and response.json().get('status') == 1:
                return response
            return None

        response = polling2.poll(
            lambda: self.session.get(
                f'{self.host}/res.php',
                params={
                    'key': self.api_key,
                    'action': 'reportbad',
                    'id': jobID,
                    'json': '1'
                },
                timeout=30
            ),
            check_success=_checkRequest,
            step=5,
            timeout=180
        )

        if response:
            return True
        else:
            raise CaptchaReportError(
                "CaptchaAI: Error - Failed to report bad Captcha solve."
            )

    # ------------------------------------------------------------------------------- #

    def requestJob(self, jobID):
        if not jobID:
            raise CaptchaBadJobID("CaptchaAI: Error bad job id to request Captcha.")

        def _checkRequest(response):
            self.checkErrorStatus(response, 'res.php')
            if response.ok and response.json().get('status') == 1:
                return response
            return None

        response = polling2.poll(
            lambda: self.session.get(
                f'{self.host}/res.php',
                params={
                    'key': self.api_key,
                    'action': 'get',
                    'id': jobID,
                    'json': '1'
                },
                timeout=30
            ),
            check_success=_checkRequest,
            step=5,
            timeout=180
        )

        if response:
            return response.json().get('request')
        else:
            raise CaptchaTimeout(
                "CaptchaAI: Error failed to solve Captcha."
            )

    # ------------------------------------------------------------------------------- #

    def requestSolve(self, captchaType, url, siteKey):
        def _checkRequest(response):
            self.checkErrorStatus(response, 'in.php')
            if response.ok and response.json().get("status") == 1 and response.json().get('request'):
                return response
            return None

        data = {
            'key': self.api_key,
            'pageurl': url,
            'json': 1
        }

        # CaptchaAI supports reCAPTCHA (and Cloudflare Turnstile / image OCR) but not hCaptcha.
        if captchaType != 'reCaptcha':
            raise CaptchaParameter(
                f"CaptchaAI: Unsupported captcha type '{captchaType}'. CaptchaAI does not support hCaptcha."
            )

        data.update(
            {
                'method': 'userrecaptcha',
                'googlekey': siteKey
            }
        )

        if self.proxy:
            data.update(
                {
                    'proxy': self.proxy,
                    'proxytype': self.proxyType
                }
            )

        response = polling2.poll(
            lambda: self.session.post(
                f'{self.host}/in.php',
                data=data,
                allow_redirects=False,
                timeout=30
            ),
            check_success=_checkRequest,
            step=5,
            timeout=180
        )

        if response:
            return response.json().get('request')
        else:
            raise CaptchaBadJobID(
                'CaptchaAI: Error no job id was returned.'
            )

    # ------------------------------------------------------------------------------- #

    def getCaptchaAnswer(self, captchaType, url, siteKey, captchaParams):
        jobID = None

        if not captchaParams.get('api_key'):
            raise CaptchaParameter(
                "CaptchaAI: Missing api_key parameter."
            )

        self.api_key = captchaParams.get('api_key')

        if captchaParams.get('proxy') and not captchaParams.get('no_proxy'):
            hostParsed = urlparse(captchaParams.get('proxy', {}).get('https'))

            if not hostParsed.scheme:
                raise CaptchaParameter('Cannot parse proxy correctly, bad scheme')

            if not hostParsed.netloc:
                raise CaptchaParameter('Cannot parse proxy correctly, bad netloc')

            self.proxyType = hostParsed.scheme
            self.proxy = hostParsed.netloc
        else:
            self.proxy = None

        try:
            jobID = self.requestSolve(captchaType, url, siteKey)
            return self.requestJob(jobID)
        except polling2.TimeoutException:
            try:
                if jobID:
                    self.reportJob(jobID)
            except polling2.TimeoutException:
                raise CaptchaTimeout(
                    f"CaptchaAI: Captcha solve took to long and also failed reporting the job the job id {jobID}."
                )

            raise CaptchaTimeout(
                f"CaptchaAI: Captcha solve took to long to execute job id {jobID}, aborting."
            )


# ------------------------------------------------------------------------------- #

captchaSolver()
