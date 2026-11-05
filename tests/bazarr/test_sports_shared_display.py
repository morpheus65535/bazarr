def test_sports_event_uses_indexed_subtitles_and_sports_paths(monkeypatch):
    from api import utils

    monkeypatch.setattr(utils.settings.general, 'embedded_subs_show_desired', False)
    monkeypatch.setattr(utils, 'get_sports_subtitles', lambda sports_event_id: [
        {'name': 'English', 'path': '/sports/event.en.srt'}], raising=False)
    monkeypatch.setattr(utils, 'get_subtitles', lambda **kwargs: [])
    monkeypatch.setattr(utils.path_mappings, 'path_replace_sports', lambda path: f'/mapped{path}')
    monkeypatch.setattr(utils.path_mappings, 'path_replace', lambda path: f'/series{path}')

    event = utils.postprocess({
        'sportsEventId': 91,
        'sportarrLeagueId': 5,
        'path': '/sports/event.mkv',
        'video_path': '/sports/event.mkv',
        'subtitles_path': '/sports/event.en.srt',
    })

    assert event['subtitles'] == [{'name': 'English', 'path': '/sports/event.en.srt'}]
    assert event['path'] == '/mapped/sports/event.mkv'
    assert event['video_path'] == '/mapped/sports/event.mkv'
    assert event['subtitles_path'] == '/mapped/sports/event.en.srt'


def test_postprocess_uses_batched_subtitles_without_a_query(monkeypatch):
    from api import utils

    def no_query(**kwargs):
        raise AssertionError('postprocess must not query subtitles when they are passed in')

    monkeypatch.setattr(utils.settings.general, 'embedded_subs_show_desired', False)
    monkeypatch.setattr(utils, 'get_subtitles', no_query)
    monkeypatch.setattr(utils, 'get_sports_subtitles', no_query)
    monkeypatch.setattr(utils.path_mappings, 'path_replace', lambda path: path)
    monkeypatch.setattr(utils.path_mappings, 'path_replace_movie', lambda path: path)
    monkeypatch.setattr(utils.path_mappings, 'path_replace_sports', lambda path: path)

    batched = [{'name': 'English', 'path': '/media/file.en.srt'}]

    episode = utils.postprocess({'sonarrSeriesId': 1, 'sonarrEpisodeId': 2}, subtitles=batched)
    movie = utils.postprocess({'radarrId': 3}, subtitles=[])
    event = utils.postprocess({'sportarrLeagueId': 5, 'sportsEventId': 91}, subtitles=batched)

    assert episode['subtitles'] == batched
    assert movie['subtitles'] == []
    assert event['subtitles'] == batched


def test_league_parser_keeps_sportarr_banner():
    from sportarr.sync.parser import leagueParser

    league = {
        'id': 5, 'name': 'League', 'path': '/sports/league', 'monitored': True,
        'bannerUrl': 'https://example.com/banner.jpg',
    }

    parsed = leagueParser(league, 'update', [], [], None)

    assert parsed['fanart'] == league['bannerUrl']
