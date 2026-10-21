import typing

from babelfish import Country, CountryReverseConverter, CountryReverseError
from babelfish.converters import CaseInsensitiveDict


class GuessCountryConverter(CountryReverseConverter):  # type: ignore[misc]
    def __init__(self, config: typing.Mapping[str, str]):
        self.synonyms: dict[str, str] = CaseInsensitiveDict(config)

    def convert(self, alpha2: str) -> str:
        return str(Country(alpha2))

    def reverse(self, name: str) -> str:
        try:
            return self.synonyms[name]
        except KeyError:
            pass

        if name.isupper() and len(name) == 2:
            try:
                alpha2: str = Country(name).alpha2
                return alpha2
            except ValueError:
                pass

        for conv in (Country.fromname,):
            try:
                alpha2 = conv(name).alpha2
                return alpha2
            except CountryReverseError:
                pass

        raise CountryReverseError(name)
