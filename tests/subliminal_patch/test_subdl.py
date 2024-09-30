import os

import pytest
from subliminal_patch.providers.subdl import SubdlProvider
from subliminal_patch.providers.subdl import SubdlSubtitle


@pytest.fixture(scope="session")
def provider():
    with SubdlProvider(os.environ["SUBDL_TOKEN"]) as provider:
        yield provider


def test_list_subtitles_movie(provider, movies, languages):
    for sub in provider.list_subtitles(movies["dune"], {languages["en"]}):
        assert sub.language == languages["en"]


def test_download_subtitle(provider, languages):
    data = {
        "language": languages["en"],
        "forced": False,
        "hearing_impaired": False,
        "page_link": "https://subdl.com/s/info/ebC6BrLCOC",
        "download_link": "/subtitle/2808552-2770424.zip",
        "file_id": "SUBDL::dune-2021-2770424.zip",
        "release_names": ["Dune Part 1 WebDl"],
        "uploader": "makoto77",
        "season": 0,
        "episode": None,
    }

    sub = SubdlSubtitle(**data)
    provider.download_subtitle(sub)

    assert sub.is_valid()
