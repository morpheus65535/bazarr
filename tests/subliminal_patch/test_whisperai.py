# -*- coding: utf-8 -*-
import os

from subliminal_patch.providers.whisperai import _get_ffprobe_path


def test_ffprobe_path_derived_from_configured_ffmpeg_directory():
    # ffprobe lives alongside the configured ffmpeg binary, so it must be
    # invoked by its full path rather than relying on the system PATH.
    ffmpeg_path = os.path.join("opt", "bazarr", "bin", "ffmpeg")
    expected_name = "ffprobe.exe" if os.name == "nt" else "ffprobe"
    assert _get_ffprobe_path(ffmpeg_path) == os.path.join(
        "opt", "bazarr", "bin", expected_name
    )


def test_ffprobe_path_windows_style_directory():
    # A Windows install path (with drive + backslashes) still resolves ffprobe
    # into the same directory as the configured ffmpeg executable.
    ffmpeg_path = os.path.join("C:\\Bazarr", "bin", "ffmpeg", "ffmpeg.exe")
    result = _get_ffprobe_path(ffmpeg_path)
    assert os.path.dirname(result) == os.path.dirname(ffmpeg_path)
    assert os.path.basename(result).startswith("ffprobe")


def test_ffprobe_path_falls_back_to_bare_name_without_directory():
    # No directory component -> keep the previous PATH-based behaviour.
    assert _get_ffprobe_path("ffmpeg") == "ffprobe"
    assert _get_ffprobe_path("") == "ffprobe"
    assert _get_ffprobe_path(None) == "ffprobe"
