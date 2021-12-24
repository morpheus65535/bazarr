#!/usr/bin/env python3

import os
import pytest
import datetime
import tempfile

import subliminal
from subliminal_patch.providers.addic7ed import Addic7edProvider
from subliminal_patch.providers.addic7ed import Addic7edSubtitle
from dogpile.cache.region import register_backend as register_cache_backend
from subzero.language import Language


_ENV_VARS = (
    "ANTICAPTCHA_CLASS",
    "ANTICAPTCHA_ACCOUNT_KEY",
    "ADDIC7ED_USERNAME",
    "ADDIC7ED_PASSWORD",
)


def _can_run():
    for env_var in _ENV_VARS:
        if not os.environ.get(env_var):
            return True

    return False


pytestmark = pytest.mark.skipif(
    _can_run(), reason=f"Some environment variables not set: {_ENV_VARS}"
)


@pytest.fixture(scope="session")
def region():
    register_cache_backend(
        "subzero.cache.file", "subzero.cache_backends.file", "SZFileBackend"
    )
    subliminal.region.configure(
        "subzero.cache.file",
        expiration_time=datetime.timedelta(days=30),
        arguments={"appname": "sz_cache", "app_cache_dir": tempfile.gettempdir()},
    )
    subliminal.region.backend.sync()


def test_list_subtitles_episode(region, episodes):
    item = episodes["breaking_bad_s01e01"]
    language = Language("eng")
    with Addic7edProvider(
        os.environ["ADDIC7ED_USERNAME"], os.environ["ADDIC7ED_PASSWORD"]
    ) as provider:
        subtitles = provider.list_subtitles(item, {language})
        assert len(subtitles) == 6

    subliminal.region.backend.sync()


def test_list_subtitles_movie(region, movies):
    item = movies["dune"]
    language = Language("eng")
    with Addic7edProvider(
        os.environ["ADDIC7ED_USERNAME"], os.environ["ADDIC7ED_PASSWORD"]
    ) as provider:
        subtitles = provider.list_subtitles(item, {language})
        assert len(subtitles) == 2

    subliminal.region.backend.sync()
