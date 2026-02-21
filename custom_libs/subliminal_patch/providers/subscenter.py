# coding=utf-8

from __future__ import absolute_import

from guessit import guessit
from subliminal.video import Episode, Movie
from subliminal.providers.subscenter import SubsCenterProvider as _SubsCenterProvider, \
    SubsCenterSubtitle as _SubsCenterSubtitle
from subzero.language import Language
from subliminal_patch.subtitle import guess_matches


class SubsCenterSubtitle(_SubsCenterSubtitle):
    hearing_impaired_verifiable = True

    def __init__(self, language, hearing_impaired, page_link, series, season, episode, title, subtitle_id, subtitle_key,
                 subtitle_version, downloaded, releases):
        super(SubsCenterSubtitle, self).__init__(language, hearing_impaired, page_link, series, season, episode, title,
                                                 subtitle_id, subtitle_key,
                                                 subtitle_version, downloaded, releases)
        self.release_info = u", ".join(releases)
        self.page_link = page_link
        self.matches = set()

    def get_matches(self, video):
        self.matches = super().get_matches(video)
        type_ = "episode" if isinstance(video, Episode) else "movie"

        for release in self.releases:
            self.matches |= guess_matches(video, guessit(release, {'type': type_}))

        return self.matches

    def __repr__(self):
        return '<%s %r %s [%s]>' % (
            self.__class__.__name__, self.page_link, self.id, self.language)


class SubsCenterProvider(_SubsCenterProvider):
    languages = {Language.fromalpha2(l) for l in ['he']}
    video_types = (Episode, Movie)
    subtitle_class = SubsCenterSubtitle
    hearing_impaired_verifiable = True
    server_url = 'http://www.subscenter.info/he/'
