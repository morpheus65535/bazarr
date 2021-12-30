"""
google translator API
"""
import json
from .constants import BASE_URLS, PAPAGO_LANGUAGE_TO_CODE
from .exceptions import LanguageNotSupportedException, TranslationNotFound, NotValidPayload
import requests
import warnings
import logging


class PapagoTranslator(object):
    """
    class that wraps functions, which use google translate under the hood to translate text(s)
    """
    _languages = PAPAGO_LANGUAGE_TO_CODE
    supported_languages = list(_languages.keys())

    def __init__(self, client_id=None, secret_key=None, source="auto", target="en", **kwargs):
        """
        @param source: source language to translate from
        @param target: target language to translate to
        """
        if not client_id or not secret_key:
            raise Exception("Please pass your client id and secret key! visit the papago website for more infos")

        self.__base_url = BASE_URLS.get("PAPAGO_API")
        self.client_id = client_id
        self.secret_key = secret_key
        if self.is_language_supported(source, target):
            self._source, self._target = self._map_language_to_code(source.lower(), target.lower())

    @staticmethod
    def get_supported_languages(as_dict=False, **kwargs):
        """
        return the supported languages by the google translator
        @param as_dict: if True, the languages will be returned as a dictionary mapping languages to their abbreviations
        @return: list or dict
        """
        return PapagoTranslator.supported_languages if not as_dict else PapagoTranslator._languages

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

        payload = {
            "source": self._source,
            "target": self._target,
            "text": text
        }
        headers = {
            'X-Naver-Client-Id': self.client_id,
            'X-Naver-Client-Secret': self.secret_key,
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
        }
        response = requests.post(self.__base_url, headers=headers, data=payload)
        if response.status_code != 200:
            raise Exception(f'Translation error! -> status code: {response.status_code}')
        res_body = json.loads(response.text)
        if "message" not in res_body:
            raise TranslationNotFound(text)

        msg = res_body.get("message")
        result = msg.get("result", None)
        if not result:
            raise TranslationNotFound(text)
        translated_text = result.get("translatedText")
        return translated_text

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
                text = f.read().strip()
            return self.translate(text)
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

    def translate_batch(self, batch=None, **kwargs):
        """
        translate a list of texts
        @param batch: list of texts you want to translate
        @return: list of translations
        """
        if not batch:
            raise Exception("Enter your text list that you want to translate")
        arr = []
        for i, text in enumerate(batch):

            translated = self.translate(text, **kwargs)
            arr.append(translated)
        return arr


