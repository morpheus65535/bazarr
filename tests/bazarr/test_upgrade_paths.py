from pathlib import Path
from types import SimpleNamespace

from tests.test_helpers import _Column, _Result, load_isolated_module


def _load_upgrade_module():
    root = Path(__file__).resolve().parents[2]
    module_path = root / "bazarr" / "subtitles" / "upgrade.py"

    class _Query:
        def where(self, *args, **kwargs):
            return self

        def join(self, *args, **kwargs):
            return self

        def select_from(self, *args, **kwargs):
            return self

        def subquery(self):
            return self

        def group_by(self, *args, **kwargs):
            return self

        def label(self, *args, **kwargs):
            return self

    table_shows = SimpleNamespace(
        title=_Column("title"),
        sonarrSeriesId=_Column("sonarrSeriesId"),
        profileId=_Column("profileId"),
    )
    table_episodes = SimpleNamespace(
        season=_Column("season"),
        episode=_Column("episode"),
        title=_Column("title"),
        audio_language=_Column("audio_language"),
        sceneName=_Column("sceneName"),
        path=_Column("path"),
        sonarrEpisodeId=_Column("sonarrEpisodeId"),
    )
    table_movies = SimpleNamespace(
        title=_Column("title"),
        audio_language=_Column("audio_language"),
        sceneName=_Column("sceneName"),
        path=_Column("path"),
        profileId=_Column("profileId"),
        radarrId=_Column("radarrId"),
    )
    table_history = SimpleNamespace(
        id=_Column("id"),
        language=_Column("language"),
        video_path=_Column("video_path"),
        score=_Column("score"),
        sonarrEpisodeId=_Column("sonarrEpisodeId"),
        sonarrSeriesId=_Column("sonarrSeriesId"),
        subtitles_path=_Column("subtitles_path"),
        action=_Column("action"),
        timestamp=_Column("timestamp"),
        upgradedFromId=_Column("upgradedFromId"),
    )
    table_history_movie = SimpleNamespace(
        id=_Column("id"),
        language=_Column("language"),
        video_path=_Column("video_path"),
        score=_Column("score"),
        radarrId=_Column("radarrId"),
        subtitles_path=_Column("subtitles_path"),
        action=_Column("action"),
        timestamp=_Column("timestamp"),
        upgradedFromId=_Column("upgradedFromId"),
    )
    table_episode_subs = SimpleNamespace(path=_Column("path"), sonarrEpisodeId=_Column("sonarrEpisodeId"))
    table_movie_subs = SimpleNamespace(path=_Column("path"), radarrId=_Column("radarrId"))

    return load_isolated_module(
        "subtitles.upgrade",
        module_path,
        ["subtitles", "app", "radarr", "sonarr", "utilities"],
        {
            "sqlalchemy": SimpleNamespace(and_=lambda *args, **kwargs: None, or_=lambda *args, **kwargs: None),
            "app.config": SimpleNamespace(
                settings=SimpleNamespace(
                    general=SimpleNamespace(
                        use_sonarr=True,
                        use_radarr=True,
                        upgrade_subs=True,
                        days_to_upgrade_subs=30,
                        upgrade_manual=False,
                    )
                )
            ),
            "app.database": SimpleNamespace(
                get_exclusion_clause=lambda media_type: [],
                get_audio_profile_languages=lambda audio_language: [],
                TableShows=table_shows,
                TableEpisodes=table_episodes,
                TableMovies=table_movies,
                TableHistory=table_history,
                TableHistoryMovie=table_history_movie,
                TableEpisodesSubtitles=table_episode_subs,
                TableMoviesSubtitles=table_movie_subs,
                database=SimpleNamespace(execute=lambda stmt: _Result(all_value=[])),
                select=lambda *args, **kwargs: _Query(),
                func=SimpleNamespace(max=lambda *_args, **_kwargs: _Query()),
                get_profiles_list=lambda profile_id=None, **kwargs: {"items": []},
            ),
            "app.jobs_queue": SimpleNamespace(
                jobs_queue=SimpleNamespace(
                    add_job_from_function=lambda *args, **kwargs: None,
                    update_job_progress=lambda *args, **kwargs: None,
                    update_job_name=lambda *args, **kwargs: None,
                )
            ),
            "app.get_providers": SimpleNamespace(get_providers=lambda: []),
            "app.notifier": SimpleNamespace(
                send_notifications=lambda *args, **kwargs: None,
                send_notifications_movie=lambda *args, **kwargs: None,
            ),
            "radarr.history": SimpleNamespace(history_log_movie=lambda *args, **kwargs: None),
            "sonarr.history": SimpleNamespace(history_log=lambda *args, **kwargs: None),
            "subtitles.indexer.movies": SimpleNamespace(store_subtitles_movie=lambda *args, **kwargs: None),
            "subtitles.indexer.series": SimpleNamespace(store_subtitles=lambda *args, **kwargs: None),
            "utilities.path_mappings": SimpleNamespace(
                path_mappings=SimpleNamespace(
                    path_replace=lambda path: path,
                    path_replace_movie=lambda path: path,
                )
            ),
            "subtitles.download": SimpleNamespace(generate_subtitles=lambda *args, **kwargs: []),
            "app.event_handler": SimpleNamespace(event_stream=lambda *args, **kwargs: None),
        },
    )


def test_parse_language_string_handles_non_string_input():
    module = _load_upgrade_module()

    assert module.parse_language_string(None) == ["", "False", "False"]
    assert module.parse_language_string(123) == ["", "False", "False"]
    assert module.parse_language_string("  ") == ["", "False", "False"]


def test_language_profile_helpers_handle_malformed_items():
    module = _load_upgrade_module()

    module.get_profiles_list = lambda *args, **kwargs: {"items": [None, {"bad": "shape"}, {"language": "en", "hi": "True"}]}

    assert module._language_still_desired("en:hi", 10) is True
    assert module._is_hi_required("en:forced", 10) is True
    assert module._language_from_items([None, {"language": None}, {"language": "fr", "forced": "True"}]) == ["fr:forced"]


def test_upgrade_movies_subtitles_handles_none_audio_list_and_result_without_message():
    module = _load_upgrade_module()

    movie_row = SimpleNamespace(
        id=10,
        title="Movie",
        language="en",
        audio_language="['eng']",
        video_path="/movies/movie.mkv",
        sceneName=None,
        score=80,
        radarrId=7,
        path="/movies/movie.mkv",
        profileId=44,
        subtitles_path="/movies/sub.srt",
        external_subtitles="/movies/sub.srt",
    )

    module.get_upgradable_movies_subtitles = lambda history_id_list=None: {10: None}
    module._language_still_desired = lambda language, profile_id: True
    module.database = SimpleNamespace(execute=lambda stmt: _Result(all_value=[movie_row]))
    module.get_providers = lambda: ["provider"]
    module.get_audio_profile_languages = lambda audio_language: None
    module.generate_subtitles = lambda *args, **kwargs: [SimpleNamespace()]

    stored = []
    history_calls = []
    notifications = []
    module.store_subtitles_movie = lambda movie_id: stored.append(movie_id)
    module.history_log_movie = lambda *args, **kwargs: history_calls.append((args, kwargs))
    module.send_notifications_movie = lambda *args, **kwargs: notifications.append(args)
    module.jobs_queue = SimpleNamespace(
        update_job_progress=lambda *args, **kwargs: None,
        update_job_name=lambda *args, **kwargs: None,
        add_job_from_function=lambda *args, **kwargs: None,
    )
    module.event_stream = lambda *args, **kwargs: None

    module.upgrade_movies_subtitles(job_id="job")

    assert stored == [7]
    assert len(history_calls) == 1
    assert notifications == []
    class _Query:
        def where(self, *args, **kwargs):
            return self

        def join(self, *args, **kwargs):
            return self

        def select_from(self, *args, **kwargs):
            return self

        def subquery(self):
            return self

        def group_by(self, *args, **kwargs):
            return self

        def label(self, *args, **kwargs):
            return self
