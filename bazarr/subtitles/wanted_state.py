# coding=utf-8

from datetime import datetime
from contextlib import contextmanager

from sqlalchemy import case, func, or_
from sqlalchemy.engine import Connection

from app.database import (
    TableEpisodes,
    TableFailedSubtitleAttempts,
    TableMissingSubtitles,
    TableMovies,
    TableShows,
    database,
    delete,
    insert,
    select,
)
from subtitles.adaptive_searching import (
    get_adaptive_search_policy,
    get_active_search_languages,
    get_attempt_windows,
)
from subtitles.language_utils import parse_language_token
from subtitles.serialization import parse_missing_subtitles

WANTED_STATE_QUERY_BATCH_SIZE = 5000
# Keep IN queries below SQLite's historical 999-variable limit, including
# their fixed media-type and policy parameters.
WANTED_STATE_ID_QUERY_BATCH_SIZE = 900
FAILED_ATTEMPT_TEMP_TABLE_MIN_SIZE = 1000
FAILED_ATTEMPT_UPSERT_BATCH_SIZE = 100
FAILED_ATTEMPT_UPDATE_BATCH_SIZE = 300


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


def get_missing_subtitle_rows(media_type, media_id, missing_subtitles):
    rows = []
    seen_languages = set()
    for language in parse_missing_subtitles(missing_subtitles):
        parsed_language = parse_language_token(language)
        if parsed_language is not None:
            language = parsed_language[0]
        if language in seen_languages:
            continue
        seen_languages.add(language)
        rows.append({
            "media_type": media_type,
            "media_id": media_id,
            "language": language,
        })

    return rows


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


def serialize_legacy_failed_attempts(attempt_windows):
    attempts = []
    for language, (initial_attempt_at, latest_attempt_at) in attempt_windows.items():
        attempts.append([language, initial_attempt_at])
        if latest_attempt_at != initial_attempt_at:
            attempts.append([language, latest_attempt_at])

    return str(sorted(attempts, key=lambda attempt: attempt[0]))


def refresh_failed_subtitle_attempts(media_type, media_id, failed_attempts):
    database.execute(
        delete(TableFailedSubtitleAttempts)
        .where(TableFailedSubtitleAttempts.media_type == media_type)
        .where(TableFailedSubtitleAttempts.media_id == media_id)
    )

    rows = get_failed_subtitle_attempt_rows(media_type, media_id, failed_attempts)
    if rows:
        database.execute(insert(TableFailedSubtitleAttempts), rows)


def serialize_failed_subtitle_attempts(media_type, media_id):
    attempt_windows = {}
    for row in database.execute(
        select(
            TableFailedSubtitleAttempts.language,
            TableFailedSubtitleAttempts.initial_attempt_at,
            TableFailedSubtitleAttempts.latest_attempt_at,
        )
        .where(TableFailedSubtitleAttempts.media_type == media_type)
        .where(TableFailedSubtitleAttempts.media_id == media_id)
    ):
        attempt_windows[row.language] = (row.initial_attempt_at, row.latest_attempt_at)

    return serialize_legacy_failed_attempts(attempt_windows)


def record_failed_subtitle_attempts(media_type, media_id, languages):
    if isinstance(languages, str):
        languages = [languages]
    else:
        languages = list(dict.fromkeys(languages))

    if not languages:
        return serialize_failed_subtitle_attempts(media_type, media_id)

    return record_failed_subtitle_attempts_map(media_type, {media_id: languages}).get(media_id, '[]')


def record_failed_subtitle_attempts_map(media_type, languages_by_media_id):
    languages_by_media_id = {
        media_id: list(dict.fromkeys(languages))
        for media_id, languages in languages_by_media_id.items()
        if languages
    }
    if not languages_by_media_id:
        return {}

    media_ids = list(languages_by_media_id)
    serialized_attempts = {}
    media_table, media_id_column = {
        'movie': (TableMovies.__table__, 'radarrId'),
        'series': (TableEpisodes.__table__, 'sonarrEpisodeId'),
    }[media_type]
    for media_id_chunk in _iter_chunks(media_ids, WANTED_STATE_ID_QUERY_BATCH_SIZE):
        with _wanted_state_transaction() as connection:
            media_ids_to_update = connection.execute(
                select(media_table.c[media_id_column])
                .where(media_table.c[media_id_column].in_(media_id_chunk))
                .order_by(media_table.c[media_id_column])
                .with_for_update()
            ).scalars().all()
            if not media_ids_to_update:
                continue

            current_timestamp = datetime.timestamp(datetime.now())
            media_ids_to_update = set(media_ids_to_update)
            existing_attempts = {media_id: {} for media_id in media_ids_to_update}
            for row in connection.execute(
                select(
                    TableFailedSubtitleAttempts.media_id,
                    TableFailedSubtitleAttempts.language,
                    TableFailedSubtitleAttempts.initial_attempt_at,
                    TableFailedSubtitleAttempts.latest_attempt_at,
                )
                .where(TableFailedSubtitleAttempts.media_type == media_type)
                .where(TableFailedSubtitleAttempts.media_id.in_(media_ids_to_update))
            ):
                existing_attempts[row.media_id][row.language] = row

            rows = []
            for media_id in media_ids_to_update:
                for language in languages_by_media_id[media_id]:
                    existing_attempt = existing_attempts[media_id].get(language)
                    rows.append({
                        "media_type": media_type,
                        "media_id": media_id,
                        "language": language,
                        "initial_attempt_at": (
                            existing_attempt.initial_attempt_at if existing_attempt else current_timestamp
                        ),
                        "latest_attempt_at": current_timestamp,
                    })

            latest_timestamp = TableFailedSubtitleAttempts.latest_attempt_at
            for row_chunk in _iter_chunks(rows, FAILED_ATTEMPT_UPSERT_BATCH_SIZE):
                statement = insert(TableFailedSubtitleAttempts).values(row_chunk)
                connection.execute(
                    statement.on_conflict_do_update(
                        index_elements=["media_type", "media_id", "language"],
                        set_={
                            "latest_attempt_at": case(
                                (latest_timestamp < current_timestamp, current_timestamp),
                                else_=latest_timestamp,
                            ),
                        },
                    )
                )

            attempt_windows = {media_id: {} for media_id in media_ids_to_update}
            for row in connection.execute(
                select(
                    TableFailedSubtitleAttempts.media_id,
                    TableFailedSubtitleAttempts.language,
                    TableFailedSubtitleAttempts.initial_attempt_at,
                    TableFailedSubtitleAttempts.latest_attempt_at,
                )
                .where(TableFailedSubtitleAttempts.media_type == media_type)
                .where(TableFailedSubtitleAttempts.media_id.in_(media_ids_to_update))
            ):
                attempt_windows[row.media_id][row.language] = (
                    row.initial_attempt_at, row.latest_attempt_at,
                )

            serialized_chunk = {
                media_id: serialize_legacy_failed_attempts(windows)
                for media_id, windows in attempt_windows.items()
            }
            update_failed_subtitle_attempts(
                media_table,
                list(serialized_chunk.items()),
                media_id_column,
                connection=connection,
            )
            serialized_attempts.update(serialized_chunk)

    return serialized_attempts


def refresh_wanted_search_state(media_type, media_id, missing_subtitles, failed_attempts=None,
                                refresh_failed_attempts=True):
    database.execute(
        delete(TableMissingSubtitles)
        .where(TableMissingSubtitles.media_type == media_type)
        .where(TableMissingSubtitles.media_id == media_id)
    )

    rows = get_missing_subtitle_rows(
        media_type,
        media_id,
        missing_subtitles,
    )
    if rows:
        database.execute(insert(TableMissingSubtitles), rows)
    if refresh_failed_attempts:
        refresh_failed_subtitle_attempts(media_type, media_id, failed_attempts)


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


def store_missing_subtitles(table, id_column_name, media_type, media_id, missing_subtitles):
    """Save both representations atomically, repairing stale normalized rows too."""
    id_column = table.c[id_column_name]
    rows = get_missing_subtitle_rows(media_type, media_id, missing_subtitles)
    with _wanted_state_transaction() as connection:
        media = connection.execute(
            select(table.c.missing_subtitles).where(id_column == media_id).with_for_update()
        ).first()
        if media is None:
            return
        if media.missing_subtitles != missing_subtitles:
            connection.execute(
                table.update().where(id_column == media_id).values(missing_subtitles=missing_subtitles)
            )

        missing_filter = (
            (TableMissingSubtitles.media_type == media_type) &
            (TableMissingSubtitles.media_id == media_id)
        )
        current_languages = connection.execute(
            select(TableMissingSubtitles.language).where(missing_filter).order_by(TableMissingSubtitles.id)
        ).scalars().all()
        if current_languages != [row['language'] for row in rows]:
            connection.execute(delete(TableMissingSubtitles).where(missing_filter))
            if rows:
                connection.execute(insert(TableMissingSubtitles), rows)


def get_missing_languages(media_type, media_id):
    languages = [
        row.language
        for row in database.execute(
            select(TableMissingSubtitles.language)
            .where(TableMissingSubtitles.media_type == media_type)
            .where(TableMissingSubtitles.media_id == media_id)
            .order_by(TableMissingSubtitles.id)
        )
    ]
    if languages:
        return languages

    return []


def legacy_missing_cache_needs_rebuild(missing_subtitles):
    return missing_subtitles is None


def get_missing_languages_map(media_type, media_ids):
    media_ids = _normalize_media_ids(media_ids)
    missing_languages = {media_id: [] for media_id in media_ids}
    if not media_ids:
        return missing_languages

    for media_id_chunk in _iter_chunks(media_ids, WANTED_STATE_ID_QUERY_BATCH_SIZE):
        for row in database.execute(
            select(TableMissingSubtitles.media_id, TableMissingSubtitles.language)
            .where(TableMissingSubtitles.media_type == media_type)
            .where(TableMissingSubtitles.media_id.in_(media_id_chunk))
            .order_by(TableMissingSubtitles.id)
        ):
            missing_languages[row.media_id].append(row.language)

    return missing_languages


def delete_wanted_search_state(media_type, media_ids, connection=None):
    executor = database if connection is None else connection
    media_ids = _normalize_media_ids(media_ids, coerce_int=True)

    for media_id_chunk in _iter_chunks(media_ids, WANTED_STATE_ID_QUERY_BATCH_SIZE):
        if not media_id_chunk:
            continue
        executor.execute(
            delete(TableMissingSubtitles)
            .where(TableMissingSubtitles.media_type == media_type)
            .where(TableMissingSubtitles.media_id.in_(media_id_chunk))
        )
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


def update_failed_subtitle_attempts(table, update_items, id_column_name, connection=None):
    if not update_items:
        return

    dialect_name = connection.dialect.name if connection is not None else database.get_bind().dialect.name
    if len(update_items) >= FAILED_ATTEMPT_TEMP_TABLE_MIN_SIZE and dialect_name == 'sqlite':
        connection = connection or database.connection()
        connection.exec_driver_sql('DROP TABLE IF EXISTS temp_failed_attempt_updates')
        connection.exec_driver_sql(
            'CREATE TEMP TABLE temp_failed_attempt_updates '
            '(media_id INTEGER PRIMARY KEY, failedAttempts TEXT NOT NULL)'
        )
        try:
            for index in range(0, len(update_items), WANTED_STATE_QUERY_BATCH_SIZE):
                connection.exec_driver_sql(
                    'INSERT INTO temp_failed_attempt_updates (media_id, failedAttempts) VALUES (?, ?)',
                    update_items[index:index + WANTED_STATE_QUERY_BATCH_SIZE],
                )
            connection.exec_driver_sql(
                f'UPDATE {table.name} '
                'SET "failedAttempts" = ('
                'SELECT failedAttempts FROM temp_failed_attempt_updates '
                f'WHERE media_id = {table.name}."{id_column_name}") '
                f'WHERE "{id_column_name}" IN (SELECT media_id FROM temp_failed_attempt_updates)'
            )
        finally:
            connection.exec_driver_sql('DROP TABLE IF EXISTS temp_failed_attempt_updates')
        return

    id_column_ref = getattr(table.c, id_column_name, None)
    if id_column_ref is None:
        return

    for index in range(0, len(update_items), FAILED_ATTEMPT_UPDATE_BATCH_SIZE):
        chunk = dict(update_items[index:index + FAILED_ATTEMPT_UPDATE_BATCH_SIZE])
        execute = connection.execute if connection is not None else database.execute
        execute(
            table.update()
            .where(id_column_ref.in_(chunk))
            .values(failedAttempts=case(chunk, value=id_column_ref))
        )


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


def get_due_missing_languages_for_media(media_type, media_id, adaptive_search_policy=None):
    if adaptive_search_policy is None:
        adaptive_search_policy = get_adaptive_search_policy()

    return get_active_search_languages(
        get_missing_languages(media_type, media_id),
        get_failed_attempt_pairs(media_type, media_id),
        adaptive_search_policy=adaptive_search_policy,
    )


def due_missing_languages_statement(media_type, adaptive_search_policy):
    statement = (
        select(TableMissingSubtitles.media_id, TableMissingSubtitles.language)
        .where(TableMissingSubtitles.media_type == media_type)
    )

    if adaptive_search_policy is None:
        return statement

    initial_search_cutoff = adaptive_search_policy["initial_search_cutoff"]
    latest_search_cutoff = adaptive_search_policy["latest_search_cutoff"]

    return (
        statement
        .outerjoin(
            TableFailedSubtitleAttempts,
            (TableFailedSubtitleAttempts.media_type == TableMissingSubtitles.media_type) &
            (TableFailedSubtitleAttempts.media_id == TableMissingSubtitles.media_id) &
            (TableFailedSubtitleAttempts.language == TableMissingSubtitles.language),
        )
        .where(or_(
            TableFailedSubtitleAttempts.id.is_(None),
            TableFailedSubtitleAttempts.initial_attempt_at > initial_search_cutoff,
            TableFailedSubtitleAttempts.latest_attempt_at <= latest_search_cutoff,
        ))
    )


def count_due_missing_media(media_type, adaptive_search_policy=None):
    if adaptive_search_policy is None:
        adaptive_search_policy = get_adaptive_search_policy()

    return database.execute(
        due_missing_languages_statement(media_type, adaptive_search_policy)
        .with_only_columns(func.count(func.distinct(TableMissingSubtitles.media_id)))
        .order_by(None)
    ).scalar() or 0


def iter_due_missing_languages_maps(media_type, adaptive_search_policy=None, batch_size=None):
    if batch_size is None:
        batch_size = WANTED_STATE_QUERY_BATCH_SIZE
    if batch_size < 1:
        raise ValueError('batch_size must be positive')
    if adaptive_search_policy is None:
        adaptive_search_policy = get_adaptive_search_policy()

    statement = due_missing_languages_statement(media_type, adaptive_search_policy)
    last_media_id = None
    while True:
        # Keyset pagination bounds ORM buffering and tolerates searches deleting
        # earlier rows between batches. Fetch all languages for each selected ID.
        ids_statement = (
            statement.with_only_columns(TableMissingSubtitles.media_id)
            .distinct().order_by(TableMissingSubtitles.media_id).limit(batch_size)
        )
        if last_media_id is not None:
            ids_statement = ids_statement.where(TableMissingSubtitles.media_id > last_media_id)
        media_ids = database.execute(ids_statement).scalars().all()
        if not media_ids:
            return
        due_languages = {}
        for media_id_chunk in _iter_chunks(media_ids, WANTED_STATE_ID_QUERY_BATCH_SIZE):
            for row in database.execute(
                statement.where(TableMissingSubtitles.media_id.in_(media_id_chunk))
                .order_by(TableMissingSubtitles.media_id, TableMissingSubtitles.id)
            ):
                due_languages.setdefault(row.media_id, []).append(row.language)
        last_media_id = media_ids[-1]
        yield due_languages


def get_due_missing_languages_map(media_type, media_ids=None, adaptive_search_policy=None):
    has_media_filter = media_ids is not None
    if has_media_filter:
        media_ids = list(dict.fromkeys(media_ids))
        due_languages = {media_id: [] for media_id in media_ids}
        if not media_ids:
            return due_languages
    else:
        due_languages = {}

    if adaptive_search_policy is None:
        adaptive_search_policy = get_adaptive_search_policy()

    if adaptive_search_policy is None:
        if has_media_filter:
            return get_missing_languages_map(media_type, media_ids)

        for row in database.execute(
            select(TableMissingSubtitles.media_id, TableMissingSubtitles.language)
            .where(TableMissingSubtitles.media_type == media_type)
            .order_by(TableMissingSubtitles.id)
        ):
            due_languages.setdefault(row.media_id, []).append(row.language)
        return due_languages

    statement = (
        due_missing_languages_statement(media_type, adaptive_search_policy)
        .order_by(TableMissingSubtitles.id)
    )
    if has_media_filter:
        for media_id_chunk in _iter_chunks(media_ids, WANTED_STATE_ID_QUERY_BATCH_SIZE):
            for row in database.execute(
                statement.where(TableMissingSubtitles.media_id.in_(media_id_chunk))
            ):
                due_languages.setdefault(row.media_id, []).append(row.language)
    else:
        for row in database.execute(statement):
            due_languages.setdefault(row.media_id, []).append(row.language)

    return due_languages
