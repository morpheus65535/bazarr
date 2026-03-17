# coding=utf-8

import logging
import requests
import datetime
import semver

from requests.exceptions import JSONDecodeError

from dogpile.cache import make_region

from app.config import settings, empty_values
from constants import HEADERS

region = make_region().configure('dogpile.cache.memory')


class GetSonarrInfo:
    @staticmethod
    def version():
        """
        Call system/status API endpoint and get the Sonarr version
        @return: str
        """
        sonarr_version = region.get("sonarr_version", expiration_time=datetime.timedelta(seconds=60).total_seconds())
        if sonarr_version and sonarr_version != 'unknown':
            region.set("sonarr_version", sonarr_version)
            return sonarr_version
        else:
            sonarr_version = ''
        if settings.general.use_sonarr:
            try:
                sv = f"{url_sonarr()}/api/system/status?apikey={settings.sonarr.apikey}"
                sonarr_json = requests.get(sv, timeout=int(settings.sonarr.http_timeout), verify=False,
                                           headers=HEADERS).json()
                if 'version' in sonarr_json:
                    sonarr_version = sonarr_json['version']
                else:
                    raise JSONDecodeError
            except JSONDecodeError:
                try:
                    sv = f"{url_sonarr()}/api/v3/system/status?apikey={settings.sonarr.apikey}"
                    sonarr_version = requests.get(sv, timeout=int(settings.sonarr.http_timeout), verify=False,
                                                  headers=HEADERS).json()['version']
                except JSONDecodeError:
                    logging.debug('BAZARR cannot get Sonarr version')
                    sonarr_version = 'unknown'
            except Exception:
                logging.debug('BAZARR cannot get Sonarr version')
                sonarr_version = 'unknown'
        logging.debug(f'BAZARR got this Sonarr version from its API: {sonarr_version}')
        region.set("sonarr_version", sonarr_version)
        return sonarr_version

    def semver(self):
        semver_version = None
        if isinstance(self.version(), str) and self.version() not in ['', 'unknown']:
            split_version = self.version().split('.')
            if len(split_version) >= 3 and all(
                    split_version[i].isdigit() for i in range(len(split_version))):
                semver_version = semver.Version(*split_version)
        return semver_version

    def is_legacy(self):
        """
        Call self.version() and parse the result to determine if it's a legacy version of Sonarr API
        @return: bool
        """
        sonarr_version = self.version()
        if sonarr_version.startswith(('0.', '2.')):
            return True
        else:
            return False

    def is_deprecated(self):
        """
                Call self.version() and parse the result to determine if it's a deprecated version of Sonarr
                @return: bool
                """
        sonarr_version = self.version()
        if sonarr_version.startswith(('0.', '2.')):
            return True
        else:
            return False


get_sonarr_info = GetSonarrInfo()


def url_sonarr():
    if settings.sonarr.ssl:
        protocol_sonarr = "https"
    else:
        protocol_sonarr = "http"

    if settings.sonarr.base_url == '':
        settings.sonarr.base_url = "/"
    if not settings.sonarr.base_url.startswith("/"):
        settings.sonarr.base_url = f"/{settings.sonarr.base_url}"
    if settings.sonarr.base_url.endswith("/"):
        settings.sonarr.base_url = settings.sonarr.base_url[:-1]

    if settings.sonarr.port in empty_values:
        port = ""
    else:
        port = f":{settings.sonarr.port}"

    return f"{protocol_sonarr}://{settings.sonarr.ip}{port}{settings.sonarr.base_url}"


def url_api_sonarr():
    return url_sonarr() + f'/api{"/v3" if not get_sonarr_info.is_legacy() else ""}/'
