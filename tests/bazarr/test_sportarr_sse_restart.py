import time
from threading import Event, Thread


def test_restart_returns_without_waiting_for_the_event_stream(monkeypatch):
    from sportarr import sse_client

    client = sse_client.SportarrSSEClient()
    monkeypatch.setattr(sse_client.settings.general, 'use_sportarr', True)
    monkeypatch.setattr(client, 'start', lambda: time.sleep(0.5))

    started = time.monotonic()
    client.restart()

    assert time.monotonic() - started < 0.2


def test_restart_stops_the_previous_stream(monkeypatch):
    from sportarr import sse_client

    client = sse_client.SportarrSSEClient()
    monkeypatch.setattr(sse_client.settings.general, 'use_sportarr', True)
    first_started = Event()
    second_started = Event()
    runs = []

    def fake_connect(stop_event):
        runs.append(stop_event)
        (first_started if len(runs) == 1 else second_started).set()
        stop_event.wait(1)

    monkeypatch.setattr(client, 'connect', fake_connect)
    initial = Thread(target=client.start, daemon=True)
    initial.start()
    assert first_started.wait(1)

    client.restart()

    assert second_started.wait(1)
    assert runs[0].is_set()
    client.stop()
    initial.join(1)
    assert not initial.is_alive()


def test_restart_drops_the_previous_server_cursor(monkeypatch):
    from sportarr import sse_client

    client = sse_client.SportarrSSEClient()
    client.last_event_id = '400'
    monkeypatch.setattr(sse_client.settings.general, 'use_sportarr', False)

    client.restart()

    assert client.last_event_id is None


def test_stop_shuts_down_the_stream_before_closing_it():
    from sportarr import sse_client

    calls = []

    class Raw:
        def shutdown(self):
            calls.append('shutdown')

    class Response:
        raw = Raw()

        def close(self):
            calls.append('close')

    client = sse_client.SportarrSSEClient()
    client._response = Response()

    client.stop()

    assert calls == ['shutdown', 'close']
