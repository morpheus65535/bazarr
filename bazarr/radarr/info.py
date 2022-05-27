# coding=utf-8

import logging
import requests
import datetime
import json

from dogpile.cache import make_region

from app.config import settings, empty_values
from constants import headers

region = make_region().configure("dogpile.cache.memory")


class GetRadarrInfo:
    @staticmethod
    def version():
        """
        Call system/status API endpoint and get the Radarr version
        @return: str
        """
        radarr_version = region.get(
            "radarr_version",
            expiration_time=datetime.timedelta(seconds=60).total_seconds(),
        )
        if radarr_version:
            region.set("radarr_version", radarr_version)
            return radarr_version
        else:
            radarr_version = ""
        if settings.general.getboolean("use_radarr"):
            try:
                rv = f"{url_radarr()}/api/system/status?apikey={settings.radarr.apikey}"
                radarr_json = requests.get(
                    rv, timeout=60, verify=False, headers=headers
                ).json()
                if "version" in radarr_json:
                    radarr_version = radarr_json["version"]
                else:
                    raise json.decoder.JSONDecodeError
            except json.decoder.JSONDecodeError:
                try:
                    rv = f"{url_radarr()}/api/v3/system/status?apikey={settings.radarr.apikey}"
                    radarr_version = requests.get(
                        rv, timeout=60, verify=False, headers=headers
                    ).json()["version"]
                except json.decoder.JSONDecodeError:
                    logging.debug("BAZARR cannot get Radarr version")
                    radarr_version = "unknown"
            except Exception:
                logging.debug("BAZARR cannot get Radarr version")
                radarr_version = "unknown"
        logging.debug(f"BAZARR got this Radarr version from its API: {radarr_version}")
        region.set("radarr_version", radarr_version)
        return radarr_version

    def is_legacy(self):
        """
        Call self.version() and parse the result to determine if it's a legacy version of Radarr
        @return: bool
        """
        radarr_version = self.version()
        return bool(radarr_version.startswith("0."))


get_radarr_info = GetRadarrInfo()


def url_radarr():
    protocol_radarr = "https" if settings.radarr.getboolean("ssl") else "http"
    if settings.radarr.base_url == "":
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
