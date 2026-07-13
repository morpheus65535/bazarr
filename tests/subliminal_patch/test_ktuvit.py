# -*- coding: utf-8 -*-
import json

from subliminal_patch.providers.ktuvit import KtuvitProvider

SEARCH_URL = "https://www.ktuvit.me/Services/ContentProvider.svc/SearchPage_search"
MOVIE_INFO_URL = "https://www.ktuvit.me/MovieInfo.aspx?ID=KT_ID_1"

IMDB_ID = "tt2866360"  # Coherence (2014)

# A minimal MovieInfo.aspx page carrying a single subtitle row, enough for
# KtuvitProvider._search_movie() to extract one subtitle.
MOVIE_INFO_HTML = (
    '<table id="subtitlesList"><tbody><tr>'
    "<td>Coherence.2014.1080p.WEB</td><td></td><td></td><td></td><td></td>"
    '<td><a data-subtitle-id="SUB_1">download</a></td>'
    "</tr></tbody></table>"
)


def _films_by_year(request, context):
    """Return zero films for a year-filtered search, one film otherwise.

    Simulates a Ktuvit catalog entry whose ReleaseYear is missing server-side:
    the year-filtered query finds nothing, while the yearless query returns the
    exact IMDb match.
    """
    year = request.json()["request"]["Year"]
    if year:
        films = []
    else:
        films = [{"IMDB_Link": "http://www.imdb.com/title/%s" % IMDB_ID, "ID": "KT_ID_1"}]
    return {"d": json.dumps({"Films": films})}


def _make_provider():
    provider = KtuvitProvider()
    provider.initialize()  # creates the requests session, no login without creds
    provider.logged_in = True
    return provider


def test_query_falls_back_to_yearless_search(requests_mock):
    # Regression test for #3420: a movie whose Ktuvit entry has no ReleaseYear
    # must still be found by falling back to a yearless search.
    requests_mock.post(SEARCH_URL, json=_films_by_year)
    requests_mock.get(MOVIE_INFO_URL, text=MOVIE_INFO_HTML)

    provider = _make_provider()
    subtitles = list(provider.query(title="Coherence", year=2014, imdb_id=IMDB_ID))

    # both the year-filtered and the yearless search were issued
    years_sent = [r.json()["request"]["Year"] for r in requests_mock.request_history if r.method == "POST"]
    assert years_sent == [2014, ""]

    assert len(subtitles) == 1
    assert subtitles[0].imdb_id == IMDB_ID
    assert subtitles[0].subtitle_id == "SUB_1"


def test_query_does_not_fall_back_when_year_search_matches(requests_mock):
    # When the year-filtered search already returns the film, no extra
    # yearless request should be made (common path stays unchanged).
    film = [{"IMDB_Link": "http://www.imdb.com/title/%s" % IMDB_ID, "ID": "KT_ID_1"}]
    requests_mock.post(SEARCH_URL, json={"d": json.dumps({"Films": film})})
    requests_mock.get(MOVIE_INFO_URL, text=MOVIE_INFO_HTML)

    provider = _make_provider()
    subtitles = list(provider.query(title="Coherence", year=2014, imdb_id=IMDB_ID))

    post_calls = [r for r in requests_mock.request_history if r.method == "POST"]
    assert len(post_calls) == 1
    assert post_calls[0].json()["request"]["Year"] == 2014
    assert len(subtitles) == 1
