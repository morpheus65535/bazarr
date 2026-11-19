# -*- coding: utf-8 -*-
import json
import os
import subprocess
from unittest import mock

from subliminal_patch.providers import whisperai
from subliminal_patch.providers.whisperai import WhisperAIProvider


def _make_provider(ffprobe_path):
    return WhisperAIProvider(
        endpoint="http://localhost:9000",
        response=1,
        timeout=1,
        ffmpeg_path=os.path.join("opt", "bazarr", "bin", "ffmpeg"),
        ffprobe_path=ffprobe_path,
        pass_video_name=False,
        loglevel="INFO",
    )


def test_ffprobe_path_uses_provided_value():
    # Bazarr resolves ffprobe in get_providers (via get_binary) and passes it
    # in, so the provider must use exactly that rather than relying on a bare
    # 'ffprobe' being on the system PATH.
    resolved = os.path.join("opt", "bazarr", "bin", "ffprobe")
    assert _make_provider(resolved).ffprobe_path == resolved


def test_ffprobe_path_falls_back_when_not_provided():
    # When no ffprobe path is provided, fall back to the bare name (the
    # previous PATH-based behaviour).
    expected = "ffprobe.exe" if os.name == "nt" else "ffprobe"
    assert _make_provider(None).ffprobe_path == expected


def _mock_ffprobe(format_start, packet_pts, stream_index=1):
    # Mimics the JSON ffprobe prints for the command built in get_audio_delay
    payload = {
        "streams": [{"index": stream_index, "tags": {"language": "jpn"}}],
        "format": {"start_time": format_start},
        "packets": [{"stream_index": stream_index, "pts_time": packet_pts}],
    }
    return subprocess.CompletedProcess(args=[], returncode=0, stdout=json.dumps(payload), stderr="")


def _detect_delay(format_start, packet_pts, audio_language="ja"):
    provider = _make_provider(os.path.join("opt", "bazarr", "bin", "ffprobe"))
    with mock.patch.object(whisperai.subprocess, "run", return_value=_mock_ffprobe(format_start, packet_pts)):
        return provider.get_audio_delay("episode.ts", audio_language)


def test_audio_delay_ignores_container_start_offset():
    # MPEG-TS broadcast capture: container and first audio packet both start at
    # ~67224s. That is not a delay, so no silence should be inserted.
    assert _detect_delay("67224.300433", "67224.300433") == 0


def test_audio_delay_is_relative_to_container_start():
    # Audio starting 0.5s after the container start is a real 500ms delay.
    assert _detect_delay("67224.300000", "67224.800000") == 500


def test_audio_delay_applies_when_container_start_is_zero():
    assert _detect_delay("0.000000", "1.250000") == 1250


def test_implausible_audio_delay_is_ignored():
    # A packet far past the container start must not produce a huge adelay.
    assert _detect_delay("0.000000", "67224.300433") == 0


def test_unknown_container_start_falls_back_to_zero():
    # ffprobe prints 'N/A' for an unknown start time; the delay should still be
    # computed rather than crashing into the generic exception handler.
    provider = _make_provider(os.path.join("opt", "bazarr", "bin", "ffprobe"))
    payload = _mock_ffprobe("N/A", "0.500000")
    with mock.patch.object(whisperai.subprocess, "run", return_value=payload):
        assert provider.get_audio_delay("episode.ts", "ja") == 500
