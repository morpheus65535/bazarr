# -*- coding: utf-8 -*-
import os

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
