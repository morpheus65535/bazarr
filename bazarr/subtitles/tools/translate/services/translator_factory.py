# coding=utf-8

class TranslatorFactory:

    @classmethod
    def create_translator(cls, translator_type, **kwargs):
        match translator_type:
            case 'google_translate':
                from .google_translator import GoogleTranslatorService
                return GoogleTranslatorService(**kwargs)

            case 'gemini':
                from .gemini_translator import GeminiTranslatorService
                return GeminiTranslatorService(**kwargs)

            case 'lingarr':
                from .lingarr_translator import LingarrTranslatorService
                return LingarrTranslatorService(**kwargs)

            case _:
                available_types = ['google_translate', 'gemini', 'lingarr']

                raise ValueError(
                    f"Unknown translator type: '{translator_type}'. "
                    f"Available types: {available_types}"
                )