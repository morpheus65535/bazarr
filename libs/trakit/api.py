import typing

from trakit.config import Config
from trakit.context import Context
from trakit.patterns import configure


class TrakItApi:

    def __init__(self, config: typing.Optional[typing.Mapping[str, typing.Any]] = None):
        self.rebulk = configure(Config(config))

    def trakit(self, string: str, options: typing.Optional[typing.Mapping[str, typing.Any]] = None):
        """Return a mapping of extracted information."""
        matches = self.rebulk.matches(string, Context(options))
        guess: typing.Mapping[str, typing.Any] = matches.to_dict()
        return guess


default_api = TrakItApi()


def trakit(string: str, options: typing.Optional[typing.Mapping[str, typing.Any]] = None):
    return default_api.trakit(string, options)
