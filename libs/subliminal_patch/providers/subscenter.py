# coding=utf-8

from subliminal.providers.subscenter import SubsCenterProvider as _SubsCenterProvider, \
    SubsCenterSubtitle as _SubsCenterSubtitle
from subzero.language import Language


class SubsCenterSubtitle(_SubsCenterSubtitle):
    hearing_impaired_verifiable = True

    def __init__(self, language, hearing_impaired, page_link, series, season, episode, title, subtitle_id, subtitle_key,
                 subtitle_version, downloaded, releases):
        super(SubsCenterSubtitle, self).__init__(language, hearing_impaired, page_link, series, season, episode, title,
                                                 subtitle_id, subtitle_key,
                                                 subtitle_version, downloaded, releases)
        self.release_info = u", ".join(releases)
        self.page_link = page_link

    def __repr__(self):
        return '<%s %r %s [%s]>' % (
            self.__class__.__name__, self.page_link, self.id, self.language)


class SubsCenterProvider(_SubsCenterProvider):
    languages = {Language.fromalpha2(l) for l in ['he']}
    subtitle_class = SubsCenterSubtitle
    hearing_impaired_verifiable = True
    server_url = 'http://www.subscenter.info/he/'

