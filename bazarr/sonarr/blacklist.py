# coding=utf-8

import time

from app.database import TableBlacklist
from app.event_handler import event_stream


def get_blacklist():
    blacklist_db = TableBlacklist.select(TableBlacklist.provider, TableBlacklist.subs_id).dicts()

    return [(item['provider'], item['subs_id']) for item in blacklist_db]


def blacklist_log(sonarr_series_id, sonarr_episode_id, provider, subs_id, language):
    TableBlacklist.insert({
        TableBlacklist.sonarr_series_id: sonarr_series_id,
        TableBlacklist.sonarr_episode_id: sonarr_episode_id,
        TableBlacklist.timestamp: time.time(),
        TableBlacklist.provider: provider,
        TableBlacklist.subs_id: subs_id,
        TableBlacklist.language: language
    }).execute()
    event_stream(type='episode-blacklist')


def blacklist_delete(provider, subs_id):
    TableBlacklist.delete().where((TableBlacklist.provider == provider) and
                                  (TableBlacklist.subs_id == subs_id))\
        .execute()
    event_stream(type='episode-blacklist', action='delete')


def blacklist_delete_all():
    TableBlacklist.delete().execute()
    event_stream(type='episode-blacklist', action='delete')
