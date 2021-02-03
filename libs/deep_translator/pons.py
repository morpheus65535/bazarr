"""
pons translator API
"""
from bs4 import BeautifulSoup
import requests
from deep_translator.constants import BASE_URLS, PONS_LANGUAGES_TO_CODES, PONS_CODES_TO_LANGUAGES
from deep_translator.exceptions import (LanguageNotSupportedException,
                                        TranslationNotFound,
                                        NotValidPayload,
                                        ElementNotFoundInGetRequest,
                                        RequestError,
                                        TooManyRequests)
from deep_translator.parent import BaseTranslator
from requests.utils import requote_uri


class PonsTranslator(BaseTranslator):
    """
    class that uses PONS translator to translate words
    """
    _languages = PONS_LANGUAGES_TO_CODES
    supported_languages = list(_languages.keys())

    def __init__(self, source, target="english"):
        """
        @param source: source language to translate from
        @param target: target language to translate to
        """
        self.__base_url = BASE_URLS.get("PONS")

        if self.is_language_supported(source, target):
            self._source, self._target = self._map_language_to_code(source, target)

        super().__init__(base_url=self.__base_url,
                         source=self._source,
                         target=self._target,
                         payload_key=None,
                         element_tag='div',
                         element_query={"class": "target"}
                         )

    @staticmethod
    def get_supported_languages(as_dict=False):
        """
          return the supported languages by the linguee translator
          @param as_dict: if True, the languages will be returned as a dictionary mapping languages to their abbreviations
          @return: list or dict
          """
        return PonsTranslator.supported_languages if not as_dict else PonsTranslator._languages

    def _map_language_to_code(self, *languages, **kwargs):
        """
           map language to its corresponding code (abbreviation) if the language was passed by its full name by the user
           @param languages: list of languages
           @return: mapped value of the language or raise an exception if the language is not supported
        """
        for language in languages:
            if language in self._languages.values():
                yield PONS_CODES_TO_LANGUAGES[language]
            elif language in self._languages.keys():
                yield language
            else:
                raise LanguageNotSupportedException(language)

    def is_language_supported(self, *languages, **kwargs):
        """
         check if the language is supported by the translator
         @param languages: list of languages
         @return: bool or raise an Exception
         """
        for lang in languages:
            if lang not in self._languages.keys():
                if lang not in self._languages.values():
                    raise LanguageNotSupportedException(lang)
        return True

    def translate(self, word, return_all=False, **kwargs):
        """
        function that uses PONS to translate a word
        @param word: word to translate
        @type word: str
        @param return_all: set to True to return all synonym of the translated word
        @type return_all: bool
        @return: str: translated word
        """
        if self._validate_payload(word, max_chars=50):
            url = "{}{}-{}/{}".format(self.__base_url, self._source, self._target, word)
            url = requote_uri(url)
            response = requests.get(url)

            if response.status_code == 429:
                raise TooManyRequests()

            if response.status_code != 200:
                raise RequestError()

            soup = BeautifulSoup(response.text, 'html.parser')
            elements = soup.findAll(self._element_tag, self._element_query)

            if not elements:
                raise ElementNotFoundInGetRequest(word)

            filtered_elements = []
            for el in elements:
                temp = ''
                for e in el.findAll('a'):
                    if e.parent.name == 'div':
                        if e and "/translate/{}-{}/".format(self._target, self._source) in e.get('href'):
                            temp += e.get_text() + ' '
                filtered_elements.append(temp)

            if not filtered_elements:
                raise ElementNotFoundInGetRequest(word)

            word_list = [word for word in filtered_elements if word and len(word) > 1]

            if not word_list:
                raise TranslationNotFound(word)

            return word_list if return_all else word_list[0]

    def translate_words(self, words, **kwargs):
        """
        translate a batch of words together by providing them in a list
        @param words: list of words you want to translate
        @param kwargs: additional args
        @return: list of translated words
        """
        if not words:
            raise NotValidPayload(words)

        translated_words = []
        for word in words:
            translated_words.append(self.translate(payload=word))
        return translated_words

