from types import SimpleNamespace


def test_database_refiner_allows_a_series_without_a_tvdb_id(monkeypatch):
    from subliminal import Episode
    from subtitles.refiners import database as database_refiner

    row = SimpleNamespace(
        seriesTitle='Yu-Gi-Oh!', season=1, episode=1, absoluteEpisode=None,
        episodeTitle='The Heart of the Cards', year='2000', tvdbId=None,
        alternativeTitles='[]', format=None, resolution=None, video_codec=None,
        audio_codec=None, imdbId=None, sonarrSeriesId=1, sonarrEpisodeId=2,
    )
    monkeypatch.setattr(database_refiner.database, 'execute',
                        lambda statement: SimpleNamespace(first=lambda: row))
    monkeypatch.setattr(database_refiner.path_mappings, 'path_replace_reverse', lambda path: path)
    video = Episode('episode.mkv', series='Guessed series', season=1, episode=1, series_tvdb_id=123)

    database_refiner.refine_from_db('episode.mkv', video)

    assert video.series_tvdb_id == 123
