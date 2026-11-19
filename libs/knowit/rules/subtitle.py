import re
import typing

from knowit.core import Rule


class ClosedCaptionRule(Rule[typing.Any]):
    """Closed caption rule."""

    cc_re = re.compile(r'(\bcc\d\b)', re.IGNORECASE)

    def execute(
        self,
        props: typing.MutableMapping[str, typing.Any],
        pv_props: typing.MutableMapping[str, typing.Any],
        context: typing.MutableMapping[str, typing.Any],
    ) -> typing.Any:
        """Execute closed caption rule."""
        if '_closed_caption' in pv_props and self.cc_re.search(pv_props['_closed_caption']):
            return True

        if 'guessed' in pv_props:
            guessed = pv_props['guessed']
            return guessed.get('closed_caption')
        return None


class HearingImpairedRule(Rule[typing.Any]):
    """Hearing Impaired rule."""

    def execute(
        self,
        props: typing.MutableMapping[str, typing.Any],
        pv_props: typing.MutableMapping[str, typing.Any],
        context: typing.MutableMapping[str, typing.Any],
    ) -> typing.Any:
        """Hearing Impaired."""
        if 'guessed' in pv_props:
            guessed = pv_props['guessed']
            return guessed.get('hearing_impaired')
        return None
