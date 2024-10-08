import pytest
import subliminal
import datetime
import tempfile
import os

from subliminal_patch.providers.titlovi import TitloviProvider 
from subliminal_patch.providers.titlovi import TitloviSubtitle 
from dogpile.cache.region import register_backend as register_cache_backend
from subliminal_patch.core import Episode
from subzero.language import Language
from subliminal.subtitle import fix_line_ending

from zipfile import ZipFile

@pytest.fixture(scope="session")
def titlovi_episodes():
    return {
        "la_femme_nikita_s01e13": Episode(
            "La Femme Nikita (1997) - S01E13 - Recruit [HDTV-720p][Opus 2.0][x265].mkv",
            "La Femme Nikita",
            1,
            13,
            series_imdb_id="tt21209876",
            video_codec="x265",
        ),
    }

@pytest.fixture(scope="session")
def region():
    register_cache_backend("subzero.cache.file", "subzero.cache_backends.file", "SZFileBackend")
    subliminal.region.configure(
        "subzero.cache.file",
        expiration_time=datetime.timedelta(days=30),
        arguments={"appname": "sz_cache", "app_cache_dir": tempfile.gettempdir()},
        replace_existing_backend=True,
    )
    subliminal.region.backend.sync()

def test_list_subtitles_and_download_from_pack(region, titlovi_episodes, requests_mock, data):
    language = Language.fromietf('sr-Latn')
    item = titlovi_episodes["la_femme_nikita_s01e13"]

    with open(os.path.join(data, 'titlovi_gettoken_response.json'), "rb") as f:
        response = f.read()
        requests_mock.post('https://kodi.titlovi.com/api/subtitles/gettoken?username=user1&password=pass1&json=True', content=response)

    with open(os.path.join(data, 'titlovi_search_response.json'), "rb") as f:
        response = f.read()
        requests_mock.get('https://kodi.titlovi.com/api/subtitles/search?token=asdf1234&userid=111&&query=la femme nikita&lang=Srpski&json=True', content=response)
        
    with open(os.path.join(data, 'titlovi_some_subtitle_pack.zip'), "rb") as f:
        response = f.read()
        requests_mock.get('https://titlovi.com/download/?type=1&mediaid=81022', content=response)
        
    with TitloviProvider('user1','pass1') as provider:
        subtitles = provider.list_subtitles(item, languages={language})

        assert len(subtitles) == 1

        subtitle = subtitles[0]
        provider.download_subtitle(subtitle)
        with open(os.path.join(data, 'titlovi_some_subtitle_pack.zip'), "rb") as f:
          archive = ZipFile(f)
          # subs_in_archive = archive.namelist()
          subtitle_content = fix_line_ending(archive.read('La Femme Nikita - 01x13 - Recruit.srt'))
          assert(subtitle.content == subtitle_content)


