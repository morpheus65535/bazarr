import re
from functools import partial

from rebulk import Rebulk
from rebulk.validators import chars_surround

from trakit.config import Config
from trakit.language import language
from trakit.words import seps


def configure(config: Config):
    seps_surround = partial(chars_surround, seps)

    others = Rebulk()
    others.defaults(ignore_case=True, validator=seps_surround)
    others.regex_defaults(flags=re.IGNORECASE,
                          abbreviations=[(r'-', rf'[{re.escape("".join(seps))}]')],
                          validator=seps_surround)
    for name in ('forced', 'commentary', 'external'):
        others.string(name, name=name, value=True)

    others.string('sdh', name='hearing_impaired', value=True)
    others.string('alternate', name='version', value='alternate')
    others.string('descriptive', name='descriptive', value=True)
    others.regex('cc', 'closed-captions?', name='closed_caption', value=True)

    rebulk = Rebulk()
    rebulk.rebulk(language(config))
    rebulk.rebulk(others)

    return rebulk
