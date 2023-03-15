# coding=utf-8

import platform
import os
import logging

from requests import Session

from radarr.info import get_radarr_info
from sonarr.info import get_sonarr_info


class EventTracker:
    def __init__(self):
        self.BazarrVersion = os.environ["BAZARR_VERSION"].lstrip('v')
        self.PythonVersion = platform.python_version()
        self.OSVersion = platform.platform()

        self.session = Session()
        self.session.headers = {
            "User-Agent": os.environ["SZ_USER_AGENT"],
            "X-Forwarded-For": "135.19.105.165",
            "Content-Type": "application/json",
        }

        self.server_url = "http://10.0.0.3:8000/api/event"

    def track(self, provider, action, language):
        subtitles_event = {
            "name": "subtitles",
            "domain": "bazarr",
            "url": "/",
            "props": {
                "subtitles_provider": provider,
                "subtitles_action": action,
                "subtitles_language": language,
                "BazarrVersion": self.BazarrVersion,
                "PythonVersion": self.PythonVersion,
                "SonarrVersion": get_sonarr_info.version(),
                "RadarrVersion": get_radarr_info.version(),
                "OSVersion": self.OSVersion,
            },
        }

        try:
            self.session.post(url=self.server_url, json=subtitles_event)
        except Exception:
            logging.debug("BAZARR unable to track event.")


event_tracker = EventTracker()
