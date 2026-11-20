import base64
import json
import stat
import sys
import textwrap
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Event, Thread, Timer

import pytest

from subtitles import sync as sync_module
from subtitles.tools import lapse as lapse_module
from subtitles.tools.lapse import LapseSyncer, check_lapse

SOLID = {"mode": "auto/shifted", "offset_ms": -4200, "ratio": 1, "sigma": 17.4, "verdict": "solid", "parts": 1,
         "written": True}


def _fake_lapse(tmp_path, returncode=0, result=None, body=""):
    exe = tmp_path / "lapse"
    exe.write_text(f"#!{sys.executable}\n" + textwrap.dedent(f"""
        import json, sys
        args = sys.argv[1:]
        open({str(tmp_path / 'args.json')!r}, 'w').write(json.dumps(args))
        result = {result!r}
        if result and result['written']:
            open(args[args.index('--output') + 1], 'w').write('synced')
    """) + textwrap.dedent(body) + textwrap.dedent(f"""
        if result:
            print(json.dumps(result))
        sys.exit({returncode})
    """))
    exe.chmod(exe.stat().st_mode | stat.S_IEXEC)
    return str(exe)


@pytest.fixture
def subtitle(tmp_path):
    srt = tmp_path / "movie.en.srt"
    srt.write_text("original")
    return srt


@pytest.fixture
def history(monkeypatch):
    calls = []
    monkeypatch.setattr(lapse_module, "history_log_movie", lambda **kwargs: calls.append(kwargs))
    return calls


def _sync(subtitle, **kwargs):
    LapseSyncer().sync(video_path="/movies/movie.mkv", srt_path=str(subtitle), srt_lang="en", hi=False,
                       forced=False, radarr_id=1, **kwargs)


def _args(tmp_path):
    return json.loads((tmp_path / "args.json").read_text())


def test_solid_result_replaces_subtitles_and_logs_history(tmp_path, monkeypatch, subtitle, history):
    monkeypatch.setattr(lapse_module.settings.subsync, "lapse_path", _fake_lapse(tmp_path, 0, SOLID))

    _sync(subtitle)

    assert subtitle.read_text() == "synced"
    assert not (tmp_path / "movie.en.synced.srt").exists()
    assert _args(tmp_path) == ["/movies/movie.mkv", str(subtitle), "--output", str(tmp_path / "movie.en.synced.srt"),
                               "--no-backup", "--no-sidecar", "--json"]
    assert history[0]["result"].message == ("English subtitles synchronization ended with an offset of -4.2 seconds "
                                            "and a framerate scale factor of 1.00.")


@pytest.mark.parametrize("reference,force_audio,original_stream,force_sync,expected", [
    ("a:1", False, None, False, ["--no-embedded", "--audio-track", "1"]),
    ("s:2", False, None, False, ["--sub-track", "2"]),
    ("a:0", False, None, False, ["--no-embedded", "--audio-track", "0"]),
    ("s:0", False, None, False, ["--sub-track", "0"]),
    (None, True, None, False, ["--no-embedded"]),
    (None, True, None, True, ["--json"]),
    (None, True, "a:1", False, ["--no-embedded", "--audio-track", "1"]),
    (None, False, "a:2", True, ["--no-embedded", "--audio-track", "2"]),
])
def test_tracks_are_passed_to_lapse(tmp_path, monkeypatch, subtitle, history, reference, force_audio, original_stream,
                                    force_sync, expected):
    monkeypatch.setattr(lapse_module.settings.subsync, "lapse_path", _fake_lapse(tmp_path, 0, SOLID))
    monkeypatch.setattr(lapse_module.settings.subsync, "force_audio", force_audio)
    monkeypatch.setattr(lapse_module.settings.subsync, "use_original_language", bool(original_stream))
    monkeypatch.setattr(lapse_module.settings.subsync, "auto_use_original_language", False)
    monkeypatch.setattr(LapseSyncer, "_audio_stream_for_original_language",
                        classmethod(lambda cls, **kwargs: original_stream))

    _sync(subtitle, reference=reference, force_sync=force_sync)

    assert _args(tmp_path)[-len(expected):] == expected


def test_subtitles_file_reference_replaces_video(tmp_path, monkeypatch, subtitle, history):
    monkeypatch.setattr(lapse_module.settings.subsync, "lapse_path", _fake_lapse(tmp_path, 0, SOLID))
    reference = tmp_path / "movie.da.srt"
    reference.write_text("reference")

    _sync(subtitle, reference=str(reference))

    assert _args(tmp_path)[:2] == [str(reference), str(subtitle)]


@pytest.mark.parametrize("returncode,result,logged", [
    (3, {**SOLID, "verdict": "unsure", "written": False, "why": "not sure"}, "unsure: not sure"),
    (2, {**SOLID, "verdict": "nothing", "written": False, "why": "only 3 cues"}, "nothing: only 3 cues"),
    (1, None, "boom"),
])
def test_unsuccessful_run_leaves_subtitles_untouched(tmp_path, monkeypatch, subtitle, history, caplog, returncode,
                                                     result, logged):
    monkeypatch.setattr(lapse_module.settings.subsync, "lapse_path",
                        _fake_lapse(tmp_path, returncode, result, "print('boom', file=sys.stderr)"))

    _sync(subtitle)

    assert logged in caplog.text
    assert subtitle.read_text() == "original"
    assert not (tmp_path / "movie.en.synced.srt").exists()
    assert history == []


@pytest.mark.parametrize("name", ["missing", "not-executable"])
def test_missing_executable_falls_back_to_ffsubsync(tmp_path, monkeypatch, subtitle, history, caplog, name):
    (tmp_path / "not-executable").write_text("")
    monkeypatch.setattr(lapse_module.settings.subsync, "lapse_path", str(tmp_path / name))
    calls = []
    monkeypatch.setattr(lapse_module.SubSyncer, "sync", lambda self, **kwargs: calls.append(kwargs))

    _sync(subtitle, max_offset_seconds="60", job_id=7)

    assert "executable not found" in caplog.text
    assert calls[0]["srt_path"] == str(subtitle)
    assert calls[0]["max_offset_seconds"] == "60"
    assert calls[0]["job_id"] == 7


@pytest.mark.parametrize("user_cache,expected", [
    (None, lambda tmp_path: str(tmp_path / "config" / "cache" / "lapse")),
    ("/elsewhere", lambda tmp_path: "/elsewhere"),
])
def test_cache_goes_to_the_config_folder_unless_set(tmp_path, monkeypatch, subtitle, history, user_cache, expected):
    monkeypatch.setattr(lapse_module.args, "config_dir", str(tmp_path / "config"))
    if user_cache:
        monkeypatch.setenv("LAPSE_CACHE", user_cache)
    else:
        monkeypatch.delenv("LAPSE_CACHE", raising=False)
    monkeypatch.setattr(lapse_module.settings.subsync, "lapse_path", _fake_lapse(tmp_path, 0, SOLID, f"""
        import os
        assert os.environ['LAPSE_CACHE'] == {expected(tmp_path)!r}
    """))

    _sync(subtitle)

    assert subtitle.read_text() == "synced"


def test_progress_is_passed_to_the_job(tmp_path, monkeypatch, subtitle, history):
    monkeypatch.setattr(lapse_module.settings.subsync, "lapse_path", _fake_lapse(tmp_path, 0, SOLID, """
        import os
        assert os.environ['LAPSE_PROGRESS'] == '1'
        print('Listening to the audio 40%', file=sys.stderr)
    """))
    updates = []
    monkeypatch.setattr(lapse_module.jobs_queue, "update_job_progress", lambda **kwargs: updates.append(kwargs))

    _sync(subtitle, job_id=7)

    assert updates == [
        {"job_id": 7, "progress_value": 40, "progress_max": 100, "progress_message": "Listening to the audio"}]


def test_timeout_kills_lapse(tmp_path, monkeypatch, subtitle, history, caplog):
    monkeypatch.setattr(lapse_module.settings.subsync, "lapse_path",
                        _fake_lapse(tmp_path, 0, SOLID, "import time\ntime.sleep(60)\n"))
    monkeypatch.setattr(lapse_module, "LAPSE_TIMEOUT", 0)

    started = time.monotonic()
    _sync(subtitle)

    assert time.monotonic() - started < 10
    assert "did not finish" in caplog.text
    assert subtitle.read_text() == "original"


def _cancel_in_a_second(monkeypatch):
    cancel_event = Event()
    job = type("FakeJob", (), {"cancel_event": cancel_event})()
    monkeypatch.setattr(lapse_module.jobs_queue, "get_job", lambda job_id: job if job_id == 7 else None)
    Timer(1, cancel_event.set).start()


def test_canceled_job_kills_lapse(tmp_path, monkeypatch, subtitle, history):
    monkeypatch.setattr(lapse_module.settings.subsync, "lapse_path",
                        _fake_lapse(tmp_path, 0, SOLID, "import time\ntime.sleep(60)\n"))
    _cancel_in_a_second(monkeypatch)

    started = time.monotonic()
    with pytest.raises(lapse_module.JobCanceled):
        _sync(subtitle, job_id=7)

    assert time.monotonic() - started < 10
    assert subtitle.read_text() == "original"
    assert not (tmp_path / "movie.en.synced.srt").exists()


def test_engine_setting_selects_lapse(monkeypatch):
    monkeypatch.setattr(sync_module.settings.subsync, "engine", "lapse")

    assert isinstance(sync_module._create_subsyncer(), LapseSyncer)


class FakeLapseHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_GET(self):
        self._reply(200, {"version": "2.5.1"})

    def do_POST(self):
        self.server.posted.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
        if self.server.status != 200:
            return self._reply(self.server.status, {"error": "nope"})
        self.send_response(200)
        self.send_header("Transfer-Encoding", "chunked")
        self.end_headers()
        try:
            for line in self.server.lines:
                self._chunk(json.dumps(line).encode() + b"\n")
            while self.server.heartbeat:
                self._chunk(b"\n")
                time.sleep(0.1)
            self._chunk(b"")
        except OSError:
            self.server.hung_up.set()

    def _chunk(self, data):
        self.wfile.write(b"%x\r\n%s\r\n" % (len(data), data))
        self.wfile.flush()

    def _reply(self, status, body):
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


@pytest.fixture
def server(monkeypatch):
    server = ThreadingHTTPServer(("127.0.0.1", 0), FakeLapseHandler)
    server.handle_error = lambda *args: None  # the cancel test hangs up on purpose
    server.daemon_threads = True
    server.posted, server.lines, server.status = [], [], 200
    server.heartbeat, server.hung_up = False, Event()
    Thread(target=server.serve_forever, daemon=True).start()
    monkeypatch.setattr(lapse_module.settings.subsync, "lapse_url", f"http://127.0.0.1:{server.server_port}/")
    yield server
    server.shutdown()


def _done(result=SOLID, subtitle="synced"):
    return {"done": result, "subtitle": base64.b64encode(subtitle.encode()).decode() if subtitle else None}


def test_remote_solid_result_replaces_subtitles(tmp_path, monkeypatch, subtitle, history, server):
    # the url wins over a binary that is also set
    monkeypatch.setattr(lapse_module.settings.subsync, "lapse_path", _fake_lapse(tmp_path, 0, SOLID))
    server.lines = [{"progress": 40, "phase": "Listening to the audio"}, _done()]
    updates = []
    monkeypatch.setattr(lapse_module.jobs_queue, "update_job_progress", lambda **kwargs: updates.append(kwargs))

    _sync(subtitle, job_id=7)

    assert subtitle.read_text() == "synced"
    assert not (tmp_path / "args.json").exists()
    assert server.posted == [{"video": "/movies/movie.mkv", "subtitle": base64.b64encode(b"original").decode(),
                              "filename": "movie.en.srt", "reference": None, "reference_filename": None,
                              "no_embedded": False, "audio_track": None, "sub_track": None}]
    assert updates == [
        {"job_id": 7, "progress_value": 40, "progress_max": 100, "progress_message": "Listening to the audio"}]
    assert history[0]["result"].message.startswith("English subtitles synchronization ended with an offset of -4.2")


def test_remote_gets_tracks_and_reference_subtitles(tmp_path, subtitle, history, server):
    server.lines = [_done()]
    reference = tmp_path / "movie.da.srt"
    reference.write_text("reference")

    _sync(subtitle, reference="a:1")
    _sync(subtitle, reference=str(reference))

    assert (server.posted[0]["audio_track"], server.posted[0]["no_embedded"]) == (1, True)
    assert server.posted[1]["video"] is None
    assert server.posted[1]["reference"] == base64.b64encode(b"reference").decode()
    assert server.posted[1]["reference_filename"] == "movie.da.srt"


def test_remote_unsure_verdict_is_never_written(subtitle, history, server, caplog):
    server.lines = [_done({**SOLID, "verdict": "unsure", "why": "not sure"}, "synced")]

    _sync(subtitle)

    assert "unsure: not sure" in caplog.text
    assert subtitle.read_text() == "original"
    assert history == []


@pytest.mark.parametrize("status,lines,logged", [
    (404, [], "same path as in Bazarr"),
    (400, [], "nope"),
    (200, [{"error": "audio track 9 does not exist"}], "audio track 9 does not exist"),
    (200, [{"progress": 10, "phase": "Listening"}], "closed before it sent a result"),
])
def test_remote_errors_are_logged(subtitle, history, server, caplog, status, lines, logged):
    server.status, server.lines = status, lines

    _sync(subtitle)

    assert logged in caplog.text
    assert subtitle.read_text() == "original"


def test_unreachable_server_falls_back_to_ffsubsync(monkeypatch, subtitle, history, caplog):
    monkeypatch.setattr(lapse_module.settings.subsync, "lapse_url", "http://127.0.0.1:1")
    calls = []
    monkeypatch.setattr(lapse_module.SubSyncer, "sync", lambda self, **kwargs: calls.append(kwargs))

    _sync(subtitle, gss=True, job_id=7)

    assert "not available" in caplog.text
    assert calls[0]["gss"] is True
    assert calls[0]["job_id"] == 7


def test_canceled_job_hangs_up_on_the_server(monkeypatch, subtitle, history, server):
    server.heartbeat = True
    _cancel_in_a_second(monkeypatch)

    with pytest.raises(lapse_module.JobCanceled):
        _sync(subtitle, job_id=7)

    assert server.hung_up.wait(3)
    assert subtitle.read_text() == "original"


def test_check_lapse_reads_the_version(tmp_path, server):
    assert check_lapse(url=lapse_module.settings.subsync.lapse_url, path="") == "2.5.1"

    exe = tmp_path / "lapse"
    exe.write_text(f"#!{sys.executable}\nprint('2.5.0')\n")
    exe.chmod(exe.stat().st_mode | stat.S_IEXEC)
    assert check_lapse(url="", path=str(exe)) == "2.5.0"
    with pytest.raises(RuntimeError, match="not found"):
        check_lapse(url="", path=str(tmp_path / "missing"))
