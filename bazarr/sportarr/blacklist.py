# coding=utf-8

from datetime import datetime

from app.database import TableBlacklistSports, database, insert, delete, select
from app.event_handler import event_stream


def get_blacklist_sports():
    return [(item.provider, item.subs_id) for item in
            database.execute(
                select(TableBlacklistSports.provider, TableBlacklistSports.subs_id))
            .all()]


def blacklist_log_sports(sportarr_league_id, sports_event_id, provider, subs_id, language):
    database.execute(
        insert(TableBlacklistSports)
        .values(
            sportarr_league_id=sportarr_league_id,
            sports_event_id=sports_event_id,
            timestamp=datetime.now(),
            provider=provider,
            subs_id=subs_id,
            language=language
        ))
    event_stream(type='sports-event-blacklist')


def blacklist_delete_sports(provider, subs_id):
    database.execute(
        delete(TableBlacklistSports)
        .where((TableBlacklistSports.provider == provider) & (TableBlacklistSports.subs_id == subs_id)))
    event_stream(type='sports-event-blacklist', action='delete')


def blacklist_delete_all_sports():
    database.execute(delete(TableBlacklistSports))
    event_stream(type='sports-event-blacklist', action='delete')
