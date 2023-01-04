# coding=utf-8

from datetime import datetime

from app.database import TableBlacklist
from app.event_handler import event_stream


def get_blacklist():
    blacklist_db = TableBlacklist.select(TableBlacklist.provider, TableBlacklist.subs_id).dicts()

    blacklist_list = []
    for item in blacklist_db:
        blacklist_list.append((item['provider'], item['subs_id']))

    return blacklist_list


def blacklist_log(sonarr_series_id, sonarr_episode_id, provider, subs_id, language):
    TableBlacklist.insert({
        TableBlacklist.sonarr_series_id: sonarr_series_id,
        TableBlacklist.sonarr_episode_id: sonarr_episode_id,
        TableBlacklist.timestamp: datetime.now(),
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
