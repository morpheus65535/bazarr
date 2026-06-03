# coding=utf-8

from datetime import datetime

from sqlalchemy import func, or_

from app.database import (
    TableEpisodes,
    TableFailedSubtitleAttempts,
    TableMissingSubtitles,
    TableMovies,
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
from subtitles.serialization import parse_missing_subtitles

WANTED_STATE_QUERY_BATCH_SIZE = 5000


def _iter_chunks(items, batch_size=None):
    if batch_size is None:
        batch_size = WANTED_STATE_QUERY_BATCH_SIZE
    for index in range(0, len(items), batch_size):
        yield items[index:index + batch_size]


def get_missing_subtitle_rows(media_type, media_id, missing_subtitles):
    rows = []
    seen_languages = set()
    for language in parse_missing_subtitles(missing_subtitles):
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


def _serialize_attempt_windows(attempt_windows):
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

    return _serialize_attempt_windows(attempt_windows)


def record_failed_subtitle_attempts(media_type, media_id, languages):
    if isinstance(languages, str):
        languages = [languages]
    else:
        languages = list(dict.fromkeys(languages))

    if not languages:
        return serialize_failed_subtitle_attempts(media_type, media_id)

    return record_failed_subtitle_attempts_map(media_type, {media_id: languages})[media_id]


def record_failed_subtitle_attempts_map(media_type, languages_by_media_id):
    languages_by_media_id = {
        media_id: list(dict.fromkeys(languages))
        for media_id, languages in languages_by_media_id.items()
        if languages
    }
    if not languages_by_media_id:
        return {}

    media_ids = list(languages_by_media_id)
    current_timestamp = datetime.timestamp(datetime.now())
    serialized_attempts = {}
    for media_id_chunk in _iter_chunks(media_ids):
        existing_attempts = {media_id: {} for media_id in media_id_chunk}
        for row in database.execute(
            select(
                TableFailedSubtitleAttempts.media_id,
                TableFailedSubtitleAttempts.language,
                TableFailedSubtitleAttempts.initial_attempt_at,
                TableFailedSubtitleAttempts.latest_attempt_at,
            )
            .where(TableFailedSubtitleAttempts.media_type == media_type)
            .where(TableFailedSubtitleAttempts.media_id.in_(media_id_chunk))
        ):
            existing_attempts[row.media_id][row.language] = row

        rows = []
        updated_attempts = {
            media_id: {
                language: (row.initial_attempt_at, row.latest_attempt_at)
                for language, row in media_attempts.items()
            }
            for media_id, media_attempts in existing_attempts.items()
        }
        for media_id in media_id_chunk:
            for language in languages_by_media_id[media_id]:
                existing_attempt = existing_attempts[media_id].get(language)
                initial_attempt_at = (
                    existing_attempt.initial_attempt_at
                    if existing_attempt is not None else current_timestamp
                )
                rows.append({
                    "media_type": media_type,
                    "media_id": media_id,
                    "language": language,
                    "initial_attempt_at": initial_attempt_at,
                    "latest_attempt_at": current_timestamp,
                })
                updated_attempts[media_id][language] = (initial_attempt_at, current_timestamp)

        for row_chunk in _iter_chunks(rows):
            statement = insert(TableFailedSubtitleAttempts).values(row_chunk)
            database.execute(
                statement.on_conflict_do_update(
                    index_elements=["media_type", "media_id", "language"],
                    set_={"latest_attempt_at": current_timestamp},
                )
            )

        for media_id, media_attempts in updated_attempts.items():
            serialized_attempts[media_id] = _serialize_attempt_windows(media_attempts)

    return serialized_attempts


def refresh_wanted_search_state(media_type, media_id, missing_subtitles, failed_attempts=None,
                                adaptive_search_policy=None, refresh_failed_attempts=True):
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

    legacy_column = TableMovies.missing_subtitles if media_type == 'movie' else TableEpisodes.missing_subtitles
    legacy_id_column = TableMovies.radarrId if media_type == 'movie' else TableEpisodes.sonarrEpisodeId
    return parse_missing_subtitles(database.execute(
        select(legacy_column)
        .where(legacy_id_column == media_id)
    ).scalar_one_or_none())


def get_missing_languages_map(media_type, media_ids):
    media_ids = list(dict.fromkeys(media_ids))
    missing_languages = {media_id: [] for media_id in media_ids}
    if not media_ids:
        return missing_languages

    for media_id_chunk in _iter_chunks(media_ids):
        for row in database.execute(
            select(TableMissingSubtitles.media_id, TableMissingSubtitles.language)
            .where(TableMissingSubtitles.media_type == media_type)
            .where(TableMissingSubtitles.media_id.in_(media_id_chunk))
            .order_by(TableMissingSubtitles.id)
        ):
            missing_languages[row.media_id].append(row.language)

    missing_legacy_ids = [
        media_id for media_id, languages in missing_languages.items()
        if not languages
    ]
    if missing_legacy_ids:
        legacy_column = TableMovies.missing_subtitles if media_type == 'movie' else TableEpisodes.missing_subtitles
        legacy_id_column = TableMovies.radarrId if media_type == 'movie' else TableEpisodes.sonarrEpisodeId
        for row in database.execute(
            select(legacy_id_column.label("media_id"), legacy_column.label("missing_subtitles"))
            .where(legacy_id_column.in_(missing_legacy_ids))
        ):
            missing_languages[row.media_id] = parse_missing_subtitles(row.missing_subtitles)

    return missing_languages


def delete_wanted_search_state(media_type, media_ids):
    if isinstance(media_ids, (int, str)):
        media_ids = [media_ids]
    else:
        media_ids = list(dict.fromkeys(media_ids))
    media_ids = [int(media_id) for media_id in media_ids]

    for media_id_chunk in _iter_chunks(media_ids):
        if not media_id_chunk:
            continue
        database.execute(
            delete(TableMissingSubtitles)
            .where(TableMissingSubtitles.media_type == media_type)
            .where(TableMissingSubtitles.media_id.in_(media_id_chunk))
        )
        database.execute(
            delete(TableFailedSubtitleAttempts)
            .where(TableFailedSubtitleAttempts.media_type == media_type)
            .where(TableFailedSubtitleAttempts.media_id.in_(media_id_chunk))
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
    if adaptive_search_policy is None:
        adaptive_search_policy = get_adaptive_search_policy()

    statement = (
        due_missing_languages_statement(media_type, adaptive_search_policy)
        .order_by(TableMissingSubtitles.media_id, TableMissingSubtitles.id)
    )
    due_languages = {}
    for row in database.execute(statement):
        if row.media_id not in due_languages and len(due_languages) >= batch_size:
            yield due_languages
            due_languages = {}
        due_languages.setdefault(row.media_id, []).append(row.language)

    if due_languages:
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
        for media_id_chunk in _iter_chunks(media_ids):
            for row in database.execute(
                statement.where(TableMissingSubtitles.media_id.in_(media_id_chunk))
            ):
                due_languages.setdefault(row.media_id, []).append(row.language)
    else:
        for row in database.execute(statement):
            due_languages.setdefault(row.media_id, []).append(row.language)

    return due_languages
