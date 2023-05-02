import typing

from babelfish import Language, LanguageReverseConverter, LanguageReverseError
from babelfish.converters import CaseInsensitiveDict


class GuessLanguageConverter(LanguageReverseConverter):
    def __init__(self, config: typing.Mapping[str, str]):
        self.synonyms = CaseInsensitiveDict()
        for synonym, code in config.items():
            lang = Language.fromietf(code) if '-' in code else Language(code)
            self.synonyms[synonym] = (lang.alpha3, lang.country.alpha2 if lang.country else None, lang.script)

    def convert(self, alpha3: str, country=None, script=None):
        return str(Language(alpha3, country, script))

    def reverse(self, name: str):
        try:
            return self.synonyms[name]
        except KeyError:
            pass

        for conv in (Language.fromname,):
            try:
                reverse = conv(name)
                return reverse.alpha3, reverse.country, reverse.script
            except (ValueError, LanguageReverseError):
                pass

        raise LanguageReverseError(name)
