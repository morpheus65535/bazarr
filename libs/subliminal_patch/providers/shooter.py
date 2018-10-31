# coding=utf-8

from subliminal.providers.shooter import ShooterProvider as _ShooterProvider, ShooterSubtitle as _ShooterSubtitle


class ShooterSubtitle(_ShooterSubtitle):
    def __init__(self, language, hash, download_link):
        super(ShooterSubtitle, self).__init__(language, hash, download_link)
        self.release_info = hash
        self.page_link = download_link


class ShooterProvider(_ShooterProvider):
    subtitle_class = ShooterSubtitle

