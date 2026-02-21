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


class GetRadarrInfo:
    @staticmethod
    def version():
        """
        Call system/status API endpoint and get the Radarr version
        @return: str
        """
        radarr_version = region.get("radarr_version", expiration_time=datetime.timedelta(seconds=60).total_seconds())
        if radarr_version and radarr_version != 'unknown':
            region.set("radarr_version", radarr_version)
            return radarr_version
        else:
            radarr_version = ''
        if settings.general.use_radarr:
            try:
                rv = f"{url_radarr()}/api/system/status?apikey={settings.radarr.apikey}"
                radarr_json = requests.get(rv, timeout=int(settings.radarr.http_timeout), verify=False,
                                           headers=HEADERS).json()
                if 'version' in radarr_json:
                    radarr_version = radarr_json['version']
                else:
                    raise JSONDecodeError
            except JSONDecodeError:
                try:
                    rv = f"{url_radarr()}/api/v3/system/status?apikey={settings.radarr.apikey}"
                    radarr_version = requests.get(rv, timeout=int(settings.radarr.http_timeout), verify=False,
                                                  headers=HEADERS).json()['version']
                except JSONDecodeError:
                    logging.debug('BAZARR cannot get Radarr version')
                    radarr_version = 'unknown'
            except Exception:
                logging.debug('BAZARR cannot get Radarr version')
                radarr_version = 'unknown'
        logging.debug(f'BAZARR got this Radarr version from its API: {radarr_version}')
        region.set("radarr_version", radarr_version)
        return radarr_version

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
        Call self.version() and parse the result to determine if it's a legacy version of Radarr
        @return: bool
        """
        radarr_version = self.version()
        if radarr_version.startswith('0.'):
            return True
        else:
            return False

    def is_deprecated(self):
        """
                Call self.version() and parse the result to determine if it's a deprecated version of Radarr
                @return: bool
                """
        radarr_version = self.version()
        if radarr_version.startswith(('0.', '3.')):
            return True
        else:
            return False


get_radarr_info = GetRadarrInfo()


def url_radarr():
    if settings.radarr.ssl:
        protocol_radarr = "https"
    else:
        protocol_radarr = "http"

    if settings.radarr.base_url == '':
        settings.radarr.base_url = "/"
    if not settings.radarr.base_url.startswith("/"):
        settings.radarr.base_url = f"/{settings.radarr.base_url}"
    if settings.radarr.base_url.endswith("/"):
        settings.radarr.base_url = settings.radarr.base_url[:-1]

    if settings.radarr.port in empty_values:
        port = ""
    else:
        port = f":{settings.radarr.port}"

    return f"{protocol_radarr}://{settings.radarr.ip}{port}{settings.radarr.base_url}"


def url_api_radarr():
    return url_radarr() + f'/api{"/v3" if not get_radarr_info.is_legacy() else ""}/'
