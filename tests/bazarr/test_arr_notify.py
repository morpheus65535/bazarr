# -*- coding: utf-8 -*-
"""
Tests for the Sonarr and Radarr rescan notifications (sonarr/notify.py, radarr/notify.py).
"""
import importlib
from types import SimpleNamespace
from unittest import mock

import pytest
import requests

CASES = [
    pytest.param(("sonarr", "notify_sonarr", "RescanSeries", "seriesId"), id="sonarr"),
    pytest.param(("radarr", "notify_radarr", "RescanMovie", "movieId"), id="radarr"),
]


class _Section(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as e:
            raise AttributeError(name) from e


@pytest.fixture
def arr(request):
    arr_name, func_name, command, id_key = request.param
    module = importlib.import_module(f"{arr_name}.notify")
    settings = SimpleNamespace(**{arr_name: _Section(apikey="key123", http_timeout="7")})
    with mock.patch.object(module, "settings", settings), \
            mock.patch.object(module, f"url_api_{arr_name}", return_value=f"http://{arr_name}/api/v3/"):
        yield SimpleNamespace(
            module=module,
            notify=getattr(module, func_name),
            command=command,
            id_key=id_key,
            name=arr_name,
        )


@pytest.mark.parametrize("arr", CASES, indirect=True)
def test_notify_posts_rescan_command_with_integer_id(arr):
    with mock.patch.object(arr.module.requests, "post") as post:
        arr.notify("42")

    post.assert_called_once()
    assert post.call_args.args[0] == f"http://{arr.name}/api/v3/command?apikey=key123"
    assert post.call_args.kwargs["json"] == {"name": arr.command, arr.id_key: 42}
    assert post.call_args.kwargs["timeout"] == 7


@pytest.mark.parametrize("arr", CASES, indirect=True)
def test_notify_logs_and_swallows_request_errors(arr, caplog):
    with mock.patch.object(arr.module.requests, "post", side_effect=requests.exceptions.ConnectionError("down")):
        arr.notify(1)

    assert f"BAZARR cannot notify {arr.name.capitalize()}" in caplog.text


@pytest.mark.parametrize("arr", CASES, indirect=True)
def test_notify_rejects_non_numeric_id_without_raising(arr, caplog):
    with mock.patch.object(arr.module.requests, "post") as post:
        arr.notify("not-a-number")

    post.assert_not_called()
    assert f"BAZARR cannot notify {arr.name.capitalize()}" in caplog.text
