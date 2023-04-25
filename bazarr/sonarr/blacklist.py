# coding=utf-8

from datetime import datetime

from app.database import TableBlacklist, database, insert, delete, select
from app.event_handler import event_stream


def get_blacklist():
    return [(item.provider, item.subs_id) for item in
            database.execute(
                select(TableBlacklist.provider, TableBlacklist.subs_id))
            .all()]


def blacklist_log(sonarr_series_id, sonarr_episode_id, provider, subs_id, language):
    database.execute(
        insert(TableBlacklist)
        .values(
            sonarr_series_id=sonarr_series_id,
            sonarr_episode_id=sonarr_episode_id,
            timestamp=datetime.now(),
            provider=provider,
            subs_id=subs_id,
            language=language
        ))
    database.commit()
    event_stream(type='episode-blacklist')


def blacklist_delete(provider, subs_id):
    database.execute(
        delete(TableBlacklist)
        .where((TableBlacklist.provider == provider) and (TableBlacklist.subs_id == subs_id)))
    database.commit()
    event_stream(type='episode-blacklist', action='delete')


def blacklist_delete_all():
    database.execute(delete(TableBlacklist))
    database.commit()
    event_stream(type='episode-blacklist', action='delete')
