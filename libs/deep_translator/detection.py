"""
language detection API
"""
import requests
from deep_translator.configs import config
from requests.exceptions import HTTPError


def get_request_body(text, api_key, *args):
    """
    send a request and return the response body parsed as dictionary

    @param text: target text that you want to detect its language
    @type text: str
    @type api_key: str
    @param api_key: your private API key

    """
    if not api_key:
        raise Exception("you need to get an API_KEY for this to work. "
                        "Get one for free here: https://detectlanguage.com/documentation")
    if not text:
        raise Exception("Please provide an input text")

    else:
        try:
            headers = config['headers']
            headers['Authorization'] = headers['Authorization'].format(api_key)
            response = requests.post(config['url'],
                                     json={'q': text},
                                     headers=headers)

            body = response.json().get('data')
            return body

        except HTTPError as e:
            print("Error occured while requesting from server: ", e.args)
            raise e


def single_detection(text, api_key=None, detailed=False, *args, **kwargs):
    """
    function responsible for detecting the language from a text

    @param text: target text that you want to detect its language
    @type text: str
    @type api_key: str
    @param api_key: your private API key
    @param detailed: set to True if you want to get detailed information about the detection process
    """
    body = get_request_body(text, api_key)
    detections = body.get('detections')
    if detailed:
        return detections[0]

    lang = detections[0].get('language', None)
    if lang:
        return lang


def batch_detection(text_list, api_key, detailed=False, *args):
    """
    function responsible for detecting the language from a text

    @param text_list: target batch that you want to detect its language
    @param api_key: your private API key
    @param detailed: set to True if you want to get detailed information about the detection process
    """
    body = get_request_body(text_list, api_key)
    detections = body.get('detections')
    res = [obj[0] for obj in detections]
    if detailed:
        return res
    else:
        return [obj['language'] for obj in res]

