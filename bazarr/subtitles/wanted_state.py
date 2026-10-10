# coding=utf-8

from datetime import datetime
from contextlib import contextmanager

from sqlalchemy import case, func, or_
from sqlalchemy.engine import Connection

from app.database import (
    TableEpisodes,
    TableFailedSubtitleAttempts,
    TableMovies,
    TableShows,
    database,
    delete,
    insert,
    select,
)
from subtitles.adaptive_searching import (
    get_attempt_windows,
)
from subtitles.language_utils import parse_language_token

WANTED_STATE_QUERY_BATCH_SIZE = 5000
# Leave room for the media-type parameter under SQLite's older bind limit.
WANTED_STATE_ID_QUERY_BATCH_SIZE = 900
FAILED_ATTEMPT_UPSERT_BATCH_SIZE = 100


def _iter_chunks(items, batch_size=None):
    if batch_size is None:
        batch_size = WANTED_STATE_QUERY_BATCH_SIZE
    for index in range(0, len(items), batch_size):
        yield items[index:index + batch_size]


def _normalize_media_ids(media_ids, coerce_int=False):
    if isinstance(media_ids, (int, str)):
        media_ids = [media_ids]
    else:
        media_ids = list(dict.fromkeys(media_ids))

    if coerce_int:
        return list(dict.fromkeys(int(media_id) for media_id in media_ids))
    return media_ids


def get_failed_subtitle_attempt_rows(media_type, media_id, failed_attempts):
    rows = []
    for language, attempt_window in get_attempt_windows(failed_attempts).items():
        rows.append({
            "media_type": media_type,
            "media_id": media_id,
            "language": language,
            "initial_attempt_at": attempt_window[0],
            "latest_attempt_at": attempt_window[1],
        })

    return rows


def refresh_failed_subtitle_attempts(media_type, media_id, failed_attempts):
    database.execute(
        delete(TableFailedSubtitleAttempts)
        .where(TableFailedSubtitleAttempts.media_type == media_type)
        .where(TableFailedSubtitleAttempts.media_id == media_id)
    )

    rows = get_failed_subtitle_attempt_rows(media_type, media_id, failed_attempts)
    if rows:
        database.execute(insert(TableFailedSubtitleAttempts), rows)


def record_failed_subtitle_attempts(media_type, media_id, languages):
    if isinstance(languages, str):
        languages = [languages]
    record_failed_subtitle_attempts_map(media_type, {media_id: languages})


def record_failed_subtitle_attempts_map(media_type, languages_by_media_id):
    normalized_languages = {}
    for media_id, languages in languages_by_media_id.items():
        if not languages:
            continue
        if isinstance(languages, str):
            languages = [languages]
        canonical_languages = dict.fromkeys(
            parsed[0] for language in languages
            if (parsed := parse_language_token(language)) is not None
        )
        if canonical_languages:
            normalized_languages[media_id] = list(canonical_languages)
    if not normalized_languages:
        return

    media_table, media_id_column = {
        'movie': (TableMovies.__table__, 'radarrId'),
        'series': (TableEpisodes.__table__, 'sonarrEpisodeId'),
    }[media_type]
    for media_id_chunk in _iter_chunks(list(normalized_languages), WANTED_STATE_ID_QUERY_BATCH_SIZE):
        with _wanted_state_transaction() as connection:
            # Lock surviving media so deletion cannot leave orphan retry rows.
            media_ids_to_update = connection.execute(
                select(media_table.c[media_id_column])
                .where(media_table.c[media_id_column].in_(media_id_chunk))
                .order_by(media_table.c[media_id_column])
                .with_for_update()
            ).scalars().all()
            current_timestamp = datetime.timestamp(datetime.now())
            rows = [
                {
                    "media_type": media_type,
                    "media_id": media_id,
                    "language": language,
                    "initial_attempt_at": current_timestamp,
                    "latest_attempt_at": current_timestamp,
                }
                for media_id in media_ids_to_update
                for language in normalized_languages[media_id]
            ]
            initial_timestamp = TableFailedSubtitleAttempts.initial_attempt_at
            latest_timestamp = TableFailedSubtitleAttempts.latest_attempt_at
            for row_chunk in _iter_chunks(rows, FAILED_ATTEMPT_UPSERT_BATCH_SIZE):
                statement = insert(TableFailedSubtitleAttempts).values(row_chunk)
                connection.execute(
                    statement.on_conflict_do_update(
                        index_elements=["media_type", "media_id", "language"],
                        set_={
                            "initial_attempt_at": case(
                                (initial_timestamp > current_timestamp, current_timestamp),
                                else_=initial_timestamp,
                            ),
                            "latest_attempt_at": case(
                                (latest_timestamp < current_timestamp, current_timestamp),
                                else_=latest_timestamp,
                            ),
                        },
                    )
                )


@contextmanager
def _wanted_state_transaction():
    bind = database.get_bind()
    if isinstance(bind, Connection):
        # Respect an existing transaction (for example a caller's unit of work).
        with bind.begin_nested():
            yield bind
        return

    # Runtime sessions use AUTOCOMMIT. Give these related writes their own real
    # transaction, without changing the isolation of the caller's connection.
    with bind.connect().execution_options(isolation_level=bind.dialect.default_isolation_level) as connection:
        with connection.begin():
            if connection.dialect.name == 'sqlite':
                connection.exec_driver_sql('BEGIN IMMEDIATE')
            yield connection


def delete_wanted_search_state(media_type, media_ids, connection=None):
    executor = database if connection is None else connection
    media_ids = _normalize_media_ids(media_ids, coerce_int=True)

    for media_id_chunk in _iter_chunks(media_ids, WANTED_STATE_ID_QUERY_BATCH_SIZE):
        if not media_id_chunk:
            continue
        executor.execute(
            delete(TableFailedSubtitleAttempts)
            .where(TableFailedSubtitleAttempts.media_type == media_type)
            .where(TableFailedSubtitleAttempts.media_id.in_(media_id_chunk))
        )


def delete_media_and_wanted_search_state(media_type, table, id_column_name, media_ids):
    """Delete media and its normalized search state atomically."""
    media_table = getattr(table, '__table__', table)
    media_ids = _normalize_media_ids(media_ids, coerce_int=True)
    deleted_ids = []

    for media_id_chunk in _iter_chunks(media_ids, WANTED_STATE_ID_QUERY_BATCH_SIZE):
        if not media_id_chunk:
            continue
        with _wanted_state_transaction() as connection:
            locked_ids = connection.execute(
                select(media_table.c[id_column_name])
                .where(media_table.c[id_column_name].in_(media_id_chunk))
                .order_by(media_table.c[id_column_name])
                .with_for_update()
            ).scalars().all()
            if not locked_ids:
                continue
            connection.execute(
                delete(media_table).where(media_table.c[id_column_name].in_(locked_ids))
            )
            delete_wanted_search_state(media_type, locked_ids, connection=connection)
            deleted_ids.extend(locked_ids)

    return deleted_ids


def delete_series_and_wanted_search_state(series_id):
    """Delete a series and its episode search state in one writer transaction."""
    series_id = int(series_id)
    with _wanted_state_transaction() as connection:
        # Lock the parent before reading its episodes, also blocking new episode
        # inserts on PostgreSQL. SQLite serializes writers with BEGIN IMMEDIATE.
        if connection.execute(
            select(TableShows.sonarrSeriesId)
            .where(TableShows.sonarrSeriesId == series_id).with_for_update()
        ).first() is None:
            return
        episode_ids = connection.execute(
            select(TableEpisodes.sonarrEpisodeId)
            .where(TableEpisodes.sonarrSeriesId == series_id)
        ).scalars().all()
        # Cascading episode deletion waits for any active episode state writer;
        # cleanup then includes the state it committed before releasing its lock.
        connection.execute(delete(TableShows).where(TableShows.sonarrSeriesId == series_id))
        delete_wanted_search_state('series', episode_ids, connection=connection)


def get_failed_attempt_pairs(media_type, media_id):
    attempts = []
    for row in database.execute(
        select(
            TableFailedSubtitleAttempts.language,
            TableFailedSubtitleAttempts.initial_attempt_at,
            TableFailedSubtitleAttempts.latest_attempt_at,
        )
        .where(TableFailedSubtitleAttempts.media_type == media_type)
        .where(TableFailedSubtitleAttempts.media_id == media_id)
    ):
        attempts.append([row.language, row.initial_attempt_at])
        if row.latest_attempt_at != row.initial_attempt_at:
            attempts.append([row.language, row.latest_attempt_at])

    return attempts
