from types import SimpleNamespace
from unittest.mock import Mock

from bazarr.utilities import helper


def test_force_unicode_defaults_to_utf8_when_encoding_is_not_detected(monkeypatch):
    detect = Mock(return_value={"encoding": None})
    monkeypatch.setattr(helper, "detect", detect)
    monkeypatch.setattr(helper, "UnicodeDammit", lambda _: SimpleNamespace(unicode_markup=None))

    assert helper.force_unicode(b"\xff") == "\ufffd"
    detect.assert_called_once_with(b"\xff")


def test_force_unicode_replaces_undecodable_bytes_when_dammit_has_no_markup(monkeypatch):
    monkeypatch.setattr(helper, "detect", lambda _: {"encoding": "ascii"})
    monkeypatch.setattr(helper, "UnicodeDammit", lambda _: SimpleNamespace(unicode_markup=None))

    assert helper.force_unicode(b"\xff") == "\ufffd"
