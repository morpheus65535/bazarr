
import requests
from requests.utils import requote_uri
from deep_translator.constants import BASE_URLS
from deep_translator.exceptions import (RequestError,
                                        ServerException, TranslationNotFound, TooManyRequests)


class QCRI(object):
    """
    class that wraps functions, which use the QRCI translator under the hood to translate word(s)
    """

    def __init__(self, api_key=None):
        """
        @param api_key: your qrci api key. Get one for free here https://mt.qcri.org/api/v1/ref
        """

        if not api_key:
            raise ServerException(401)
        self.__base_url = BASE_URLS.get("QCRI")

        self.api_key = api_key
        self.api_endpoints = {
            "get_languages": "getLanguagePairs",
            "get_domains": "getDomains",
            "translate": "translate",
        }

        self.params = {
            "key": self.api_key
        }

    def _get(self, endpoint, params=None, return_text=True):
        if not params:
            params = self.params
        try:
            res = requests.get(self.__base_url.format(endpoint=self.api_endpoints[endpoint]), params=params)
            return res.text if return_text else res
        except Exception as e:
            raise e

    def get_supported_languages(self):

        pairs = self._get("get_languages")
        return pairs

    @property
    def languages(self):
        return self.get_supported_languages()

    def get_domains(self):
        domains = self._get("get_domains")
        return domains

    @property
    def domains(self):
        return self.get_domains()

    def translate(self, source, target, domain, text):
        params = {
            "key": self.api_key,
            "langpair": "{}-{}".format(source, target),
            "domain": domain,
            "text": text
        }
        try:
            response = self._get("translate", params=params, return_text=False)
        except ConnectionError:
            raise ServerException(503)

        else:
            if response.status_code != 200:
                ServerException(response.status_code)
            else:
                res = response.json()
                translation = res["translatedText"]
                if not translation:
                    raise TranslationNotFound(text)
                return translation

    def translate_batch(self, source, target, domain, batch):
        """
        translate a batch of texts
        @param source: source language
        @param target: target language
        @param batch: list of texts to translate
        @return: list of translations
        """
        return [self.translate(source, target, domain, text) for text in batch]

