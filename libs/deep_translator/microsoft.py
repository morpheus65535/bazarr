# -*- coding: utf-8 -*-

import requests
import logging
import sys

from .constants import BASE_URLS, MICROSOFT_CODES_TO_LANGUAGES
from .exceptions import LanguageNotSupportedException, ServerException, MicrosoftAPIerror


class MicrosoftTranslator:
    """
    the class that wraps functions, which use the Microsoft translator under the hood to translate word(s)
    """

    _languages = MICROSOFT_CODES_TO_LANGUAGES
    supported_languages = list(_languages.values())

    def __init__(self, api_key=None, region=None, source=None, target=None, proxies=None, **kwargs):
        """
        @params api_key and target are the required params
        @param api_key: your Microsoft API key
        @param region: your Microsoft Location
        """
        if not api_key:
            raise ServerException(401)
        else:
            self.api_key = api_key

        self.proxies = proxies
        self.headers = {
            "Ocp-Apim-Subscription-Key": self.api_key,
            "Content-type": "application/json",
        }
        # region is not required but very common and goes to headers if passed
        if region:
            self.region = region
            self.headers["Ocp-Apim-Subscription-Region"] = self.region

        if not target:
            raise ServerException(401)
        else:
            if type(target) is str:
                self.target = target.lower()
            else:
                self.target = [i.lower() for i in target]
            if self.is_language_supported(self.target):
                self.target = self._map_language_to_code(self.target)

        self.url_params = {'to': self.target, **kwargs}

        if source:
            self.source = source.lower()
            if self.is_language_supported(self.source):
                self.source = self._map_language_to_code(self.source)
            self.url_params['from'] = self.source

        self.__base_url = BASE_URLS.get("MICROSOFT_TRANSLATE")

    @staticmethod
    def get_supported_languages(as_dict=False, **kwargs):
        """
        return the languages supported by the microsoft translator
        @param as_dict: if True, the languages will be returned as a dictionary mapping languages to their abbreviations
        @return: list or dict
        """
        return MicrosoftTranslator.supported_languages if not as_dict else MicrosoftTranslator._languages

    def _map_language_to_code(self, language, **kwargs):
        """
        map the language to its corresponding code (abbreviation) if the language was passed by its full name by the user
        @param language: a string (if 1 lang) or a list (if multiple langs)
        @return: mapped value of the language or raise an exception if the language is not supported
        """
        if type(language) is str:
            language = [language]
        for lang in language:
            if lang in self._languages.values():
                yield lang
            elif lang in self._languages.keys():
                yield self._languages[lang]
            else:
                raise LanguageNotSupportedException(lang)

    def is_language_supported(self, language, **kwargs):
        """
        check if the language is supported by the translator
        @param language: a string (if 1 lang) or a list (if multiple langs)
        @return: bool or raise an Exception
        """
        if type(language) is str:
            language = [language]
        for lang in language:
            if lang not in self._languages.keys():
                if lang not in self._languages.values():
                    raise LanguageNotSupportedException(lang)
        return True

    def translate(self, text, **kwargs):
        """
        function that uses microsoft translate to translate a text
        @param text: desired text to translate
        @return: str: translated text
        """
        # a body must be a list of dicts to process multiple texts;
        # I have not added multiple text processing here since it is covered by the translate_batch method
        valid_microsoft_json = [{'text': text}]
        try:
            requested = requests.post(self.__base_url,
                                      params=self.url_params,
                                      headers=self.headers,
                                      json=valid_microsoft_json,
                                      proxies=self.proxies)
        except requests.exceptions.RequestException:
            exc_type, value, traceback = sys.exc_info()
            logging.warning(f"Returned error: {exc_type.__name__}")

        # Where Microsoft API responds with an api error, it returns a dict in response.json()
        if type(requested.json()) is dict:
            error_message = requested.json()['error']
            raise MicrosoftAPIerror(error_message)
        # Where it responds with a translation, its response.json() is a list e.g. [{'translations': [{'text': 'Hello world!', 'to': 'en'}]}]
        elif type(requested.json()) is list:
            all_translations = [i['text'] for i in requested.json()[0]['translations']]
            return "\n".join(all_translations)

    def translate_file(self, path, **kwargs):
        """
        translate from a file
        @param path: path to file
        @return: translated text
        """
        try:
            with open(path, 'r', encoding='utf-8') as f:
                text = f.read().strip()
            return self.translate(text)
        except Exception as e:
            raise e

    def translate_batch(self, batch, **kwargs):
        """
        translate a batch of texts
        @param batch: list of texts to translate
        @return: list of translations
        """
        return [self.translate(text, **kwargs) for text in batch]
