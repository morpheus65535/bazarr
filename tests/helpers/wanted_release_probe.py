"""Exercise installed PR stages against one persistent, isolated database.

Run from the repository root through devenv. Use --phase seed on development,
then --phase stage --stage N after checking out each successive PR. Providers
are replaced with a deterministic failed search; storage and runtime callers
are the application's real implementations.
"""
import argparse
import importlib
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import time
from threading import Event
from unittest.mock import Mock, patch

parser = argparse.ArgumentParser()
parser.add_argument('--config', type=Path, required=True)
parser.add_argument('--snapshot', type=Path, required=True)
parser.add_argument('--phase', choices=['seed', 'stage', 'bench'], required=True)
parser.add_argument('--stage', type=int)
parser.add_argument('--rows', type=int, default=10005)
parser.add_argument('--reuse-fixture', action='store_true')
options = parser.parse_args()
root = Path.cwd()
assert (root / 'bazarr/app/database.py').exists()
options.config.mkdir(parents=True, exist_ok=True)
(options.config / 'db').mkdir(exist_ok=True)
os.environ.update(NO_CLI='true', SZ_USER_AGENT='release-probe', BAZARR_VERSION='release-probe')
sys.path.insert(0, str(root))
import bazarr.app.libs  # noqa: E402,F401
sys.path.insert(0, str(root / 'bazarr'))
from app.get_args import args  # noqa: E402
args.config_dir = str(options.config.resolve())
from app import database as db  # noqa: E402
from app.config import settings  # noqa: E402
from flask import Flask  # noqa: E402


def state():
    return {f'{row.media_type}|{row.media_id}|{row.language}': [row.initial_attempt_at, row.latest_attempt_at]
            for row in db.database.execute(db.select(db.TableFailedSubtitleAttempts)).scalars()}


def profile(languages):
    return json.dumps([{'id': index, 'language': language, 'hi': 'False', 'forced': 'False',
                        'audio_exclude': 'False', 'audio_only_include': 'False'}
                       for index, language in enumerate(languages, start=1)])


def seed(count):
    db.metadata.create_all(db.engine)
    for name in ('TableMissingSubtitles', 'TableFailedSubtitleAttempts'):
        if hasattr(db, name):
            getattr(db, name).__table__.drop(db.engine)
    db.database.execute(db.text('CREATE TABLE alembic_version (version_num VARCHAR(32) PRIMARY KEY)'))
    db.database.execute(db.text("INSERT INTO alembic_version VALUES ('537e9b4d10e3')"))
    db.database.execute(db.insert(db.TableLanguagesProfiles).values(
        profileId=11, name='Probe', items=profile(['en', 'fr']), mustContain='[]', mustNotContain='[]',
    ))
    db.database.execute(db.insert(db.TableShows).values(
        sonarrSeriesId=3, path='/probe/series', title='Series', profileId=11, tags='[]', monitored='True',
    ))
    legacy = "[['en', 100], ['en', 200], ['fr:hi:forced', 110], ['FR:FORCED:HI', 210], ['de', 120], ['de', 220]]"
    for start in range(0, count, 1000):
        indices = range(start, min(count, start + 1000))
        db.database.execute(db.insert(db.TableMovies), [
            {'radarrId': index + 7, 'path': f'/probe/movie-{index}.mkv', 'title': 'Movie', 'tmdbId': str(index + 7),
             'profileId': 11, 'audio_language': "['English']", 'monitored': 'True', 'tags': '[]',
             'missing_subtitles': "['en', 'fr:hi:forced', 'FR:FORCED:HI', 'de']", 'failedAttempts': legacy}
            for index in indices
        ])
        db.database.execute(db.insert(db.TableEpisodes), [
            {'sonarrEpisodeId': index + 17, 'sonarrSeriesId': 3, 'path': f'/probe/series/e-{index}.mkv',
             'title': 'Episode', 'season': 1, 'episode': index + 1, 'audio_language': "['English']",
             'monitored': 'True', 'missing_subtitles': "['en', 'fr:hi:forced', 'FR:FORCED:HI', 'de']",
             'failedAttempts': legacy} for index in indices
        ])
    db.database.commit()
    return legacy


result = {'phase': options.phase, 'stage': options.stage,
          'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
          'database': db.engine.dialect.name}
if options.phase in ('seed', 'bench'):
    legacy = None if options.reuse_fixture else seed(1 if options.phase == 'seed' else options.rows)
    if options.phase == 'seed':
        expected = {f'{kind}|{media_id}|{language}': window
                    for kind, media_id in [('movie', 7), ('series', 17)]
                    for language, window in [('en', [100, 200]), ('fr:forced:hi', [110, 210]), ('de', [120, 220])]}
        missing = {f'{kind}|{media_id}': ['en', 'fr:forced:hi', 'de']
                   for kind, media_id in [('movie', 7), ('series', 17)]}
        options.snapshot.write_text(json.dumps({'attempts': expected, 'legacy': legacy, 'missing': missing}))
    else:
        before_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        started = time.perf_counter()
        db.migrate_db(Flask(__name__))
        elapsed = time.perf_counter() - started
        counts = {model.__tablename__: db.database.execute(db.select(db.func.count()).select_from(model)).scalar_one()
                  for model in ([db.TableMissingSubtitles] if hasattr(db, 'TableMissingSubtitles') else []) + [db.TableFailedSubtitleAttempts]}
        assert set(counts.values()) == {options.rows * 6}, counts
        bounds = db.database.execute(db.select(db.func.min(db.TableFailedSubtitleAttempts.initial_attempt_at),
                                               db.func.max(db.TableFailedSubtitleAttempts.latest_attempt_at))).one()
        assert bounds == (100, 220), bounds
        assert db.database.execute(db.select(db.func.count()).select_from(db.TableMovies)).scalar_one() == options.rows
        assert db.database.execute(db.select(db.func.count()).select_from(db.TableEpisodes)).scalar_one() == options.rows
        result.update(media_rows=options.rows * 2, normalized_counts=counts, upgrade_seconds=elapsed,
                      python_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                      python_peak_rss_before_upgrade_kib=before_rss,
                      server_version=db.engine.dialect.server_version_info,
                      driver_version=db.engine.dialect.dbapi.__version__ if db.postgresql else db.engine.dialect.dbapi.sqlite_version)
else:
    expected = json.loads(options.snapshot.read_text())
    db.init_db()
    db.migrate_db(Flask(__name__))
    assert state() == expected['attempts'], ('restart overwrote retry history', state(), expected['attempts'])
    from sqlalchemy import inspect
    missing_table_exists = inspect(db.engine).has_table('table_missing_subtitles')
    assert missing_table_exists == (options.stage >= 3631), (options.stage, missing_table_exists)
    result['missing_table_exists'] = missing_table_exists
    if options.stage == 3631:
        from subtitles.wanted_state import get_missing_languages
        for kind, media_id in [('movie', 7), ('series', 17)]:
            assert get_missing_languages(kind, media_id) == expected['missing'][f'{kind}|{media_id}']
        result['intervening_missing_writes_imported'] = True
    from languages.get_languages import load_language_in_db
    load_language_in_db()
    for model, values in [(db.TableMoviesSubtitles, {'radarrId': 7}),
                          (db.TableEpisodesSubtitles, {'sonarrEpisodeId': 17, 'sonarrSeriesId': 3})]:
        if db.database.execute(db.select(db.func.count()).select_from(model)).scalar_one() == 0:
            db.database.execute(db.insert(model).values(language='ja', hi=False, forced=False,
                                                       path='/probe/ja.srt', size=1, **values))
    new_language = {3630: 'it', 3631: 'es', 3632: 'pt', 3633: 'nl', 3634: 'sv'}[options.stage]
    db.database.execute(db.update(db.TableLanguagesProfiles).values(items=profile(['en', new_language])))
    db.update_profile_id_list.invalidate()
    movie_indexer = importlib.import_module('subtitles.indexer.movies')
    episode_indexer = importlib.import_module('subtitles.indexer.series')
    movie_indexer.list_missing_subtitles_movies(no=7)
    episode_indexer.list_missing_subtitles(epno=17)
    db.database.commit()
    settings.general.adaptive_searching = False
    requested = {}
    scheduled_attempts = {}
    for kind, module_name, function, media_id in [
        ('movie', 'subtitles.wanted.movies', 'wanted_download_subtitles_movie', 7),
        ('series', 'subtitles.wanted.series', 'wanted_download_subtitles', 17),
    ]:
        module = importlib.import_module(module_name)

        def failed_search(path, languages, *args, **kwargs):
            requested[kind] = list(languages)
            attempted_languages = kwargs.get('attempted_languages')
            if attempted_languages is not None:
                attempted_languages.update(languages)
                scheduled_attempts[kind] = list(languages)
            return iter([])

        with patch.object(module, 'get_providers', return_value=['probe']), \
                patch.object(module, 'generate_subtitles', side_effect=failed_search):
            getattr(module, function)(media_id)
            if options.stage == 3634:
                queue = Mock()
                queue.get_job.return_value.cancel_event = Event()
                scheduled_function = ('wanted_search_missing_subtitles_movies' if kind == 'movie'
                                      else 'wanted_search_missing_subtitles_series')
                with patch.object(module, 'jobs_queue', queue):
                    getattr(module, scheduled_function)(job_id='probe')
                assert scheduled_attempts[kind] == requested[kind]
                queue.update_job_name.assert_called_once()
        assert set(requested[kind]) == {('en', 'False', 'False'), (new_language, 'False', 'False')}, requested
    current = state()
    assert set(current) == set(expected['attempts']) | {f'{kind}|{media_id}|{new_language}'
                for kind, media_id in [('movie', 7), ('series', 17)]}, current
    for key, old_window in expected['attempts'].items():
        assert current[key][0] == old_window[0], (key, old_window, current[key])
        assert current[key][1] >= old_window[1], (key, old_window, current[key])
        if key.endswith('|en') or key.endswith('|' + new_language):
            assert current[key][1] > old_window[1]
        else:
            assert current[key] == old_window
    assert db.database.execute(db.select(db.TableMovies.failedAttempts)).scalar_one() == expected['legacy']
    assert db.database.execute(db.select(db.TableEpisodes.failedAttempts)).scalar_one() == expected['legacy']
    # Change missing languages through the real indexers. With only the old,
    # recently retried English subtitle missing, both sync checks must throttle.
    db.database.execute(db.update(db.TableLanguagesProfiles).values(items=profile(['en'])))
    db.update_profile_id_list.invalidate()
    movie_indexer.list_missing_subtitles_movies(no=7)
    episode_indexer.list_missing_subtitles(epno=17)
    settings.general.adaptive_searching = True
    settings.general.adaptive_searching_delay = '21d'
    settings.general.adaptive_searching_delta = '7d'
    movies_sync = importlib.import_module('radarr.sync.movies')
    episodes_sync = importlib.import_module('sonarr.sync.episodes')
    assert movies_sync._is_there_missing_subtitles(radarr_id=7) is False
    assert episodes_sync._is_there_missing_subtitles(episode_id=17) is False
    # Leave the latest missing-language update in place before installing the
    # next release. The next migration must import this value, not the seed.
    db.database.execute(db.update(db.TableLanguagesProfiles).values(items=profile(['en', new_language])))
    db.update_profile_id_list.invalidate()
    movie_indexer.list_missing_subtitles_movies(no=7)
    episode_indexer.list_missing_subtitles(epno=17)
    expected['missing'] = {f'{kind}|{media_id}': ['en', new_language]
                           for kind, media_id in [('movie', 7), ('series', 17)]}
    if missing_table_exists:
        from subtitles.wanted_state import get_missing_languages
        for kind, media_id in [('movie', 7), ('series', 17)]:
            assert get_missing_languages(kind, media_id) == ['en', new_language]
    db.database.commit()
    db.migrate_db(Flask(__name__))
    assert state() == current, 'second startup changed retries'
    expected['attempts'] = current
    options.snapshot.write_text(json.dumps(expected))
    result.update(requested=requested, retry_windows=current, restart_preserved=True, throttled=True)
    if options.stage == 3634:
        result["scheduled_searches_completed"] = sorted(scheduled_attempts)
print(json.dumps(result, sort_keys=True))
db.database.remove()
db.engine.dispose()
