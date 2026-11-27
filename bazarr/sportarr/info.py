# coding=utf-8

import logging
import requests
import datetime
import semver

from requests.exceptions import JSONDecodeError, RequestException

from dogpile.cache import make_region

from app.config import settings, empty_values
from constants import HEADERS

region = make_region().configure('dogpile.cache.memory')


class GetSportarrInfo:
    @staticmethod
    def version():
        """
        Call health API endpoint and get the Sportarr version
        @return: str
        """
        sportarr_version = region.get("sportarr_version",
                                      expiration_time=datetime.timedelta(seconds=60).total_seconds())
        if sportarr_version and sportarr_version != 'unknown':
            region.set("sportarr_version", sportarr_version)
            return sportarr_version
        else:
            sportarr_version = ''
        if settings.general.use_sportarr:
            try:
                sv = f"{url_sportarr()}/api/health"
                sportarr_json = requests.get(sv, timeout=int(settings.sportarr.http_timeout), verify=False,
                                             headers=HEADERS).json()
                if 'version' in sportarr_json:
                    sportarr_version = sportarr_json['version']
                else:
                    raise JSONDecodeError
            except (RequestException, JSONDecodeError, KeyError):
                logging.debug('BAZARR cannot get Sportarr version')
                sportarr_version = 'unknown'
            except Exception:
                logging.debug('BAZARR cannot get Sportarr version')
                sportarr_version = 'unknown'
        logging.debug(f'BAZARR got this Sportarr version from its API: {sportarr_version}')
        region.set("sportarr_version", sportarr_version)
        return sportarr_version

    def semver(self):
        semver_version = None
        if isinstance(self.version(), str) and self.version() not in ['', 'unknown']:
            split_version = self.version().split('.')
            # Sportarr reports four parts, major.minor.patch.build. semver takes
            # three, so the build number is dropped.
            if len(split_version) >= 3 and all(
                    split_version[i].isdigit() for i in range(3)):
                semver_version = semver.Version(*split_version[:3])
        return semver_version


get_sportarr_info = GetSportarrInfo()


def url_sportarr():
    if settings.sportarr.ssl:
        protocol_sportarr = "https"
    else:
        protocol_sportarr = "http"

    if settings.sportarr.base_url == '':
        settings.sportarr.base_url = "/"
    if not settings.sportarr.base_url.startswith("/"):
        settings.sportarr.base_url = f"/{settings.sportarr.base_url}"
    if settings.sportarr.base_url.endswith("/"):
        settings.sportarr.base_url = settings.sportarr.base_url[:-1]

    if settings.sportarr.port in empty_values:
        port = ""
    else:
        port = f":{settings.sportarr.port}"

    return f"{protocol_sportarr}://{settings.sportarr.ip}{port}{settings.sportarr.base_url}"


def url_api_sportarr():
    # Sportarr has one native API and no legacy dialect, so there is no version
    # to detect here. Its /api/v3 path is a Sonarr compatibility shim and is
    # deliberately not used.
    return url_sportarr() + '/api/'
