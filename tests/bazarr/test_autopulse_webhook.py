# -*- coding: utf-8 -*-
"""
Tests for the external webhook and Autopulse helpers in utilities/autopulse_webhook.py.

Covers the fix in commit fe6092c19 (None values in call_external_webhook), config
generation from the Autopulse template, webhook URL and auth resolution, and path
rewrite detection. The last two xfail cases document defects found while writing
these tests; they are strict, so they will fail loudly once the code is fixed.
"""
from types import SimpleNamespace
from unittest import mock
from urllib.parse import parse_qs, urlsplit

import pytest
import requests

from utilities import autopulse_webhook as aw


class _Section(dict):
    """Dict that also allows attribute access, like the settings sections."""

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as e:
            raise AttributeError(name) from e


@pytest.fixture
def settings():
    general = _Section(
        use_external_webhook=True,
        external_webhook_url="http://autopulse:2875/triggers/bazarr",
        external_webhook_username="",
        external_webhook_password="",
        movie_path="",
        series_path="",
    )
    plex = _Section(server_url="http://plex:32400", server_name="Plex", auth_method="oauth")
    fake = SimpleNamespace(general=general, plex=plex)
    with mock.patch.object(aw, "settings", fake):
        yield fake


def _query_of(url):
    return parse_qs(urlsplit(url).query, keep_blank_values=True)


# call_external_webhook

def test_call_external_webhook_sends_empty_strings_for_none_values(settings):
    """Regression for fe6092c19: None values must not break the request."""
    with mock.patch.object(aw, "_make_webhook_request") as request:
        request.return_value = mock.Mock(status_code=200)

        aw.call_external_webhook(
            subtitle_path=None, media_path=None, language=None, media_type=None, action_type=None
        )

    request.assert_called_once()
    assert _query_of(request.call_args.args[0]) == {
        "path": [""],
        "action_type": [""],
        "language": [""],
        "media_type": [""],
        "subtitle_path": [""],
        "media_path": [""],
    }


def test_call_external_webhook_sends_parent_directory_of_media(settings):
    with mock.patch.object(aw, "_make_webhook_request") as request:
        request.return_value = mock.Mock(status_code=200)

        aw.call_external_webhook(
            subtitle_path="/media/tv/show/ep.en.srt",
            media_path="/media/tv/show/ep.mkv",
            language="en",
            media_type="series",
            action_type="download",
        )

    query = _query_of(request.call_args.args[0])
    assert query["path"] == ["/media/tv/show"]
    assert query["media_path"] == ["/media/tv/show/ep.mkv"]
    assert query["subtitle_path"] == ["/media/tv/show/ep.en.srt"]
    assert query["language"] == ["en"]
    assert query["media_type"] == ["series"]
    assert query["action_type"] == ["download"]


def test_call_external_webhook_passes_basic_auth_when_configured(settings):
    settings.general["external_webhook_username"] = "user"
    settings.general["external_webhook_password"] = "secret"

    with mock.patch.object(aw, "_make_webhook_request") as request:
        request.return_value = mock.Mock(status_code=200)
        aw.call_external_webhook(None, "/media/x.mkv", "en", "movie", "download")

    assert request.call_args.args[1] == ("user", "secret")


def test_call_external_webhook_does_nothing_when_disabled(settings):
    settings.general["use_external_webhook"] = False

    with mock.patch.object(aw, "_make_webhook_request") as request:
        aw.call_external_webhook(None, "/media/x.mkv", "en", "movie", "download")

    request.assert_not_called()


def test_call_external_webhook_does_nothing_without_url(settings):
    settings.general["external_webhook_url"] = "   "

    with mock.patch.object(aw, "_make_webhook_request") as request:
        aw.call_external_webhook(None, "/media/x.mkv", "en", "movie", "download")

    request.assert_not_called()


def test_call_external_webhook_swallows_request_errors(settings):
    with mock.patch.object(aw, "_make_webhook_request", side_effect=requests.exceptions.ConnectionError("down")):
        # Must not raise: webhook failures should never break subtitle processing.
        aw.call_external_webhook(None, "/media/x.mkv", "en", "movie", "download")


@pytest.mark.parametrize("status_code", [200, 400, 401, 500])
def test_call_external_webhook_handles_every_status_code(settings, status_code):
    with mock.patch.object(aw, "_make_webhook_request") as request:
        request.return_value = mock.Mock(status_code=status_code)
        aw.call_external_webhook(None, "/media/x.mkv", "en", "movie", "download")

    request.assert_called_once()


# URL and auth resolution

@pytest.mark.parametrize("url", ["autopulse:2875/triggers/bazarr", "ftp://autopulse/triggers/bazarr"])
def test_get_webhook_url_rejects_non_http_schemes(settings, url):
    settings.general["external_webhook_url"] = url

    assert aw._get_webhook_url() is None


def test_get_webhook_url_returns_stripped_http_url(settings):
    settings.general["external_webhook_url"] = "  https://autopulse.local/triggers/bazarr  "

    assert aw._get_webhook_url() == "https://autopulse.local/triggers/bazarr"


def test_get_webhook_auth_requires_both_username_and_password(settings):
    settings.general["external_webhook_username"] = "user"
    assert aw._get_webhook_auth() is None

    settings.general["external_webhook_password"] = "pass"
    assert aw._get_webhook_auth() == ("user", "pass")


@pytest.mark.parametrize(
    "webhook_url, expected",
    [
        ("http://autopulse:2875/triggers/bazarr", "http://autopulse:2875/api/config-template"),
        ("http://autopulse:2875/", "http://autopulse:2875/api/config-template"),
    ],
)
def test_get_autopulse_template_url(settings, webhook_url, expected):
    settings.general["external_webhook_url"] = webhook_url

    assert aw._get_autopulse_template_url() == expected


# Config generation

TEMPLATE = (
    '[triggers.bazarr]\n'
    'type = "bazarr"\n'
    '\n'
    '[targets.plex]\n'
    'url = "{url}"\n'
    'token = "{token}"\n'
    'username = "{username}"\n'
    'password = "{password}"\n'
    'refresh = false\n'
    'analyze = true\n'
)


@pytest.fixture
def no_rewrite(settings):
    with mock.patch.object(aw, "_detect_path_rewrite", return_value=aw._empty_rewrite_config()):
        yield


def test_generate_config_from_template_replaces_placeholders(settings, no_rewrite):
    with mock.patch.object(aw, "_get_webhook_auth", return_value=("user", "pass")):
        result = aw._generate_config_from_template(
            {"config": TEMPLATE, "version": "1.2.3"}, "http://plex:32400", "tok123", "Plex"
        )

    config = result["config_yaml"]
    assert 'url = "http://plex:32400"' in config
    assert 'token = "tok123"' in config
    assert 'username = "user"' in config
    assert 'password = "pass"' in config
    assert result["server_name"] == "Plex"
    assert result["rewrite_detected"] is False
    assert result["rewrite_suggestion"] is None
    assert "Configuration generated using Autopulse template v1.2.3" == result["template_info"]


def test_generate_config_from_template_overrides_autopulse_defaults(settings, no_rewrite):
    with mock.patch.object(aw, "_get_webhook_auth", return_value=None):
        config = aw._generate_config_from_template(
            {"config": TEMPLATE}, "http://plex:32400", "tok", "Plex"
        )["config_yaml"]

    assert "refresh = true" in config
    assert "analyze = false" in config
    assert "refresh = false" not in config


def test_generate_config_from_template_blanks_auth_when_unset(settings, no_rewrite):
    with mock.patch.object(aw, "_get_webhook_auth", return_value=None):
        config = aw._generate_config_from_template(
            {"config": TEMPLATE}, "http://plex:32400", "tok", "Plex"
        )["config_yaml"]

    assert 'username = ""' in config
    assert 'password = ""' in config
    assert "{username}" not in config
    assert "{password}" not in config


def test_generate_config_from_template_returns_none_without_config(settings, no_rewrite):
    assert aw._generate_config_from_template({"version": "1"}, "http://plex", "tok", "Plex") is None


def test_generate_config_from_template_includes_detected_rewrite(settings):
    rewrite = {
        "detected": True,
        "suggestion": "Detected mount point difference",
        "trigger_section": '\nrewrite.from = "/mnt/"\nrewrite.to = "/"',
        "target_section": '\nrewrite.from = "/"\nrewrite.to = "/mnt/"',
    }
    with mock.patch.object(aw, "_detect_path_rewrite", return_value=rewrite), \
            mock.patch.object(aw, "_get_webhook_auth", return_value=None):
        result = aw._generate_config_from_template({"config": TEMPLATE}, "http://plex", "tok", "Plex")

    assert result["rewrite_detected"] is True
    assert result["rewrite_suggestion"] == "Detected mount point difference"
    assert "Path rewriting: Enabled" in result["config_yaml"]
    assert 'rewrite.from = "/mnt/"' in result["config_yaml"]


def test_generate_autopulse_config_requires_oauth(settings):
    settings.plex["auth_method"] = "apikey"

    with mock.patch.object(aw, "_get_autopulse_template") as template:
        assert aw.generate_autopulse_config(decrypted_token="tok") is None

    template.assert_not_called()


def test_generate_autopulse_config_returns_none_without_token(settings):
    with mock.patch("api.plex.oauth.get_decrypted_token", return_value=None), \
            mock.patch.object(aw, "_get_autopulse_template") as template:
        assert aw.generate_autopulse_config() is None

    template.assert_not_called()


def test_generate_autopulse_config_returns_none_when_template_unavailable(settings):
    with mock.patch.object(aw, "_get_autopulse_template", return_value=None):
        assert aw.generate_autopulse_config(decrypted_token="tok") is None


def test_generate_autopulse_config_end_to_end(settings, no_rewrite):
    with mock.patch.object(aw, "_get_autopulse_template", return_value={"config": TEMPLATE, "version": "2"}), \
            mock.patch.object(aw, "_get_webhook_auth", return_value=None):
        result = aw.generate_autopulse_config(decrypted_token="tok")

    assert result is not None
    assert 'token = "tok"' in result["config_yaml"]
    assert result["server_name"] == "Plex"


# Path rewrite detection

def test_compare_path_sets_identical_paths_are_not_rewritten(settings):
    result = aw._compare_path_sets("/media/movies/", ["/media/movies"], "movie")

    assert result["detected"] is False


def test_detect_common_patterns_finds_mnt_prefix(settings):
    settings.general["movie_path"] = "/mnt/movies"

    result = aw._detect_common_patterns()

    assert result["detected"] is True
    assert result["trigger_section"] == '\nrewrite.from = "/mnt"\nrewrite.to = ""'


def test_detect_common_patterns_returns_empty_without_match(settings):
    settings.general["movie_path"] = "/srv/movies"
    settings.general["series_path"] = "/srv/tv"

    assert aw._detect_common_patterns()["detected"] is False


@pytest.mark.parametrize(
    "bazarr_path, plex_path, expected_prefix",
    [
        ("/mnt/media/movies", "/media/movies", "/mnt"),
        ("/media/movies", "/data/media/movies", "/data"),
    ],
)
def test_detect_mount_point_difference_absolute_paths(bazarr_path, plex_path, expected_prefix):
    result = aw._detect_mount_point_difference(bazarr_path, plex_path, "movie")

    assert result["detected"] is True
    assert f"'{expected_prefix}' prefix" in result["suggestion"]


def test_detect_mount_point_difference_bazarr_extra_prefix_section_text():
    result = aw._detect_mount_point_difference("/mnt/media/movies", "/media/movies", "movie")

    assert result["trigger_section"] == '\nrewrite.from = "/mnt/"\nrewrite.to = "/"'
    assert result["target_section"] == '\nrewrite.from = "/"\nrewrite.to = "/mnt/"'


def test_detect_mount_point_difference_plex_extra_prefix_section_text():
    result = aw._detect_mount_point_difference("/media/movies", "/data/media/movies", "movie")

    assert result["trigger_section"] == '\nrewrite.from = "/"\nrewrite.to = "/data/"'
    assert result["target_section"] == '\nrewrite.from = "/data/"\nrewrite.to = "/"'


def test_detect_mount_point_difference_no_match_for_unrelated_paths():
    assert aw._detect_mount_point_difference("/srv/movies", "/media/tv", "movie")["detected"] is False


# TOML injection

def test_inject_rewrite_config_places_trigger_rewrite_inside_trigger_section():
    text = '[triggers.bazarr]\ntype = "bazarr"\n[targets.plex]\nurl = "x"\n'
    rewrite = {
        "trigger_section": '\nrewrite.from = "/mnt/"\nrewrite.to = "/"',
        "target_section": '\nrewrite.from = "/"\nrewrite.to = "/mnt/"',
    }

    result = aw._inject_rewrite_config(text, rewrite)

    assert result == (
        '[triggers.bazarr]\ntype = "bazarr"\n'
        'rewrite.from = "/mnt/"\nrewrite.to = "/"\n'
        '[targets.plex]\nurl = "x"\n\n'
        'rewrite.from = "/"\nrewrite.to = "/mnt/"'
    )


def test_inject_rewrite_config_places_target_rewrite_before_next_section():
    text = '[targets.plex]\nurl = "x"\n[other]\nkey = 1\n'
    rewrite = {
        "trigger_section": "",
        "target_section": '\nrewrite.from = "/"\nrewrite.to = "/mnt/"',
    }

    result = aw._inject_rewrite_config(text, rewrite)

    assert result == (
        '[targets.plex]\nurl = "x"\n'
        'rewrite.from = "/"\nrewrite.to = "/mnt/"\n'
        '[other]\nkey = 1\n'
    )


def test_inject_rewrite_config_is_noop_without_rewrite():
    text = '[triggers.bazarr]\ntype = "bazarr"\n[targets.plex]\nurl = "x"\n'

    assert aw._inject_rewrite_config(text, aw._empty_rewrite_config()) == text


# Connectivity test helper

@pytest.mark.parametrize(
    "status_code, expected_success",
    [(200, True), (401, False), (400, False), (503, False)],
)
def test_webhook_connection_maps_status_codes(settings, status_code, expected_success):
    with mock.patch.object(aw.requests, "get", return_value=mock.Mock(status_code=status_code)) as get:
        success, _message = aw.test_external_webhook_connection()

    assert success is expected_success
    assert get.call_args.args[0] == "http://autopulse:2875/stats"


def test_webhook_connection_reports_missing_url(settings):
    settings.general["use_external_webhook"] = False

    success, message = aw.test_external_webhook_connection()

    assert success is False
    assert "not configured" in message
