# -*- coding: utf-8 -*-
"""
Tests for the Sonarr and Radarr SignalR clients and the event pipeline in app/signalr_client.py.

Importing the module starts two consumer threads over module-level deques. The fixtures swap
those deques and the last-event globals for fresh ones, so the threads cannot drain what a test
queued. Connections are mocks, and sleep is patched so reconnect loops finish immediately.
"""
import json
from collections import deque
from types import SimpleNamespace
from unittest import mock

import pytest
from requests.exceptions import ConnectionError

from app import signalr_client as sr


class _Section(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as e:
            raise AttributeError(name) from e


@pytest.fixture
def sr_settings(monkeypatch):
    fake = SimpleNamespace(
        general=_Section(use_sonarr=True, use_radarr=True),
        sonarr=_Section(apikey="sonarr-key", series_sync_on_live=True, defer_search_signalr=False, http_timeout=5),
        radarr=_Section(apikey="radarr-key", movies_sync_on_live=True, defer_search_signalr=False, http_timeout=5),
    )
    monkeypatch.setattr(sr, "settings", fake)
    monkeypatch.setattr(sr, "url_sonarr", lambda: "http://sonarr:8989")
    monkeypatch.setattr(sr, "url_radarr", lambda: "http://radarr:7878")
    return fake


@pytest.fixture
def fresh_queues(monkeypatch):
    sonarr_queue, radarr_queue = deque(), deque()
    monkeypatch.setattr(sr, "sonarr_queue", sonarr_queue)
    monkeypatch.setattr(sr, "radarr_queue", radarr_queue)
    monkeypatch.setattr(sr, "last_series_event_data", None)
    monkeypatch.setattr(sr, "last_episode_event_data", None)
    monkeypatch.setattr(sr, "last_movie_event_data", None)
    return SimpleNamespace(sonarr=sonarr_queue, radarr=radarr_queue)


@pytest.fixture
def no_signalr(monkeypatch):
    monkeypatch.setattr(sr.args, "no_signalr", True)


@pytest.fixture
def stream():
    with mock.patch.object(sr, "event_stream") as event_stream:
        yield event_stream


def _connection(state=4):
    connection = mock.MagicMock()
    connection.transport.state.value = state
    return connection


def _builder(connection):
    builder = mock.MagicMock()
    builder.with_url.return_value = builder
    builder.with_automatic_reconnect.return_value = builder
    builder.build.return_value = connection
    return builder


CLIENTS = [
    pytest.param(sr.SonarrSignalrClient, "sonarr", "update_series", "series_sync_on_live", id="sonarr"),
    pytest.param(sr.RadarrSignalrClient, "radarr", "update_movies", "movies_sync_on_live", id="radarr"),
]


# Modern SignalR clients (Sonarr v4 and Radarr)

@pytest.mark.parametrize("client_cls, name, job_id, live_flag", CLIENTS)
def test_start_retries_connection_errors_until_connected(client_cls, name, job_id, live_flag,
                                                         sr_settings, monkeypatch):
    connection = _connection()
    attempts = []

    def start():
        attempts.append(1)
        if len(attempts) < 3:
            raise ConnectionError("down")
        connection.transport.state.value = 1

    connection.start.side_effect = start
    monkeypatch.setattr(sr, "HubConnectionBuilder", lambda: _builder(connection))

    client = client_cls()
    with mock.patch.object(sr.time, "sleep") as sleep:
        client.start()

    assert connection.start.call_count == 3
    assert sleep.call_args_list == [mock.call(5), mock.call(5)]


@pytest.mark.parametrize("client_cls, name, job_id, live_flag", CLIENTS)
def test_configure_wires_hub_handlers_and_key(client_cls, name, job_id, live_flag, sr_settings, monkeypatch):
    connection = _connection()
    builder = _builder(connection)
    monkeypatch.setattr(sr, "HubConnectionBuilder", lambda: builder)

    client = client_cls()
    client.configure()

    url = builder.with_url.call_args.args[0]
    assert url.endswith(f"/signalr/messages?access_token={getattr(sr_settings, name).apikey}")
    connection.on_open.assert_called_once_with(client.on_connect_handler)
    connection.on_reconnect.assert_called_once_with(client.on_reconnect_handler)
    connection.on_error.assert_called_once_with(client.exception_handler)
    connection.on.assert_called_once_with("receiveMessage", sr.feed_queue)


@pytest.mark.parametrize("client_cls, name, job_id, live_flag", CLIENTS)
def test_connect_marks_connected_and_syncs_when_enabled(client_cls, name, job_id, live_flag,
                                                        sr_settings, stream):
    client = client_cls()

    with mock.patch.object(sr, "scheduler") as scheduler:
        client.on_connect_handler()

    assert client.connected is True
    scheduler.execute_job_now.assert_called_once_with(taskid=job_id)
    stream.assert_called_with(type="badges")


@pytest.mark.parametrize("client_cls, name, job_id, live_flag", CLIENTS)
def test_connect_skips_sync_when_live_sync_disabled(client_cls, name, job_id, live_flag, sr_settings, stream):
    setattr(getattr(sr_settings, name), live_flag, False)
    client = client_cls()

    with mock.patch.object(sr, "scheduler") as scheduler:
        client.on_connect_handler()

    assert client.connected is True
    scheduler.execute_job_now.assert_not_called()


@pytest.mark.parametrize("client_cls, name, job_id, live_flag", CLIENTS)
def test_reconnect_marks_disconnected(client_cls, name, job_id, live_flag, sr_settings, stream):
    client = client_cls()
    client.connected = True

    client.on_reconnect_handler()

    assert client.connected is False
    stream.assert_called_with(type="badges")


@pytest.mark.parametrize("client_cls, name, job_id, live_flag", CLIENTS)
def test_exception_handler_clears_queue_and_restarts(client_cls, name, job_id, live_flag, sr_settings,
                                                     fresh_queues, stream):
    queue = getattr(fresh_queues, "sonarr" if name == "sonarr" else "radarr")
    queue.append({"name": "series"})
    client = client_cls()
    client.connected = True

    with mock.patch.object(client, "restart") as restart:
        client.exception_handler()

    assert len(queue) == 0
    assert client.connected is False
    restart.assert_called_once()


@pytest.mark.parametrize("client_cls, name, job_id, live_flag", CLIENTS)
def test_restart_stops_active_connection_then_starts(client_cls, name, job_id, live_flag, sr_settings):
    client = client_cls()
    client.connection = _connection(state=1)

    with mock.patch.object(client, "stop") as stop, mock.patch.object(client, "start") as start:
        client.restart()

    stop.assert_called_once()
    start.assert_called_once()


@pytest.mark.parametrize("client_cls, name, job_id, live_flag", CLIENTS)
def test_restart_skips_stop_when_connection_already_down(client_cls, name, job_id, live_flag, sr_settings):
    client = client_cls()
    client.connection = _connection(state=4)

    with mock.patch.object(client, "stop") as stop, mock.patch.object(client, "start") as start:
        client.restart()

    stop.assert_not_called()
    start.assert_called_once()


@pytest.mark.parametrize("client_cls, name, job_id, live_flag", CLIENTS)
def test_restart_does_not_start_when_integration_disabled(client_cls, name, job_id, live_flag, sr_settings):
    setattr(sr_settings.general, f"use_{name}", False)
    client = client_cls()
    client.connection = _connection(state=4)

    with mock.patch.object(client, "start") as start:
        client.restart()

    start.assert_not_called()


@pytest.mark.parametrize("client_cls, name, job_id, live_flag", CLIENTS)
def test_start_does_not_connect_when_signalr_disabled(client_cls, name, job_id, live_flag,
                                                      sr_settings, no_signalr, monkeypatch):
    client = client_cls()
    configure = mock.MagicMock()
    monkeypatch.setattr(client, "configure", configure)

    client.start()

    configure.assert_not_called()
    assert client.connected is False


@pytest.mark.parametrize("client_cls, name, job_id, live_flag", CLIENTS)
def test_restart_does_not_start_when_signalr_disabled(client_cls, name, job_id, live_flag,
                                                      sr_settings, no_signalr):
    client = client_cls()
    client.connection = _connection(state=4)

    with mock.patch.object(client, "start") as start:
        client.restart()

    start.assert_not_called()
    assert client.connected is False


@pytest.mark.parametrize("client_cls, name, job_id, live_flag", CLIENTS)
def test_stop_marks_client_disconnected(client_cls, name, job_id, live_flag, sr_settings):
    client = client_cls()
    client.connection = _connection()
    client.connected = True

    client.stop()

    assert client.connected is False


# Legacy Sonarr client (Sonarr v2/v3 with the old SignalR protocol)

@pytest.fixture
def legacy_connection(monkeypatch):
    connection = mock.MagicMock()
    connection.started = False
    monkeypatch.setattr(sr, "Connection", lambda url, session: connection)
    return connection


def test_legacy_start_retries_then_connects(sr_settings, legacy_connection, stream):
    attempts = []

    def start():
        attempts.append(1)
        if len(attempts) < 2:
            raise ConnectionError("down")
        legacy_connection.started = True

    legacy_connection.start.side_effect = start
    client = sr.SonarrSignalrClientLegacy()

    with mock.patch.object(sr.get_sonarr_info, "is_legacy", return_value=False), \
            mock.patch.object(sr.time, "sleep") as sleep, \
            mock.patch.object(sr, "scheduler") as scheduler:
        client.start()

    assert legacy_connection.start.call_count == 2
    sleep.assert_called_once_with(5)
    assert client.connected is True
    scheduler.execute_job_now.assert_called_once_with(taskid="update_series")


def test_legacy_start_stops_on_unparseable_json(sr_settings, legacy_connection, stream):
    legacy_connection.start.side_effect = json.decoder.JSONDecodeError("Expecting value", "doc", 0)
    client = sr.SonarrSignalrClientLegacy()

    with mock.patch.object(sr.get_sonarr_info, "is_legacy", return_value=False), \
            mock.patch.object(sr.time, "sleep") as sleep:
        client.start()

    sleep.assert_not_called()
    legacy_connection.close.assert_called_once()
    assert client.connected is False


def test_legacy_start_does_not_connect_to_legacy_sonarr(sr_settings, legacy_connection):
    client = sr.SonarrSignalrClientLegacy()

    with mock.patch.object(sr.get_sonarr_info, "is_legacy", return_value=True), \
            mock.patch.object(sr.get_sonarr_info, "version", return_value="3.0.10"):
        client.start()

    legacy_connection.start.assert_not_called()


def test_legacy_start_does_not_connect_when_signalr_disabled(sr_settings, legacy_connection, no_signalr):
    client = sr.SonarrSignalrClientLegacy()

    client.start()

    legacy_connection.start.assert_not_called()
    assert client.connected is False


def test_legacy_stop_marks_client_disconnected(sr_settings, legacy_connection):
    client = sr.SonarrSignalrClientLegacy()
    client.connection = legacy_connection
    client.connected = True

    client.stop()

    assert client.connected is False


# feed_queue and filter_nested_dict

@pytest.fixture
def series_event():
    return {"name": "series", "body": {"action": "updated", "resource": {"id": 1, "title": "Show",
                                                                          "statistics": {"episodeCount": 9}}}}


def test_feed_queue_unwraps_single_item_list(fresh_queues, series_event):
    sr.feed_queue([series_event])

    assert len(fresh_queues.sonarr) == 1


def test_feed_queue_routes_series_and_episodes_to_sonarr_and_movies_to_radarr(fresh_queues):
    sr.feed_queue({"name": "series", "body": {"resource": {"id": 1}}})
    sr.feed_queue({"name": "episode", "body": {"resource": {"id": 2}}})
    sr.feed_queue({"name": "movie", "body": {"resource": {"id": 3}}})

    assert [item["name"] for item in fresh_queues.sonarr] == ["series", "episode"]
    assert [item["name"] for item in fresh_queues.radarr] == ["movie"]


def test_feed_queue_ignores_unknown_topics(fresh_queues):
    sr.feed_queue({"name": "health", "body": {}})

    assert len(fresh_queues.sonarr) == 0
    assert len(fresh_queues.radarr) == 0


def test_feed_queue_drops_consecutive_duplicates(fresh_queues):
    event = {"name": "movie", "body": {"resource": {"id": 3}}}

    sr.feed_queue(event)
    sr.feed_queue(dict(event))
    sr.feed_queue({"name": "movie", "body": {"resource": {"id": 4}}})

    assert len(fresh_queues.radarr) == 2


def test_feed_queue_strips_statistics_before_queueing(fresh_queues, series_event):
    sr.feed_queue(series_event)

    queued = fresh_queues.sonarr[0]
    assert "statistics" not in queued["body"]["resource"]


def test_filter_nested_dict_removes_statistics_at_every_level():
    data = {
        "statistics": {"x": 1},
        "keep": 1,
        "nested": {"statistics": {"y": 2}, "value": 3},
        "items": [{"statistics": {"z": 4}, "id": 5}, 6],
    }

    assert sr.filter_nested_dict(data) == {
        "keep": 1,
        "nested": {"value": 3},
        "items": [{"id": 5}, 6],
    }


# dispatcher

@pytest.fixture
def dispatch(sr_settings, stream, monkeypatch):
    database = mock.MagicMock()
    database.execute.return_value.first.return_value = None
    monkeypatch.setattr(sr, "database", database)
    calls = SimpleNamespace(
        sync_episodes=mock.MagicMock(), update_one_series=mock.MagicMock(),
        sync_one_episode=mock.MagicMock(), update_one_movie=mock.MagicMock(), database=database,
    )
    monkeypatch.setattr(sr, "sync_episodes", calls.sync_episodes)
    monkeypatch.setattr(sr, "update_one_series", calls.update_one_series)
    monkeypatch.setattr(sr, "sync_one_episode", calls.sync_one_episode)
    monkeypatch.setattr(sr, "update_one_movie", calls.update_one_movie)
    return calls


def test_dispatch_series_with_episode_changes_resyncs_episodes(dispatch):
    sr.dispatcher({"name": "series", "body": {"action": "updated", "resource": {
        "id": 5, "title": "Show", "year": 2020, "episodesChanged": True}}})

    dispatch.sync_episodes.assert_called_once_with(series_id=5, defer_search=False, is_signalr=True)
    dispatch.update_one_series.assert_not_called()


def test_dispatch_series_update_refreshes_single_series(dispatch):
    sr.dispatcher({"name": "series", "body": {"action": "updated", "resource": {
        "id": 5, "title": "Show", "year": 2020}}})

    dispatch.update_one_series.assert_called_once_with(series_id=5, action="updated", is_signalr=True)
    dispatch.sync_episodes.assert_not_called()


def test_dispatch_episode_with_embedded_series_syncs_episode(dispatch):
    sr.dispatcher({"name": "episode", "body": {"action": "updated", "resource": {
        "id": 9, "title": "Pilot", "seasonNumber": 1, "episodeNumber": 2,
        "series": {"title": "Show", "year": 2020}}}})

    dispatch.sync_one_episode.assert_called_once_with(episode_id=9, defer_search=False, is_signalr=True)
    dispatch.database.execute.assert_not_called()


def test_dispatch_episode_without_embedded_series_looks_up_series(dispatch):
    dispatch.database.execute.return_value.first.return_value = SimpleNamespace(title="Show", year=2020)

    sr.dispatcher({"name": "episode", "body": {"action": "updated", "resource": {
        "id": 9, "title": "Pilot", "seasonNumber": 1, "episodeNumber": 2, "seriesId": 5}}})

    dispatch.database.execute.assert_called_once()
    dispatch.sync_one_episode.assert_called_once_with(episode_id=9, defer_search=False, is_signalr=True)


def test_dispatch_movie_added_updates_movie(dispatch):
    sr.dispatcher({"name": "movie", "body": {"action": "added", "resource": {
        "id": 7, "title": "Film", "year": 2021}}})

    dispatch.update_one_movie.assert_called_once_with(movie_id=7, action="added", defer_search=False,
                                                      is_signalr=True)


def test_dispatch_deleted_movie_unknown_to_bazarr_is_ignored(dispatch):
    sr.dispatcher({"name": "movie", "body": {"action": "deleted", "resource": {"id": 7}}})

    dispatch.update_one_movie.assert_not_called()


def test_dispatch_deleted_movie_known_to_bazarr_is_processed(dispatch):
    dispatch.database.execute.return_value.first.return_value = SimpleNamespace(title="Film", year=2021)

    sr.dispatcher({"name": "movie", "body": {"action": "deleted", "resource": {"id": 7}}})

    dispatch.update_one_movie.assert_called_once_with(movie_id=7, action="deleted", defer_search=False,
                                                      is_signalr=True)


def test_dispatch_ignores_malformed_payload(dispatch):
    sr.dispatcher({"name": "series"})

    dispatch.update_one_series.assert_not_called()
    dispatch.sync_episodes.assert_not_called()


def test_dispatch_ignores_unknown_topic(dispatch, stream):
    sr.dispatcher({"name": "health", "body": {"action": "updated", "resource": {"id": 1}}})

    dispatch.update_one_series.assert_not_called()
    dispatch.update_one_movie.assert_not_called()
    stream.assert_called_with(type="badges")
