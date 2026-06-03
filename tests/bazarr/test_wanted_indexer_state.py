import importlib

from sqlalchemy import select


def _profile_with_english():
    return {
        "items": [
            {
                "language": "en",
                "forced": False,
                "hi": False,
                "audio_exclude": "False",
                "audio_only_include": "False",
            }
        ]
    }


def _bind_indexer_module(bind_wanted_database, module_name, kind, monkeypatch):
    module = importlib.import_module(module_name)
    bind_wanted_database(module, kind)
    monkeypatch.setattr(module, "event_stream", lambda *args, **kwargs: None)
    monkeypatch.setattr(module, "get_profiles_list", lambda *args, **kwargs: _profile_with_english())
    monkeypatch.setattr(module, "get_profile_cutoff", lambda *args, **kwargs: None)
    monkeypatch.setattr(module.settings.general, "use_embedded_subs", False)
    return module


def _wanted_state_for(transactional_session, wanted_search_tables, media_type, media_id):
    return {
        "missing": transactional_session.execute(
            select(wanted_search_tables.missing_subtitles.c.language)
            .where(wanted_search_tables.missing_subtitles.c.media_type == media_type)
            .where(wanted_search_tables.missing_subtitles.c.media_id == media_id)
        ).scalars().all(),
        "failed": transactional_session.execute(
            select(wanted_search_tables.failed_subtitle_attempts.c.language)
            .where(wanted_search_tables.failed_subtitle_attempts.c.media_type == media_type)
            .where(wanted_search_tables.failed_subtitle_attempts.c.media_id == media_id)
        ).scalars().all(),
    }


def test_movie_missing_recalculation_updates_normalized_wanted_rows(
    bind_wanted_database,
    monkeypatch,
    movie_row_factory,
    transactional_session,
    wanted_search_tables,
):
    module = _bind_indexer_module(bind_wanted_database, "subtitles.indexer.movies", "movies", monkeypatch)
    movie = movie_row_factory(missing_languages=[], failed_attempts=[("en", 10)])

    module.list_missing_subtitles_movies(no=movie.radarrId)

    missing_subtitles = transactional_session.execute(
        select(wanted_search_tables.movie.c.missing_subtitles)
        .where(wanted_search_tables.movie.c.radarrId == movie.radarrId)
    ).scalar_one()
    wanted_state = _wanted_state_for(transactional_session, wanted_search_tables, "movie", movie.radarrId)

    assert missing_subtitles == "['en']"
    assert wanted_state == {"missing": ["en"], "failed": ["en"]}


def test_episode_missing_recalculation_updates_normalized_wanted_rows(
    bind_wanted_database,
    monkeypatch,
    episode_row_factory,
    transactional_session,
    wanted_search_tables,
):
    module = _bind_indexer_module(bind_wanted_database, "subtitles.indexer.series", "series", monkeypatch)
    episode = episode_row_factory(missing_languages=[], failed_attempts=[("en", 10)])

    module.list_missing_subtitles(epno=episode.sonarrEpisodeId)

    missing_subtitles = transactional_session.execute(
        select(wanted_search_tables.episode.c.missing_subtitles)
        .where(wanted_search_tables.episode.c.sonarrEpisodeId == episode.sonarrEpisodeId)
    ).scalar_one()
    wanted_state = _wanted_state_for(transactional_session, wanted_search_tables, "series", episode.sonarrEpisodeId)

    assert missing_subtitles == "['en']"
    assert wanted_state == {"missing": ["en"], "failed": ["en"]}
