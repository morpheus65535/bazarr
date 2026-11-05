# -*- coding: utf-8 -*-
"""
Tests for PATCH /api/subtitles: the subtitles file and sync reference must be indexed by Bazarr,
so the endpoint cannot be used to modify arbitrary files on disk.
"""
from types import SimpleNamespace
from unittest import mock

import pytest

SRT_CONTENT = "1\n00:00:01,000 --> 00:00:02,000\nHi\n"


@pytest.fixture
def subtitle(tmp_path):
    path = tmp_path / "show.en.srt"
    path.write_text(SRT_CONTENT, encoding="utf-8")
    return path


@pytest.fixture
def episode_lookup():
    """Stand in for the episode metadata query the PATCH handler runs before acting on a file."""
    metadata = SimpleNamespace(path="/tv/show/ep.mkv", sonarrSeriesId=1, season=1, episode=1,
                               imdbId=None, tvdbId=None)
    database = mock.MagicMock()
    database.execute.return_value.first.return_value = metadata
    with mock.patch("api.subtitles.subtitles.database", database), \
            mock.patch("api.subtitles.subtitles.path_mappings",
                       mock.MagicMock(path_replace=lambda p: p, path_replace_movie=lambda p: p,
                                      path_replace_reverse=lambda p: p,
                                      path_replace_reverse_movie=lambda p: p)), \
            mock.patch("api.subtitles.subtitles.sync_subtitles") as sync:
        yield sync


def _sync(api_client, api_key, path, reference=None):
    data = {"action": "sync", "language": "en", "path": str(path), "type": "episode", "id": "1"}
    if reference is not None:
        data["reference"] = reference
    return api_client.patch("/api/subtitles", data=data, headers={"X-API-KEY": api_key})


def test_patch_refuses_unindexed_subtitles_path(api_client, api_key, subtitle, indexed_subtitles, episode_lookup):
    response = _sync(api_client, api_key, subtitle)

    assert response.status_code == 404
    assert "not indexed by Bazarr" in response.get_data(as_text=True)
    episode_lookup.assert_not_called()


def test_patch_refuses_unindexed_sync_reference(api_client, api_key, subtitle, indexed_subtitles, episode_lookup,
                                                tmp_path):
    indexed_subtitles(str(subtitle))
    other = tmp_path / "other.en.srt"
    other.write_text(SRT_CONTENT, encoding="utf-8")

    response = _sync(api_client, api_key, subtitle, reference=str(other))

    assert response.status_code == 404
    assert "Reference subtitles file is not indexed" in response.get_data(as_text=True)
    episode_lookup.assert_not_called()


def test_patch_accepts_indexed_subtitles_path(api_client, api_key, subtitle, indexed_subtitles, episode_lookup):
    indexed_subtitles(str(subtitle))

    response = _sync(api_client, api_key, subtitle)

    assert response.status_code == 204
    assert episode_lookup.call_args.kwargs["srt_path"] == str(subtitle)


def test_patch_accepts_indexed_path_sent_in_mapped_form(api_client, api_key, subtitle, indexed_subtitles,
                                                        episode_lookup):
    # The index stores the Sonarr-side path; the UI sends the local path that path mapping produces
    indexed_subtitles("/sonarr/show.en.srt")
    mapping = mock.MagicMock(
        path_replace=lambda p: p, path_replace_movie=lambda p: p,
        path_replace_reverse=lambda p: p.replace(str(subtitle.parent), "/sonarr"),
        path_replace_reverse_movie=lambda p: p.replace(str(subtitle.parent), "/sonarr"),
    )

    with mock.patch("api.subtitles.subtitles.path_mappings", mapping):
        response = _sync(api_client, api_key, subtitle)

    assert response.status_code == 204


@pytest.mark.parametrize("reference", ["a:0", "/tv/show/ep.mkv"])
def test_patch_accepts_audio_track_and_video_references(api_client, api_key, subtitle, indexed_subtitles,
                                                        episode_lookup, reference):
    indexed_subtitles(str(subtitle))

    response = _sync(api_client, api_key, subtitle, reference=reference)

    assert response.status_code == 204


def test_patch_accepts_indexed_sync_reference(api_client, api_key, subtitle, indexed_subtitles, episode_lookup,
                                              tmp_path):
    indexed_subtitles(str(subtitle))
    reference = tmp_path / "reference.en.srt"
    reference.write_text(SRT_CONTENT, encoding="utf-8")
    indexed_subtitles(str(reference))

    response = _sync(api_client, api_key, subtitle, reference=str(reference))

    assert response.status_code == 204
