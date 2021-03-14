"""
mymemory translator API
"""
import logging
import warnings

from deep_translator.constants import BASE_URLS, GOOGLE_LANGUAGES_TO_CODES
from deep_translator.exceptions import (NotValidPayload,
                                        TranslationNotFound,
                                        LanguageNotSupportedException,
                                        RequestError,
                                        TooManyRequests)
from deep_translator.parent import BaseTranslator
import requests
from time import sleep


class MyMemoryTranslator(BaseTranslator):
    """
    class that uses the mymemory translator to translate texts
    """
    _languages = GOOGLE_LANGUAGES_TO_CODES
    supported_languages = list(_languages.keys())

    def __init__(self, source="auto", target="en", **kwargs):
        """
        @param source: source language to translate from
        @param target: target language to translate to
        """
        self.__base_url = BASE_URLS.get("MYMEMORY")
        if self.is_language_supported(source, target):
            self._source, self._target = self._map_language_to_code(source.lower(), target.lower())
            self._source = self._source if self._source != 'auto' else 'Lao'

        self.email = kwargs.get('email', None)
        super(MyMemoryTranslator, self).__init__(base_url=self.__base_url,
                                                 source=self._source,
                                                 target=self._target,
                                                 payload_key='q',
                                                 langpair='{}|{}'.format(self._source, self._target))

    @staticmethod
    def get_supported_languages(as_dict=False):
        """
         return the supported languages by the mymemory translator
         @param as_dict: if True, the languages will be returned as a dictionary mapping languages to their abbreviations
         @return: list or dict
         """
        return MyMemoryTranslator.supported_languages if not as_dict else MyMemoryTranslator._languages

    def _map_language_to_code(self, *languages):
        """
          map language to its corresponding code (abbreviation) if the language was passed by its full name by the user
          @param languages: list of languages
          @return: mapped value of the language or raise an exception if the language is not supported
        """
        for language in languages:
            if language in self._languages.values() or language == 'auto':
                yield language
            elif language in self._languages.keys():
                yield self._languages[language]
            else:
                raise LanguageNotSupportedException(language)

    def is_language_supported(self, *languages):
        """
        check if the language is supported by the translator
        @param languages: list of languages
        @return: bool or raise an Exception
        """
        for lang in languages:
            if lang != 'auto' and lang not in self._languages.keys():
                if lang != 'auto' and lang not in self._languages.values():
                    raise LanguageNotSupportedException(lang)
        return True

    def translate(self, text, return_all=False, **kwargs):
        """
        function that uses the mymemory translator to translate a text
        @param text: desired text to translate
        @type text: str
        @param return_all: set to True to return all synonym/similars of the translated text
        @return: str or list
        """

        if self._validate_payload(text, max_chars=500):
            text = text.strip()

            if self.payload_key:
                self._url_params[self.payload_key] = text
            if self.email:
                self._url_params['de'] = self.email

            response = requests.get(self.__base_url,
                                    params=self._url_params,
                                    headers=self.headers)

            if response.status_code == 429:
                raise TooManyRequests()
            if response.status_code != 200:
                raise RequestError()

            data = response.json()
            if not data:
                TranslationNotFound(text)

            translation = data.get('responseData').get('translatedText')
            if translation:
                return translation

            elif not translation:
                all_matches = data.get('matches')
                matches = (match['translation'] for match in all_matches)
                next_match = next(matches)
                return next_match if not return_all else list(all_matches)

    def translate_sentences(self, sentences=None, **kwargs):
        """
        translate many sentences together. This makes sense if you have sentences with different languages
        and you want to translate all to unified language. This is handy because it detects
        automatically the language of each sentence and then translate it.

        @param sentences: list of sentences to translate
        @return: list of all translated sentences
        """
        warn_msg = "deprecated. Use the translate_batch function instead"
        warnings.warn(warn_msg, DeprecationWarning, stacklevel=2)
        logging.warning(warn_msg)
        if not sentences:
            raise NotValidPayload(sentences)

        translated_sentences = []
        try:
            for sentence in sentences:
                translated = self.translate(text=sentence, **kwargs)
                translated_sentences.append(translated)

            return translated_sentences

        except Exception as e:
            raise e

    def translate_file(self, path, **kwargs):
        """
         translate directly from file
         @param path: path to the target file
         @type path: str
         @param kwargs: additional args
         @return: str
         """
        try:
            with open(path) as f:
                text = f.read()

            return self.translate(text=text)
        except Exception as e:
            raise e

    def translate_batch(self, batch=None):
        """
        translate a list of texts
        @param batch: list of texts you want to translate
        @return: list of translations
        """
        if not batch:
            raise Exception("Enter your text list that you want to translate")

        arr = []
        for text in batch:
            translated = self.translate(text)
            arr.append(translated)
            sleep(2)

        return arr
