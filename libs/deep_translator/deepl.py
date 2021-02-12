
import requests
from requests.utils import requote_uri
from deep_translator.constants import BASE_URLS
from deep_translator.exceptions import (RequestError,
                                        ServerException, TranslationNotFound, TooManyRequests)


class DeepL(object):
    """
    class that wraps functions, which use the DeepL translator under the hood to translate word(s)
    """

    def __init__(self, api_key=None):
        """
        @param api_key: your DeepL api key. Get one here: https://www.deepl.com/docs-api/accessing-the-api/
        """

        if not api_key:
            raise ServerException(401)
        self.version = 'v2'
        self.api_key = api_key
        self.__base_url = BASE_URLS.get("DEEPL").format(version=self.version)

    def translate(self, source, target, text):
        params = {
            "auth_key": self.api_key,
            "target_lang": target,
            "source_lang": source,
            "text": text
        }
        try:
            response = requests.get(self.__base_url, params=params)
        except ConnectionError:
            raise ServerException(503)

        else:
            if response.status_code != 200:
                ServerException(response.status_code)
            else:
                res = response.json()
                if not res:
                    raise TranslationNotFound(text)
                return res

    def translate_batch(self, source, target, batch):
        """
        translate a batch of texts
        @param source: source language
        @param target: target language
        @param batch: list of texts to translate
        @return: list of translations
        """
        return [self.translate(source, target, text) for text in batch]


if __name__ == '__main__':
    d = DeepL(api_key="key")
    print(d)
