"""
Yandex translator API
"""
import requests
from requests import exceptions
from deep_translator.constants import BASE_URLS
from deep_translator.exceptions import (RequestError,
                                        ServerException, TranslationNotFound, TooManyRequests)


class YandexTranslator(object):
    """
    class that wraps functions, which use the yandex translator under the hood to translate word(s)
    """

    def __init__(self, api_key=None):
        """
        @param api_key: your yandex api key
        """
        if not api_key:
            raise ServerException(401)
        self.__base_url = BASE_URLS.get("YANDEX")

        self.api_key = api_key
        self.api_version = "v1.5"
        self.api_endpoints = {
            "langs": "getLangs",
            "detect": "detect",
            "translate": "translate",
        }

    def get_supported_languages(self):
        return set(x.split("-")[0] for x in self.dirs)

    @property
    def languages(self):
        return self.get_supported_languages()

    @property
    def dirs(self, proxies=None):

        try:
            url = self.__base_url.format(version=self.api_version, endpoint="getLangs")
            print("url: ", url)
            response = requests.get(url, params={"key": self.api_key}, proxies=proxies)
        except requests.exceptions.ConnectionError:
            raise ServerException(503)
        else:
            data = response.json()

        if response.status_code != 200:
            raise ServerException(response.status_code)
        return data.get("dirs")

    def detect(self, text, proxies=None):
        response = None
        params = {
            "text": text,
            "format": "plain",
            "key": self.api_key,
        }
        try:
            url = self.__base_url.format(version=self.api_version, endpoint="detect")
            response = requests.post(url, data=params, proxies=proxies)

        except RequestError:
            raise
        except ConnectionError:
            raise ServerException(503)
        except ValueError:
            raise ServerException(response.status_code)
        else:
            response = response.json()
        language = response['lang']
        status_code = response['code']
        if status_code != 200:
            raise RequestError()
        elif not language:
            raise ServerException(501)
        return language

    def translate(self, source, target, text, proxies=None):
        params = {
            "text": text,
            "format": "plain",
            "lang": target if source == "auto" else "{}-{}".format(source, target),
            "key": self.api_key
        }
        try:
            url = self.__base_url.format(version=self.api_version, endpoint="translate")
            response = requests.post(url, data=params, proxies=proxies)
        except ConnectionError:
            raise ServerException(503)
        else:
            response = response.json()

        if response['code'] == 429:
            raise TooManyRequests()

        if response['code'] != 200:
            raise ServerException(response['code'])

        if not response['text']:
            raise TranslationNotFound()

        return response['text']

    def translate_file(self, source, target, path):
        """
        translate from a file
        @param source: source language
        @param target: target language
        @param path: path to file
        @return: translated text
        """
        try:
            with open(path) as f:
                text = f.read()

            return self.translate(source, target, text)
        except Exception as e:
            raise e

    def translate_batch(self, source, target, batch):
        """
        translate a batch of texts
        @param source: source language
        @param target: target language
        @param batch: list of texts to translate
        @return: list of translations
        """
        return [self.translate(source, target, text) for text in batch]
