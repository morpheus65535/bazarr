import typing

import babelfish


class Context(dict[str, typing.Any]):
    def __init__(self, options: typing.Mapping[str, typing.Any] | None = None):
        super().__init__(options or {})
        language = self['expected_language'] if 'expected_language' in self else None
        if language and not isinstance(language, babelfish.Language):
            language = babelfish.Language.fromietf(str(language))
        self.expected_language: babelfish.Language | None = language
        self.type: typing.Literal['trackname', 'filename'] = self.get('type') or 'trackname'

    def accept(self, lang: babelfish.Language) -> bool:
        if self.expected_language is None:
            return True
        if self.expected_language.alpha3 != lang.alpha3:
            return False
        if self.expected_language.script and self.expected_language != lang.script:
            return False

        return not self.expected_language.country or self.expected_language == lang.country
