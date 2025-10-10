# coding=utf-8

class TranslatorFactory:

    @classmethod
    def create_translator(cls, translator_type, **kwargs):
        if translator_type == 'google_translate':
            from .google_translator import GoogleTranslatorService
            return GoogleTranslatorService(**kwargs)

        elif translator_type == 'gemini':
            from .gemini_translator import GeminiTranslatorService
            return GeminiTranslatorService(**kwargs)

        elif translator_type == 'lingarr':
            from .lingarr_translator import LingarrTranslatorService
            return LingarrTranslatorService(**kwargs)

        else:
            raise ValueError(
                f"Unknown translator type: '{translator_type}'"
            )
