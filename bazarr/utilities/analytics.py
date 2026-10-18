# coding=utf-8

import platform
import os
import logging

from ga4mp import GtagMP

from app.get_args import args
from app.config import settings
from radarr.info import get_radarr_info
from sonarr.info import get_sonarr_info


class EventTracker:
    tracker: GtagMP

    def __init__(self) -> None:
        self.bazarr_version = os.environ["BAZARR_VERSION"].lstrip('v')
        self.os_version = platform.python_version()
        self.sonarr_version = get_sonarr_info.version()
        self.radarr_version = get_radarr_info.version()
        self.python_version = platform.platform()

        self.start_tracker()

    def start_tracker(self) -> None:
        """
        Initialize and configure the Google Analytics (GA4) tracker for this
        instance.

        Creates a ``GtagMP`` tracker with the predefined API secret and
        measurement ID, then resolves a persistent visitor identifier. The
        identifier is read from the ``analytics_visitor_id.txt`` file located
        in the ``config`` sub-directory of the configured directory. If that
        file does not exist, a new random client identifier is generated and
        written to it so that subsequent runs reuse the same visitor identity.

        Once the client identifier is assigned to the tracker, several user
        properties describing the running environment (Bazarr, Python, Sonarr,
        Radarr and operating system versions) are registered on the tracker
        store and the store is persisted to disk.

        :raises OSError: If the visitor identifier file cannot be created,
            read or written.

        :return: None
        """
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

        self.tracker.store.set_user_property(name="BazarrVersion", value=self.bazarr_version)
        self.tracker.store.set_user_property(name="PythonVersion", value=self.os_version)
        self.tracker.store.set_user_property(name="SonarrVersion", value=self.sonarr_version)
        self.tracker.store.set_user_property(name="RadarrVersion", value=self.radarr_version)
        self.tracker.store.set_user_property(name="OSVersion", value=self.python_version)

        self.tracker.store.save()

    def track_subtitles(self, provider: str, action: str, language: str) -> None:
        """
        Track a subtitles-related analytics event.

        Builds a new "subtitles" event on the configured tracker, attaches the
        provider, action and language as event parameters and sends it to the
        analytics backend. If analytics are disabled in the application
        settings, the method returns immediately without doing anything. When
        the event is sent successfully, the tracker store is persisted; if
        sending fails, the failure is logged at debug level and silently
        ignored.

        :param provider: Name of the subtitles provider involved in the event.
        :param action: Action performed on the subtitles (for example download,
            upgrade or manual search).
        :param language: Language of the subtitles concerned by the action.
        :return: None
        """
        if not settings.analytics.enabled:
            return

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

    def track_throttling(self, provider: str, exception_name: str, exception_info: str) -> None:
        """
        Record a throttling event for a subtitle provider in the analytics tracker.

        If analytics are disabled in the application settings, the method returns
        immediately without recording anything. Otherwise, a new ``throttling``
        event is created and populated with the provider name, the exception name
        and the exception details, after which it is sent through the tracker.
        Any failure during sending is caught and logged at debug level; on
        successful delivery the tracker store is persisted.

        :param provider: Name of the subtitle provider that triggered the
            throttling.
        :param exception_name: Name of the exception class responsible for the
            throttling.
        :param exception_info: Additional textual information describing the
            exception that caused the throttling.
        :return: None

        """
        if not settings.analytics.enabled:
            return

        throttling_event = self.tracker.create_new_event(name="throttling")

        throttling_event.set_event_param(name="provider", value=provider)
        throttling_event.set_event_param(name="exception_name", value=exception_name)
        throttling_event.set_event_param(name="exception_info", value=exception_info)

        try:
            self.tracker.send(events=[throttling_event])
        except Exception:
            logging.debug("BAZARR unable to track event.")
        else:
            self.tracker.store.save()


event_tracker = EventTracker()
