import typing

from babelfish import Country, CountryReverseConverter, CountryReverseError
from babelfish.converters import CaseInsensitiveDict


class GuessCountryConverter(CountryReverseConverter):
    def __init__(self, config: typing.Mapping[str, str]):
        self.synonyms = CaseInsensitiveDict(config)

    def convert(self, alpha2):
        return str(Country(alpha2))

    def reverse(self, name: str):
        try:
            return self.synonyms[name]
        except KeyError:
            pass

        if name.isupper() and len(name) == 2:
            try:
                return Country(name).alpha2
            except ValueError:
                pass

        for conv in (Country.fromname,):
            try:
                return conv(name).alpha2
            except CountryReverseError:
                pass

        raise CountryReverseError(name)
