# -*- coding: utf-8 -*-
"""
Tests for root folder sync and accessibility checks in sonarr/rootfolder.py and
radarr/rootfolder.py. Both modules share the same logic, so each test runs for both.

The modules use the global app.database session. Each test swaps it for an in-memory
SQLite session with the real table definitions.
"""
import importlib
from types import SimpleNamespace
from unittest import mock

import pytest
import requests
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import (TableMovies, TableMoviesRootfolder, TableShows, TableShowsRootfolder,
                          metadata)


class _Section(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as e:
            raise AttributeError(name) from e


@pytest.fixture
def db():
    engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    metadata.create_all(engine)
    session = Session(bind=engine)
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def arr(request, db):
    arr_name = request.param
    module = importlib.import_module(f"{arr_name}.rootfolder")
    is_sonarr = arr_name == "sonarr"
    series_model = TableShows if is_sonarr else TableMovies
    rootfolder_model = TableShowsRootfolder if is_sonarr else TableMoviesRootfolder
    settings = SimpleNamespace(**{arr_name: _Section(apikey="key", http_timeout=5)})
    path_mappings = mock.MagicMock(path_replace=lambda p: p, path_replace_movie=lambda p: p)

    with mock.patch.object(module, "database", db), \
            mock.patch.object(module, "settings", settings), \
            mock.patch.object(module, "path_mappings", path_mappings), \
            mock.patch.object(module, f"url_api_{arr_name}", return_value=f"http://{arr_name}/api/v3/"), \
            mock.patch.object(module.requests, "get") as get:

        def add_series(path, number):
            if is_sonarr:
                db.add(series_model(path=path, sonarrSeriesId=number, title="Show"))
            else:
                db.add(series_model(path=path, radarrId=number, title="Movie", tmdbId=str(number)))
            db.commit()

        def add_rootfolder(number, path, accessible=None, error=None):
            db.add(rootfolder_model(id=number, path=path, accessible=accessible, error=error))
            db.commit()

        def set_api_folders(folders):
            get.return_value.json.return_value = folders

        yield SimpleNamespace(
            name=arr_name,
            fetch=getattr(module, f"get_{arr_name}_rootfolder"),
            check=getattr(module, f"check_{arr_name}_rootfolder"),
            get=get,
            db=db,
            rootfolder_model=rootfolder_model,
            add_series=add_series,
            add_rootfolder=add_rootfolder,
            set_api_folders=set_api_folders,
        )


def _rootfolders(arr):
    rows = arr.db.execute(select(arr.rootfolder_model.id, arr.rootfolder_model.path)).all()
    return sorted((row.id, row.path) for row in rows)


def _status(arr):
    rows = arr.db.execute(
        select(arr.rootfolder_model.id, arr.rootfolder_model.accessible, arr.rootfolder_model.error)
    ).all()
    return {row.id: (row.accessible, row.error) for row in rows}


ARRS = pytest.mark.parametrize("arr", ["sonarr", "radarr"], indirect=True)


@ARRS
def test_fetch_leaves_database_untouched_on_connection_error(arr):
    arr.add_rootfolder(5, "/keep/")
    arr.get.side_effect = requests.exceptions.ConnectionError("down")

    assert arr.fetch() == []
    assert _rootfolders(arr) == [(5, "/keep/")]


@ARRS
def test_fetch_inserts_only_folders_that_contain_media(arr):
    arr.add_series("/data/a/show", 1)
    arr.set_api_folders([{"id": 1, "path": "/data/a/"}, {"id": 2, "path": "/data/empty/"}])

    arr.fetch()

    assert _rootfolders(arr) == [(1, "/data/a/")]


@ARRS
def test_fetch_updates_changed_paths_and_removes_stale_rows(arr):
    arr.add_rootfolder(1, "/old/")
    arr.add_rootfolder(9, "/gone/")
    arr.add_series("/data/a/show", 1)
    arr.set_api_folders([{"id": 1, "path": "/data/a/"}])

    arr.fetch()

    assert _rootfolders(arr) == [(1, "/data/a/")]


@ARRS
def test_check_flags_missing_directory_as_inaccessible(arr, tmp_path):
    root = tmp_path / "missing"
    arr.add_series(str(root / "show"), 1)
    arr.set_api_folders([{"id": 1, "path": str(root)}])

    arr.check()

    accessible, error = _status(arr)[1]
    assert accessible == 0
    assert "does not seem to be accessible by Bazarr" in error


@ARRS
def test_check_marks_writable_directory_accessible(arr, tmp_path):
    arr.add_series(str(tmp_path / "show"), 1)
    arr.set_api_folders([{"id": 1, "path": str(tmp_path)}])

    arr.check()

    assert _status(arr)[1] == (1, "")


@ARRS
def test_check_falls_back_to_write_test_when_access_check_fails(arr, tmp_path):
    arr.add_series(str(tmp_path / "show"), 1)
    arr.set_api_folders([{"id": 1, "path": str(tmp_path)}])

    with mock.patch("os.access", return_value=False):
        arr.check()

    assert _status(arr)[1] == (1, "")
    assert not (tmp_path / ".bazarr_write_test").exists()


@ARRS
def test_check_records_write_test_failure(arr, tmp_path):
    arr.add_series(str(tmp_path / "show"), 1)
    arr.set_api_folders([{"id": 1, "path": str(tmp_path)}])

    module = importlib.import_module(f"{arr.name}.rootfolder")
    with mock.patch("os.access", return_value=False), \
            mock.patch.object(module, "open", side_effect=PermissionError("denied"), create=True):
        arr.check()

    accessible, error = _status(arr)[1]
    assert accessible == 0
    assert "There's an issue with this" in error
    assert "PermissionError('denied')" in error
