
import requests
from .constants import BASE_URLS, QCRI_LANGUAGE_TO_CODE
from .exceptions import (ServerException, TranslationNotFound)

class QCRI(object):
    """
    class that wraps functions, which use the QRCI translator under the hood to translate word(s)
    """

    def __init__(self, api_key=None, source="en", target="en", **kwargs):
        """
        @param api_key: your qrci api key. Get one for free here https://mt.qcri.org/api/v1/ref
        """

        if not api_key:
            raise ServerException(401)
        self.__base_url = BASE_URLS.get("QCRI")
        self.source = source
        self.target = target
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

    @staticmethod
    def get_supported_languages(as_dict=False, **kwargs):
        # Have no use for this as the format is not what we need
        # Save this for whenever
        # pairs = self._get("get_languages")
        # Using a this one instead
        return [*QCRI_LANGUAGE_TO_CODE.keys()] if not as_dict else QCRI_LANGUAGE_TO_CODE

    @property
    def languages(self):
        return self.get_supported_languages()

    def get_domains(self):
        domains = self._get("get_domains")
        return domains

    @property
    def domains(self):
        return self.get_domains()

    def translate(self, text, domain, **kwargs):
        params = {
            "key": self.api_key,
            "langpair": "{}-{}".format(self.source, self.target),
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
                translation = res.get("translatedText")
                if not translation:
                    raise TranslationNotFound(text)
                return translation

    def translate_batch(self, batch, domain, **kwargs):
        """
        translate a batch of texts
        @domain: domain
        @param batch: list of texts to translate
        @return: list of translations
        """
        return [self.translate(domain, text, **kwargs) for text in batch]

