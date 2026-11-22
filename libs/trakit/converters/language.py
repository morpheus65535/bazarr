import typing

from babelfish import Language, LanguageReverseConverter, LanguageReverseError
from babelfish.converters import CaseInsensitiveDict


class GuessLanguageConverter(LanguageReverseConverter):  # type: ignore[misc]
    def __init__(self, config: typing.Mapping[str, str]):
        self.synonyms: dict[str, tuple[typing.Any, typing.Any, typing.Any]] = CaseInsensitiveDict()
        for synonym, code in config.items():
            lang = Language.fromietf(code) if '-' in code else Language(code)
            self.synonyms[synonym] = (lang.alpha3, lang.country.alpha2 if lang.country else None, lang.script)

    def convert(self, alpha3: str, country: str | None = None, script: str | None = None) -> str:
        return str(Language(alpha3, country, script))

    def reverse(self, name: str) -> tuple[typing.Any, typing.Any, typing.Any]:
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
