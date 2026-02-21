# coding=utf-8

from __future__ import absolute_import
from subliminal.providers.shooter import ShooterProvider as _ShooterProvider, ShooterSubtitle as _ShooterSubtitle
from subliminal.video import Episode, Movie


class ShooterSubtitle(_ShooterSubtitle):
    def __init__(self, language, hash, download_link):
        super(ShooterSubtitle, self).__init__(language, hash, download_link)
        self.release_info = hash
        self.page_link = download_link
        self.matches = set()


class ShooterProvider(_ShooterProvider):
    subtitle_class = ShooterSubtitle
    video_types = (Episode, Movie)
