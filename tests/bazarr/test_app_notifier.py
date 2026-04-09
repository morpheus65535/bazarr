from bazarr.app import notifier


class DummyRecord:
    def __init__(self, payload):
        self._payload = payload

    def to_dict(self):
        return self._payload


def test_build_media_variables_empty_on_missing_inputs():
    assert notifier._build_media_variables(None, 'movie') == {}
    assert notifier._build_media_variables(DummyRecord({'title': 'Foo'}), '') == {}


def test_build_media_variables_prefixes_keys():
    record = DummyRecord({'title': 'Foo', 'radarrId': 42})

    result = notifier._build_media_variables(record, 'movie')

    assert result == {
        'bazarr_movie_title': 'Foo',
        'bazarr_movie_radarrId': 42,
    }


def test_expand_notifier_url_replaces_multiple_placeholders():
    url = (
        'json://localhost/?:title={bazarr_movie_title}'
        '&:id={bazarr_movie_radarrId}&:path={bazarr_movie_path}'
    )
    media_variables = {
        'bazarr_movie_title': 'My Movie',
        'bazarr_movie_radarrId': 42,
        'bazarr_movie_path': '/media/Movies/My Movie (2024).mkv',
    }

    result = notifier._expand_notifier_url(url, media_variables)

    assert '{bazarr_movie_title}' not in result
    assert '{bazarr_movie_radarrId}' not in result
    assert '{bazarr_movie_path}' not in result
    assert 'title=My%20Movie' in result
    assert 'id=42' in result
    assert 'path=%2Fmedia%2FMovies%2FMy%20Movie%20%282024%29.mkv' in result


def test_expand_notifier_url_blanks_unknown_bazarr_placeholders_and_keeps_non_bazarr():
    url = 'json://localhost/?:known={bazarr_movie_title}&:unknown={bazarr_missing}&:other={title}'
    media_variables = {'bazarr_movie_title': 'Known'}

    result = notifier._expand_notifier_url(url, media_variables)

    assert 'known=Known' in result
    assert 'unknown=' in result
    assert '{bazarr_missing}' not in result
    assert '{title}' in result


def test_expand_notifier_url_none_values_become_empty_string():
    url = 'json://localhost/?:path={bazarr_movie_path}'
    media_variables = {'bazarr_movie_path': None}

    result = notifier._expand_notifier_url(url, media_variables)

    assert result.endswith('?:path=')


def test_expand_notifier_url_concatenation_blanks_missing_bazarr_key():
    url = 'json://localhost/?:path={bazarr_movie_path}{bazarr_episode_path}'
    media_variables = {'bazarr_movie_path': '/media/Movies/My Movie (2024).mkv'}

    result = notifier._expand_notifier_url(url, media_variables)

    assert 'path=%2Fmedia%2FMovies%2FMy%20Movie%20%282024%29.mkv' in result
    assert '{bazarr_episode_path}' not in result
