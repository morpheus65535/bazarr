# coding=utf-8
from subliminal.exceptions import ConfigurationError
from subliminal_patch.converters.subsource import SubsourceConverter

# Subsarr stores Subscene language names as lowercase slugs (spaces become hyphens).
# A few names differ from what SubsourceConverter uses.
_NAME_OVERRIDES = {
    'Khmer': 'cambodian-khmer',
    'Pushto': 'pashto',
    'Espranto': 'esperanto',
    'Ukrainian': 'ukranian',  # Subscene's original misspelling
}


def _to_subsarr_name(subscene_name):
    return _NAME_OVERRIDES.get(subscene_name, subscene_name.lower().replace(' ', '-'))


class SubsarrConverter(SubsourceConverter):
    """Derives from SubsourceConverter, transforming names to subsarr's lowercase/slugified format."""

    # Languages present in subsarr but missing from SubsourceConverter
    _EXTRA_LANGUAGES = {
        'kinyarwanda': ('kin',),
        'punjabi': ('pan',),
        'sundanese': ('sun',),
        'yoruba': ('yor',),
    }

    def __init__(self):
        super().__init__()
        self.from_subsarr = {_to_subsarr_name(k): v for k, v in self.from_subsource.items()}
        self.from_subsarr.update(self._EXTRA_LANGUAGES)
        self.to_subsarr = {v: k for k, v in self.from_subsarr.items()}
        self.codes = set(self.from_subsarr.keys())

    def convert(self, alpha3, country=None, script=None):
        if (alpha3, country, script) in self.to_subsarr:
            return self.to_subsarr[(alpha3, country, script)]
        if country and (alpha3, country) in self.to_subsarr:
            return self.to_subsarr[(alpha3, country)]
        if (alpha3,) in self.to_subsarr:
            return self.to_subsarr[(alpha3,)]

        raise ConfigurationError('Unsupported language code for subsarr: %s, %s, %s' % (alpha3, country, script))

    def reverse(self, subsarr):
        if subsarr in self.from_subsarr:
            return self.from_subsarr[subsarr]

        raise ConfigurationError('Unsupported language name for subsarr: %s' % subsarr)
