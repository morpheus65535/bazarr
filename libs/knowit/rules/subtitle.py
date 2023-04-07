import re

from knowit.core import Rule


class ClosedCaptionRule(Rule):
    """Closed caption rule."""

    cc_re = re.compile(r'(\bcc\d\b)', re.IGNORECASE)

    def execute(self, props, pv_props, context):
        """Execute closed caption rule."""
        if '_closed_caption' in pv_props and self.cc_re.search(pv_props['_closed_caption']):
            return True

        if 'guessed' in pv_props:
            guessed = pv_props['guessed']
            return guessed.get('closed_caption')


class HearingImpairedRule(Rule):
    """Hearing Impaired rule."""

    def execute(self, props, pv_props, context):
        """Hearing Impaired."""
        if 'guessed' in pv_props:
            guessed = pv_props['guessed']
            return guessed.get('hearing_impaired')
