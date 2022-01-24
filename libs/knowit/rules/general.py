
import re
from logging import NullHandler, getLogger

import babelfish

from knowit.core import Rule

logger = getLogger(__name__)
logger.addHandler(NullHandler())


class LanguageRule(Rule):
    """Language rules."""

    name_re = re.compile(r'(?P<name>\w+)\b', re.IGNORECASE)

    def execute(self, props, pv_props, context):
        """Language detection using name."""
        if 'language' in props:
            return

        if 'name' in props:
            name = props.get('name', '')
            match = self.name_re.match(name)
            if match:
                try:
                    return babelfish.Language.fromname(match.group('name'))
                except babelfish.Error:
                    pass
            logger.info('Invalid %s: %r', self.description, name)
