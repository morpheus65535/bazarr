# coding=utf-8

import os
import logging
import requests
import datetime
import json

from dogpile.cache import make_region

from bazarr.config import settings, url_sonarr

region = make_region().configure('dogpile.cache.memory')
headers = {"User-Agent": os.environ["SZ_USER_AGENT"]}


class GetSonarrInfo:
    @staticmethod
    def version():
        """
        Call system/status API endpoint and get the Sonarr version
        @return: str
        """
        sonarr_version = region.get("sonarr_version", expiration_time=datetime.timedelta(seconds=60).total_seconds())
        if sonarr_version:
            region.set("sonarr_version", sonarr_version)
            return sonarr_version
        else:
            sonarr_version = ''
        if settings.general.getboolean('use_sonarr'):
            try:
                sv = url_sonarr() + "/api/system/status?apikey=" + settings.sonarr.apikey
                sonarr_json = requests.get(sv, timeout=60, verify=False, headers=headers).json()
                if 'version' in sonarr_json:
                    sonarr_version = sonarr_json['version']
                else:
                    raise json.decoder.JSONDecodeError
            except json.decoder.JSONDecodeError:
                try:
                    sv = url_sonarr() + "/api/v3/system/status?apikey=" + settings.sonarr.apikey
                    sonarr_version = requests.get(sv, timeout=60, verify=False, headers=headers).json()['version']
                except json.decoder.JSONDecodeError:
                    logging.debug('BAZARR cannot get Sonarr version')
                    sonarr_version = 'unknown'
            except Exception:
                logging.debug('BAZARR cannot get Sonarr version')
                sonarr_version = 'unknown'
        logging.debug('BAZARR got this Sonarr version from its API: {}'.format(sonarr_version))
        region.set("sonarr_version", sonarr_version)
        return sonarr_version

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


get_sonarr_info = GetSonarrInfo()
