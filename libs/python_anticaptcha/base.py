import requests
import time

from six.moves.urllib_parse import urljoin
from .exceptions import AnticaptchaException

SLEEP_EVERY_CHECK_FINISHED = 3
MAXIMUM_JOIN_TIME = 60 * 5


class Job(object):
    client = None
    task_id = None
    _last_result = None

    def __init__(self, client, task_id):
        self.client = client
        self.task_id = task_id

    def _update(self):
        self._last_result = self.client.getTaskResult(self.task_id)

    def check_is_ready(self):
        self._update()
        return self._last_result['status'] == 'ready'

    def get_solution_response(self):  # Recaptcha
        return self._last_result['solution']['gRecaptchaResponse']

    def get_token_response(self):  # Funcaptcha
        return self._last_result['solution']['token']

    def get_answers(self):
        return self._last_result['solution']['answers']

    def get_captcha_text(self):  # Image
        return self._last_result['solution']['text']

    def report_incorrect(self):
        return self.client.reportIncorrectImage(self.task_id)

    def join(self, maximum_time=None):
        elapsed_time = 0
        maximum_time = maximum_time or MAXIMUM_JOIN_TIME
        while not self.check_is_ready():
            time.sleep(SLEEP_EVERY_CHECK_FINISHED)
            elapsed_time += SLEEP_EVERY_CHECK_FINISHED
            if elapsed_time is not None and elapsed_time > maximum_time:
                raise AnticaptchaException(None, 250,
                                           "The execution time exceeded a maximum time of {} seconds. It takes {} seconds.".format(
                                               maximum_time, elapsed_time))


class AnticaptchaClient(object):
    client_key = None
    CREATE_TASK_URL = "/createTask"
    TASK_RESULT_URL = "/getTaskResult"
    BALANCE_URL = "/getBalance"
    REPORT_IMAGE_URL = "/reportIncorrectImageCaptcha"
    SOFT_ID = 847
    language_pool = "en"

    def __init__(self, client_key, language_pool="en", host="api.anti-captcha.com", use_ssl=True):
        self.client_key = client_key
        self.language_pool = language_pool
        self.base_url = "{proto}://{host}/".format(proto="https" if use_ssl else "http",
                                                   host=host)
        self.session = requests.Session()

    @property
    def client_ip(self):
        if not hasattr(self, '_client_ip'):
            self._client_ip = self.session.get('http://httpbin.org/ip').json()['origin']
        return self._client_ip

    def _check_response(self, response):
        if response.get('errorId', False) == 11:
            response['errorDescription'] = "{} Your missing IP address is {}.".format(response['errorDescription'],
                                                                                      self.client_ip)
        if response.get('errorId', False):
            raise AnticaptchaException(response['errorId'],
                                       response['errorCode'],
                                       response['errorDescription'])

    def createTask(self, task):
        request = {"clientKey": self.client_key,
                   "task": task.serialize(),
                   "softId": self.SOFT_ID,
                   "languagePool": self.language_pool,
                   }
        response = self.session.post(urljoin(self.base_url, self.CREATE_TASK_URL), json=request).json()
        self._check_response(response)
        return Job(self, response['taskId'])

    def getTaskResult(self, task_id):
        request = {"clientKey": self.client_key,
                   "taskId": task_id}
        response = self.session.post(urljoin(self.base_url, self.TASK_RESULT_URL), json=request).json()
        self._check_response(response)
        return response

    def getBalance(self):
        request = {"clientKey": self.client_key}
        response = self.session.post(urljoin(self.base_url, self.BALANCE_URL), json=request).json()
        self._check_response(response)
        return response['balance']

    def reportIncorrectImage(self, task_id):
        request = {"clientKey": self.client_key,
                   "taskId": task_id
                   }
        response = self.session.post(urljoin(self.base_url, self.REPORT_IMAGE_URL), json=request).json()
        self._check_response(response)
        return response.get('status', False) != False
