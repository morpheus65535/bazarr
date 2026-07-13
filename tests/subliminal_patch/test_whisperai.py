# -*- coding: utf-8 -*-
import os

from unittest.mock import patch

from subliminal_patch.providers.whisperai import _get_ffprobe_path


def test_ffprobe_path_uses_bazarr_binary_helper():
    # ffprobe is resolved through Bazarr's own get_binary helper (the same one
    # subsyncer.py uses), so the configured/bundled binary is used rather than
    # relying on a bare 'ffprobe' being on the system PATH.
    resolved = os.path.join("opt", "bazarr", "bin", "ffmpeg", "ffprobe")
    with patch("utilities.binaries.get_binary", return_value=resolved):
        assert _get_ffprobe_path() == resolved


def test_ffprobe_path_falls_back_when_binary_not_found():
    # If get_binary can't locate ffprobe, fall back to the bare name (the
    # previous PATH-based behaviour).
    expected = "ffprobe.exe" if os.name == "nt" else "ffprobe"
    with patch("utilities.binaries.get_binary", return_value=None):
        assert _get_ffprobe_path() == expected
