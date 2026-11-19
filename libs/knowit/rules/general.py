import typing
from logging import NullHandler, getLogger

from trakit.api import trakit

from knowit.core import Rule

logger = getLogger(__name__)
logger.addHandler(NullHandler())


class GuessTitleRule(Rule[typing.Any]):
    """Guess properties from track title."""

    def execute(
        self,
        props: typing.MutableMapping[str, typing.Any],
        pv_props: typing.MutableMapping[str, typing.Any],
        context: typing.MutableMapping[str, typing.Any],
    ) -> typing.Any:
        """Language detection using name."""
        if 'name' in props:
            language = props.get('language')
            options = {'expected_language': language} if language else {}
            guessed = trakit(props['name'], options)
            if guessed:
                return guessed
        return None


class LanguageRule(Rule[typing.Any]):
    """Language rules."""

    def execute(
        self,
        props: typing.MutableMapping[str, typing.Any],
        pv_props: typing.MutableMapping[str, typing.Any],
        context: typing.MutableMapping[str, typing.Any],
    ) -> typing.Any:
        """Language detection using name."""
        if 'guessed' not in pv_props:
            return None

        guess = pv_props['guessed']
        if 'language' in guess:
            return guess['language']
        return None


class CommentaryRule(Rule[typing.Any]):
    """Commentary rule."""

    def execute(
        self,
        props: typing.MutableMapping[str, typing.Any],
        pv_props: typing.MutableMapping[str, typing.Any],
        context: typing.MutableMapping[str, typing.Any],
    ) -> typing.Any:
        """Commentary detection using name."""
        if 'guessed' in pv_props:
            return pv_props['guessed'].get('commentary')
        return None
