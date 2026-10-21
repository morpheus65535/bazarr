# -*- coding: utf-8 -*-
from subliminal import Episode, Movie
from subzero.language import Language

from subliminal_patch.providers.legendasnet import LegendasNetProvider

LOGIN_URL = "https://legendas.net/api/v1/login"
MOVIE_SEARCH_URL = "https://legendas.net/api/v1/search/movie"
TV_SEARCH_URL = "https://legendas.net/api/v1/search/tv"

TMDB_MOVIE_ID = 1514026  # Buddy (2026)


def _make_provider(requests_mock):
    requests_mock.post(LOGIN_URL, json={"access_token": "TOKEN"})
    return LegendasNetProvider("user@example.com", "secret")


def _movie_item(item_id):
    return {
        "id": item_id,
        "path": f"/api/v1/download/movie/{TMDB_MOVIE_ID}/{item_id}/Buddy.srt?movie_id={TMDB_MOVIE_ID}&legenda_id={item_id}",
        "tmdb_id": TMDB_MOVIE_ID,
        "name": "Buddy",
        "release_name": "Buddy.2026.1080p.WEBRip.x265.10bit.AAC5.1-YTS.GG",
        "uploader": "omaxfaria",
    }


def test_movie_search_uses_query_params_and_tmdb_id(requests_mock):
    # Regression test for #3668: the search must go in the query string, not a JSON body,
    # and the TMDB id must be used instead of the IMDb id.
    requests_mock.get(MOVIE_SEARCH_URL, json={"movies": [_movie_item(6382)], "page": 1, "per_page": 25,
                                              "has_more": False})
    provider = _make_provider(requests_mock)

    movie = Movie("Buddy.2026.mkv", "Buddy", year=2026, imdb_id="tt37281055")
    # set after construction, as the database refiner does, since subliminal_patch's Video drops tmdb_id
    movie.tmdb_id = TMDB_MOVIE_ID
    subtitles = provider.list_subtitles(movie, {Language("por", "BR")})

    search = [r for r in requests_mock.request_history if r.method == "GET"][0]
    assert search.body is None
    assert search.qs == {"page": ["1"], "per_page": ["25"], "tmdb_id": [str(TMDB_MOVIE_ID)]}

    assert len(subtitles) == 1
    assert subtitles[0].page_link == (f"https://legendas.net/legenda?movie_id={TMDB_MOVIE_ID}&legenda_id=6382")


def test_movie_search_falls_back_to_title_without_tmdb_id(requests_mock):
    requests_mock.get(MOVIE_SEARCH_URL, json={"movies": [], "page": 1, "per_page": 25, "has_more": False})
    provider = _make_provider(requests_mock)

    movie = Movie("Buddy.2026.mkv", "Buddy", year=2026, imdb_id="tt37281055")
    assert provider.list_subtitles(movie, {Language("por", "BR")}) == []

    search = [r for r in requests_mock.request_history if r.method == "GET"][0]
    assert search.qs == {"page": ["1"], "per_page": ["25"], "name": ["buddy"]}


TV_ITEM = {
    "id": 10,
    "path": "/api/v1/download/tv/21/10/show.srt?movie_id=21&legenda_id=10",
    "tmdb_id": 21,
    "name": "Show",
    "season": 1,
    "episode": 2,
    "release_name": None,
    "uploader": "someone",
}


def test_episode_search_uses_series_tmdb_id(requests_mock):
    # Regression test for #3668: the series TMDB id is sent when known, with no name filter.
    requests_mock.get(TV_SEARCH_URL, json={"tv_shows": [TV_ITEM], "page": 1, "per_page": 25, "has_more": False})
    provider = _make_provider(requests_mock)

    episode = Episode("Show.S01E02.mkv", "Show", 1, 2, series_imdb_id="tt0903747", tvdb_id=123)
    episode.series_tmdb_id = 21
    subtitles = provider.list_subtitles(episode, {Language("por", "BR")})

    search = [r for r in requests_mock.request_history if r.method == "GET"][0]
    assert search.body is None
    assert search.qs == {"page": ["1"], "per_page": ["25"], "tv_season": ["1"], "tv_episode": ["2"],
                         "tmdb_id": ["21"]}

    assert len(subtitles) == 1
    assert subtitles[0].page_link == "https://legendas.net/tv_legenda?movie_id=21&legenda_id=10"
    assert subtitles[0].releases == [""]


def test_episode_search_falls_back_to_series_name(requests_mock):
    # Without a known series TMDB id, the search falls back to the series name.
    requests_mock.get(TV_SEARCH_URL, json={"tv_shows": [TV_ITEM], "page": 1, "per_page": 25, "has_more": False})
    provider = _make_provider(requests_mock)

    episode = Episode("Show.S01E02.mkv", "Show", 1, 2, series_imdb_id="tt0903747", tvdb_id=123)
    subtitles = provider.list_subtitles(episode, {Language("por", "BR")})

    search = [r for r in requests_mock.request_history if r.method == "GET"][0]
    assert search.body is None
    assert search.qs == {"page": ["1"], "per_page": ["25"], "tv_season": ["1"], "tv_episode": ["2"],
                         "name": ["show"]}

    assert len(subtitles) == 1
    assert subtitles[0].page_link == "https://legendas.net/tv_legenda?movie_id=21&legenda_id=10"
    assert subtitles[0].releases == [""]
