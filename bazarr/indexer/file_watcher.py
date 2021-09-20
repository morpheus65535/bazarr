# -*- coding: utf-8 -*-
import os
import time
import logging
import gevent
from watchdog_gevent import Observer
from watchdog.events import PatternMatchingEventHandler
from watchdog.utils import WatchdogShutdown

from config import settings
from bazarr.database import TableShowsRootfolder, TableMoviesRootfolder, TableShows, TableEpisodes, TableMovies
from .video_prop_reader import VIDEO_EXTENSION
from .series.local.episodes_indexer import get_episode_metadata
from list_subtitles import store_subtitles


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

        try:
            self.timeout = int(settings.general.filewatcher_timeout)
        except TypeError:
            self.timeout = 60
            logging.info(f'BAZARR file watcher is using the default interval of {self.timeout} seconds.')
        else:
            logging.info(f'BAZARR file watcher is using the configured interval of {self.timeout} seconds.')

        self.series_observer = Observer(timeout=self.timeout)
        self.movies_observer = Observer(timeout=self.timeout)
        self.series_directories = None
        self.movies_directories = None
        self.all_paths = list(TableShowsRootfolder.select())
        self.all_paths.extend(list(TableMoviesRootfolder.select()))

    def on_any_event(self, event):
        root_dir = self.find_root_dir(event.src_path)
        if root_dir:
            if isinstance(root_dir, TableShowsRootfolder):
                if event.event_type == 'deleted':
                    TableEpisodes.delete().where(TableEpisodes.path == event.src_path).execute()
                elif event.event_type in ['created', 'modified']:
                    series_metadata = self.get_series_from_episode_path(event.src_path)
                    if series_metadata:
                        episode_metadata = get_episode_metadata(event.src_path, series_metadata['tmdbId'],
                                                                series_metadata['seriesId'])
                        if episode_metadata:
                            TableEpisodes.insert(episode_metadata).on_conflict('update').execute()
                            store_subtitles(event.src_path, use_cache=False)
                elif event.event_type in 'moved':
                    series_metadata = self.get_series_from_episode_path(event.dest_path)
                    if series_metadata:
                        episode_metadata = get_episode_metadata(event.dest_path, series_metadata['tmdbId'],
                                                                series_metadata['seriesId'])
                        if episode_metadata:
                            TableEpisodes.update(episode_metadata).where(TableEpisodes.path == event.src_path).execute()
                            store_subtitles(event.src_path, use_cache=False)
            else:
                pass

    def find_root_dir(self, path):
        root_dir_list = [x for x in self.all_paths if x.path in path]
        if root_dir_list:
            return root_dir_list[0]

    @staticmethod
    def get_series_from_episode_path(path):
        series_dir = os.path.dirname(path)
        try:
            series_metadata = TableShows.select().where(TableShows.path == series_dir).dicts().get()
        except TableShows.DoesNotExist:
            series_dir = os.path.dirname(os.path.dirname(path))
            try:
                series_metadata = TableShows.select().where(TableShows.path == series_dir).dicts().get()
            except TableShows.DoesNotExist:
                return None
            else:
                return series_metadata
        else:
            return series_metadata

    def config(self):
        self.fs_event_handler.on_any_event = self.on_any_event

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
        logging.info('BAZARR is starting file system watchers...')
        self.config()
        self.series_observer.start()
        self.movies_observer.start()
        logging.info('BAZARR is watching for file system changes.')


fileWatcher = FileWatcher()
