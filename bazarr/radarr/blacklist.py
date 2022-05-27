# coding=utf-8

import time

from app.database import TableBlacklistMovie
from app.event_handler import event_stream


def get_blacklist_movie():
    blacklist_db = TableBlacklistMovie.select(
        TableBlacklistMovie.provider, TableBlacklistMovie.subs_id
    ).dicts()

    return [(item["provider"], item["subs_id"]) for item in blacklist_db]


def blacklist_log_movie(radarr_id, provider, subs_id, language):
    TableBlacklistMovie.insert(
        {
            TableBlacklistMovie.radarr_id: radarr_id,
            TableBlacklistMovie.timestamp: time.time(),
            TableBlacklistMovie.provider: provider,
            TableBlacklistMovie.subs_id: subs_id,
            TableBlacklistMovie.language: language,
        }
    ).execute()
    event_stream(type="movie-blacklist")


def blacklist_delete_movie(provider, subs_id):
    TableBlacklistMovie.delete().where(
        (TableBlacklistMovie.provider == provider)
        and (TableBlacklistMovie.subs_id == subs_id)
    ).execute()
    event_stream(type="movie-blacklist", action="delete")


def blacklist_delete_all_movie():
    TableBlacklistMovie.delete().execute()
    event_stream(type="movie-blacklist", action="delete")
