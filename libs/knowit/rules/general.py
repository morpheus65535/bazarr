from logging import NullHandler, getLogger

from trakit.api import trakit

from knowit.core import Rule

logger = getLogger(__name__)
logger.addHandler(NullHandler())


class GuessTitleRule(Rule):
    """Guess properties from track title."""

    def execute(self, props, pv_props, context):
        """Language detection using name."""
        if 'name' in props:
            language = props.get('language')
            options = {'expected_language': language} if language else {}
            guessed = trakit(props['name'], options)
            if guessed:
                return guessed


class LanguageRule(Rule):
    """Language rules."""

    def execute(self, props, pv_props, context):
        """Language detection using name."""
        if 'guessed' not in pv_props:
            return

        guess = pv_props['guessed']
        if 'language' in guess:
            return guess['language']
