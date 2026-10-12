# -*- coding: utf-8 -*-
"""
Tests for API endpoints that take file paths or file names from the client:
subtitles/contents, subtitles/info, files/sonarr, and files/radarr.
"""
import importlib
from unittest import mock
from urllib.parse import parse_qs, urlsplit

import pytest

SRT_CONTENT = (
    "1\n"
    "00:00:01,000 --> 00:00:02,500\n"
    "Hello\n"
    "\n"
    "2\n"
    "00:00:03,000 --> 00:00:04,000\n"
    "World\n"
)


@pytest.fixture
def srt_file(tmp_path):
    path = tmp_path / "show.en.srt"
    path.write_text(SRT_CONTENT, encoding="utf-8")
    return path


# subtitles/contents

def test_contents_parses_srt_file(api_client, api_key, srt_file):
    response = api_client.get("/api/subtitles/contents", query_string={"subtitlePath": str(srt_file)},
                              headers={"X-API-KEY": api_key})

    assert response.status_code == 200
    entries = response.json["data"]
    assert [entry["content"] for entry in entries] == ["Hello", "World"]
    assert entries[0]["index"] == 1
    assert entries[0]["start"]["total_seconds"] == 1
    assert entries[0]["end"]["total_seconds"] == 2
    assert entries[0]["end"]["microseconds"] == 500000


def test_contents_requires_subtitle_path(api_client, api_key):
    response = api_client.get("/api/subtitles/contents", headers={"X-API-KEY": api_key})

    assert response.status_code == 400


def test_contents_rejects_missing_file(api_client, api_key, tmp_path):
    response = api_client.get("/api/subtitles/contents",
                              query_string={"subtitlePath": str(tmp_path / "missing.srt")},
                              headers={"X-API-KEY": api_key})

    assert response.status_code == 400


def test_contents_rejects_binary_file(api_client, api_key, tmp_path):
    path = tmp_path / "binary.srt"
    path.write_bytes(bytes(range(256)) * 40)

    response = api_client.get("/api/subtitles/contents", query_string={"subtitlePath": str(path)},
                              headers={"X-API-KEY": api_key})

    assert response.status_code == 400


def test_contents_refuses_non_subtitle_file(api_client, api_key, tmp_path):
    notes = tmp_path / "notes.txt"
    notes.write_text(SRT_CONTENT.replace("Hello", "not-a-subtitle"), encoding="utf-8")

    response = api_client.get("/api/subtitles/contents", query_string={"subtitlePath": str(notes)},
                              headers={"X-API-KEY": api_key})

    assert response.status_code == 400
    assert "not-a-subtitle" not in response.get_data(as_text=True)


def test_contents_accepts_uppercase_subtitle_extension(api_client, api_key, tmp_path):
    path = tmp_path / "SHOW.EN.SRT"
    path.write_text(SRT_CONTENT, encoding="utf-8")

    response = api_client.get("/api/subtitles/contents", query_string={"subtitlePath": str(path)},
                              headers={"X-API-KEY": api_key})

    assert response.status_code == 200


# subtitles/info

def test_info_guesses_season_and_episode_from_filename(api_client, api_key):
    response = api_client.get(
        "/api/subtitles/info",
        query_string=[("filenames[]", "Show.Name.S02E05.en.srt"), ("filenames[]", "random-clip.srt")],
        headers={"X-API-KEY": api_key},
    )

    assert response.status_code == 200
    first, second = response.json["data"]
    assert first["filename"] == "Show.Name.S02E05.en.srt"
    assert first["season"] == 2
    assert first["episode"] == 5
    assert first["subtitle_language"] == "en"
    assert second["season"] == 0
    assert second["episode"] == 0


def test_info_requires_filenames(api_client, api_key):
    response = api_client.get("/api/subtitles/info", headers={"X-API-KEY": api_key})

    assert response.status_code == 400


# files/sonarr and files/radarr

@pytest.mark.parametrize("arr", ["sonarr", "radarr"])
def test_files_browser_lists_directories(api_client, api_key, arr):
    listing = {"directories": [{"name": "tv", "path": "/tv"}, {"name": "anime", "path": "/anime"}]}

    with mock.patch(f"api.files.files_{arr}.browse_{arr}_filesystem", return_value=listing) as browse:
        response = api_client.get(f"/api/files/{arr}", query_string={"path": "/"},
                                  headers={"X-API-KEY": api_key})

    browse.assert_called_once_with("/")
    assert response.status_code == 200
    assert response.json == [
        {"name": "tv", "children": True, "path": "/tv"},
        {"name": "anime", "children": True, "path": "/anime"},
    ]


@pytest.mark.parametrize("arr", ["sonarr", "radarr"])
def test_files_browser_returns_empty_list_when_arr_unreachable(api_client, api_key, arr):
    with mock.patch(f"api.files.files_{arr}.browse_{arr}_filesystem", return_value=None):
        response = api_client.get(f"/api/files/{arr}", headers={"X-API-KEY": api_key})

    assert response.status_code == 200
    assert response.json == []


@pytest.mark.parametrize("arr", ["sonarr", "radarr"])
def test_arr_filesystem_query_encodes_path(arr):
    module = importlib.import_module(f"{arr}.filesystem")
    path = "/media&includeFiles=true"
    settings = mock.Mock()
    setattr(settings, arr, mock.Mock(apikey="real-key", http_timeout=5))

    with mock.patch.object(module, "settings", settings), \
            mock.patch.object(module, f"url_api_{arr}", return_value=f"http://{arr}/api/v3/"), \
            mock.patch.object(module.requests, "get") as get:
        get.return_value.json.return_value = {"directories": []}
        getattr(module, f"browse_{arr}_filesystem")(path)

    query = parse_qs(urlsplit(get.call_args.args[0]).query)
    assert query["path"] == [path]
    assert query["includeFiles"] == ["false"]
    assert query["apikey"] == ["real-key"]
