# coding=utf-8
from subliminal.converters.addic7ed import Addic7edConverter
from babelfish.converters.opensubtitles import OpenSubtitlesConverter


class PatchedAddic7edConverter(Addic7edConverter):
    def __init__(self):
        super(PatchedAddic7edConverter, self).__init__()
        self.from_addic7ed.update({
            "French (Canadian)": ("fra", "CA"),
        })
        self.to_addic7ed.update({
            ("fra", "CA"): "French (Canadian)",
        })


class PatchedOpenSubtitlesConverter(OpenSubtitlesConverter):
    def __init__(self):
        super(PatchedOpenSubtitlesConverter, self).__init__()
        self.to_opensubtitles.update({
            ('srp', None, "Latn"): 'scc',
            ('srp', None, "Cyrl"): 'scc',
            ('chi', None, 'Hant'): 'zht'
        })
        self.from_opensubtitles.update({
            'zht': ('zho', None, 'Hant')
        })

    def convert(self, alpha3, country=None, script=None):
        alpha3b = self.alpha3b_converter.convert(alpha3, country, script)
        if (alpha3b, country) in self.to_opensubtitles:
            return self.to_opensubtitles[(alpha3b, country)]
        elif (alpha3b, country, script) in self.to_opensubtitles:
            return self.to_opensubtitles[(alpha3b, country, script)]
        return alpha3b
