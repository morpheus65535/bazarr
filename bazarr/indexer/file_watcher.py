# -*- coding: utf-8 -*-

import time
import logging
import gevent
from watchdog_gevent import Observer
from watchdog.events import PatternMatchingEventHandler
from watchdog.utils import WatchdogShutdown

from config import settings
from bazarr.database import TableShowsRootfolder, TableMoviesRootfolder
from .video_prop_reader import VIDEO_EXTENSION


class FileWatcher:
    def __init__(self):
        self.patterns = [f"*{x}" for x in VIDEO_EXTENSION]
        self.ignore_patterns = None
        self.ignore_directories = True
        self.case_sensitive = True
        self.fs_event_handler = PatternMatchingEventHandler(self.patterns,
                                                            self.ignore_patterns,
                                                            self.ignore_directories,
                                                            self.case_sensitive)
        self.series_observer = Observer()
        self.movies_observer = Observer()
        self.series_directories = None
        self.movies_directories = None

    @staticmethod
    def on_created(event):
        logging.info(f"Created: {event.src_path}")

    @staticmethod
    def on_deleted(event):
        logging.info(f"Deleted: {event.src_path}")

    @staticmethod
    def on_modified(event):
        logging.info(f"Modified: {event.src_path}")

    @staticmethod
    def on_moved(event):
        logging.info(f"Moved: from {event.src_path} to {event.dest_path}")

    def config(self):
        self.fs_event_handler.on_created = self.on_created
        self.fs_event_handler.on_deleted = self.on_deleted
        self.fs_event_handler.on_modified = self.on_modified
        self.fs_event_handler.on_moved = self.on_moved

        if settings.general.getboolean('use_series'):
            self.series_directories = [x['path'] for x in TableShowsRootfolder.select().dicts()]
        if settings.general.getboolean('use_movies'):
            self.movies_directories = [x['path'] for x in TableMoviesRootfolder.select().dicts()]

        if settings.general.getboolean('use_series'):
            for series_directory in self.series_directories:
                self.series_observer.schedule(self.fs_event_handler, series_directory, recursive=True)

        if settings.general.getboolean('use_movies'):
            for movies_directory in self.movies_directories:
                self.movies_observer.schedule(self.fs_event_handler, movies_directory, recursive=True)

    def start(self):
        self.config()
        self.series_observer.start()
        self.movies_observer.start()
        logging.info('BAZARR is watching file system changes.')


fileWatcher = FileWatcher()
