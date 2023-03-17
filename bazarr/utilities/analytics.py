# coding=utf-8

import platform
import os
import logging

from ga4mp import GtagMP

from app.get_args import args
from radarr.info import get_radarr_info
from sonarr.info import get_sonarr_info

bazarr_version = os.environ["BAZARR_VERSION"].lstrip('v')
os_version = platform.python_version()
sonarr_version = get_sonarr_info.version()
radarr_version = get_radarr_info.version()
python_version = platform.platform()


class EventTracker:
    def __init__(self):
        self.tracker = GtagMP(api_secret="qHRaseheRsic6-h2I_rIAA", measurement_id="G-3820T18GE3", client_id="temp")

        if not os.path.isfile(os.path.normpath(os.path.join(args.config_dir, 'config', 'analytics_visitor_id.txt'))):
            visitor_id = self.tracker.random_client_id()
            with open(os.path.normpath(os.path.join(args.config_dir, 'config', 'analytics_visitor_id.txt')), 'w+') \
                    as handle:
                handle.write(str(visitor_id))
        else:
            with open(os.path.normpath(os.path.join(args.config_dir, 'config', 'analytics_visitor_id.txt')), 'r') as \
                    handle:
                visitor_id = handle.read()

        self.tracker.client_id = visitor_id

        self.tracker.store.set_user_property(name="BazarrVersion", value=bazarr_version)
        self.tracker.store.set_user_property(name="PythonVersion", value=os_version)
        self.tracker.store.set_user_property(name="SonarrVersion", value=sonarr_version)
        self.tracker.store.set_user_property(name="RadarrVersion", value=radarr_version)
        self.tracker.store.set_user_property(name="OSVersion", value=python_version)

        self.tracker.store.save()

    def track(self, provider, action, language):
        subtitles_event = self.tracker.create_new_event(name="subtitles")

        subtitles_event.set_event_param(name="subtitles_provider", value=provider)
        subtitles_event.set_event_param(name="subtitles_action", value=action)
        subtitles_event.set_event_param(name="subtitles_language", value=language)

        try:
            self.tracker.send(events=[subtitles_event])
        except Exception:
            logging.debug("BAZARR unable to track event.")
        else:
            self.tracker.store.save()


event_tracker = EventTracker()
