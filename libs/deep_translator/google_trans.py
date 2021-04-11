"""
google translator API
"""

from deep_translator.constants import BASE_URLS, GOOGLE_LANGUAGES_TO_CODES
from deep_translator.exceptions import TooManyRequests, LanguageNotSupportedException, TranslationNotFound, NotValidPayload, RequestError
from deep_translator.parent import BaseTranslator
from bs4 import BeautifulSoup
import requests
from time import sleep
import warnings
import logging


class GoogleTranslator(BaseTranslator):
    """
    class that wraps functions, which use google translate under the hood to translate text(s)
    """
    _languages = GOOGLE_LANGUAGES_TO_CODES
    supported_languages = list(_languages.keys())

    def __init__(self, source="auto", target="en"):
        """
        @param source: source language to translate from
        @param target: target language to translate to
        """
        self.__base_url = BASE_URLS.get("GOOGLE_TRANSLATE")

        if self.is_language_supported(source, target):
            self._source, self._target = self._map_language_to_code(source.lower(), target.lower())

        super(GoogleTranslator, self).__init__(base_url=self.__base_url,
                                               source=self._source,
                                               target=self._target,
                                               element_tag='div',
                                               element_query={"class": "t0"},
                                               payload_key='q',  # key of text in the url
                                               hl=self._target,
                                               sl=self._source)

        self._alt_element_query = {"class": "result-container"}

    @staticmethod
    def get_supported_languages(as_dict=False):
        """
        return the supported languages by the google translator
        @param as_dict: if True, the languages will be returned as a dictionary mapping languages to their abbreviations
        @return: list or dict
        """
        return GoogleTranslator.supported_languages if not as_dict else GoogleTranslator._languages

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

    def translate(self, text, **kwargs):
        """
        function that uses google translate to translate a text
        @param text: desired text to translate
        @return: str: translated text
        """

        if self._validate_payload(text):
            text = text.strip()

            if self.payload_key:
                self._url_params[self.payload_key] = text

            response = requests.get(self.__base_url,
                                    params=self._url_params, headers ={'User-agent': 'your bot 0.1'})

            if response.status_code == 429:
                raise TooManyRequests()

            if response.status_code != 200:
                # print("status code", response.status_code)
                raise RequestError()

            soup = BeautifulSoup(response.text, 'html.parser')
            element = soup.find(self._element_tag, self._element_query)

            if not element:
                element = soup.find(self._element_tag, self._alt_element_query)
                if not element:
                    raise TranslationNotFound(text)
            if element.get_text(strip=True) == text.strip() and text.strip().replace(' ', '').isalpha():
                self._url_params["tl"] = self._target
                del self._url_params["hl"]
                return self.translate(text)
            else:
                return element.get_text(strip=True)

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

    def translate_sentences(self, sentences=None, **kwargs):
        """
        translate many sentences together. This makes sense if you have sentences with different languages
        and you want to translate all to unified language. This is handy because it detects
        automatically the language of each sentence and then translate it.

        @param sentences: list of sentences to translate
        @return: list of all translated sentences
        """
        warnings.warn("deprecated. Use the translate_batch function instead", DeprecationWarning, stacklevel=2)
        logging.warning("deprecated. Use the translate_batch function instead")
        if not sentences:
            raise NotValidPayload(sentences)

        translated_sentences = []
        try:
            for sentence in sentences:
                translated = self.translate(text=sentence)
                translated_sentences.append(translated)

            return translated_sentences

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


if __name__ == '__main__':

    txt =GoogleTranslator(source='en', target='nl').translate('why not dutch') # GoogleTranslator(source='hindi', target='en').translate(text="ghar jaana hai")
    print("text: ", txt)
