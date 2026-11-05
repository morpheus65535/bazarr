# -*- coding: utf-8 -*-
"""
Tests for the process-control helpers in utilities/central.py.

os._exit is patched to raise, so the tests can check the exit code without ending the
test process.
"""
import logging
import os
from unittest import mock

import pytest

from literals import DIR_LOG, ENV_BAZARR_ROOT_DIR, ENV_RESTARTFILE, ENV_STOPFILE, EXIT_NORMAL, FILE_LOG
from utilities import central


class _Exited(Exception):
    pass


@pytest.fixture
def root(tmp_path, monkeypatch):
    monkeypatch.setenv(ENV_BAZARR_ROOT_DIR, str(tmp_path))
    monkeypatch.setenv(ENV_STOPFILE, str(tmp_path / "stop.txt"))
    monkeypatch.setenv(ENV_RESTARTFILE, str(tmp_path / "restart.txt"))
    return tmp_path


@pytest.fixture
def exit_call():
    with mock.patch.object(central.os, "_exit", side_effect=_Exited) as exit_:
        yield exit_


def test_get_bazarr_dir_joins_root_and_subdirectory(root):
    assert central.get_bazarr_dir("data") == os.path.join(str(root), "data")


def test_make_bazarr_dir_creates_directory_once(root):
    central.make_bazarr_dir("cache")
    central.make_bazarr_dir("cache")

    assert (root / "cache").is_dir()


def test_log_file_path_points_into_log_directory(root):
    assert central.get_log_file_path() == os.path.join(str(root), DIR_LOG, FILE_LOG)


def test_stop_and_restart_paths_come_from_environment(root):
    assert central.get_stop_file_path() == str(root / "stop.txt")
    assert central.get_restart_file_path() == str(root / "restart.txt")


def test_stop_bazarr_writes_status_code_and_exits(root, exit_call):
    with pytest.raises(_Exited):
        central.stop_bazarr(status_code=3)

    assert (root / "stop.txt").read_text() == "3\n"
    exit_call.assert_called_once_with(3)


def test_stop_bazarr_defaults_to_normal_exit(root, exit_call):
    with pytest.raises(_Exited):
        central.stop_bazarr()

    assert (root / "stop.txt").read_text() == f"{EXIT_NORMAL}\n"
    exit_call.assert_called_once_with(EXIT_NORMAL)


def test_stop_bazarr_still_exits_when_stop_file_cannot_be_written(root, exit_call, monkeypatch, caplog):
    monkeypatch.setenv(ENV_STOPFILE, str(root / "missing" / "stop.txt"))

    with caplog.at_level(logging.ERROR), pytest.raises(_Exited):
        central.stop_bazarr()

    assert "Cannot create stop file" in caplog.text
    exit_call.assert_called_once_with(EXIT_NORMAL)


def test_restart_bazarr_touches_restart_file_and_exits_normally(root, exit_call):
    with pytest.raises(_Exited):
        central.restart_bazarr()

    assert (root / "restart.txt").exists()
    exit_call.assert_called_once_with(EXIT_NORMAL)


def test_restart_bazarr_still_exits_when_restart_file_cannot_be_written(root, exit_call, monkeypatch, caplog):
    monkeypatch.setenv(ENV_RESTARTFILE, str(root / "missing" / "restart.txt"))

    with caplog.at_level(logging.ERROR), pytest.raises(_Exited):
        central.restart_bazarr()

    assert "Cannot create restart file" in caplog.text
    exit_call.assert_called_once_with(EXIT_NORMAL)
