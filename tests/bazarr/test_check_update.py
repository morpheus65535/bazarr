# -*- coding: utf-8 -*-
"""
Tests for the release checker and updater in app/check_update.py.

GitHub is mocked, every path is redirected into a temporary config directory, and
update_cleaner is only ever given a temporary install tree. apply_update is never called
because it extracts into the repository and restarts the webserver.
"""
import json
import os
from types import SimpleNamespace
from unittest import mock
from zipfile import ZipFile

import pytest
import requests

from app import check_update as cu

# The env fixture replaces cu.download_release, so keep the real function for the download test
real_download_release = cu.download_release


class _Section(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as e:
            raise AttributeError(name) from e


def _release(name, prerelease=False, link=None):
    return {
        "name": name,
        "body": "",
        "published_at": "2026-01-01T00:00:00Z",
        "prerelease": prerelease,
        "assets": [{"name": "bazarr.zip", "browser_download_url": link or f"https://example.test/{name}.zip"}],
    }


def _response(payload=None, content=b""):
    response = mock.Mock(content=content)
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    return response


@pytest.fixture
def env(tmp_path, monkeypatch):
    (tmp_path / "config").mkdir()
    monkeypatch.setattr(cu.args, "config_dir", str(tmp_path))
    monkeypatch.setattr(cu.args, "no_update", False)
    monkeypatch.setattr(cu, "settings", SimpleNamespace(general=_Section(branch="master")))
    monkeypatch.setenv("BAZARR_VERSION", "1.0.0")
    monkeypatch.setattr(cu, "deprecated_python_version", lambda: False)
    with mock.patch.object(cu, "download_release") as download:
        yield SimpleNamespace(root=tmp_path, download=download, settings=cu.settings, monkeypatch=monkeypatch)


def _serve_releases(releases):
    return mock.patch.object(cu.requests, "get", return_value=_response(releases))


# check_releases

def test_check_releases_keeps_only_releases_with_zip_asset(env):
    releases = [_release("v1.2.0"), {**_release("v1.1.0"), "assets": []}]

    with _serve_releases(releases):
        cu.check_releases(startup=True)

    saved = json.loads((env.root / "config" / "releases.txt").read_text())
    assert [item["name"] for item in saved] == ["v1.2.0"]
    assert saved[0]["download_link"] == "https://example.test/v1.2.0.zip"
    assert saved[0]["prerelease"] is False


def test_check_releases_network_error_keeps_previous_file(env):
    releases_file = env.root / "config" / "releases.txt"
    releases_file.write_text("[]")

    with mock.patch.object(cu.requests, "get", side_effect=requests.exceptions.ConnectionError("down")):
        cu.check_releases(startup=True)

    assert releases_file.read_text() == "[]"


# check_if_new_update

def test_master_branch_ignores_prereleases(env):
    releases = [_release("v2.0.0-beta", prerelease=True, link="beta-link"),
                _release("v1.5.0", link="stable-link")]

    with _serve_releases(releases):
        cu.check_if_new_update()

    env.download.assert_called_once_with(url="stable-link")


def test_development_branch_takes_newest_release_including_prereleases(env):
    env.settings.general["branch"] = "development"
    releases = [_release("v2.0.0-beta", prerelease=True, link="beta-link"),
                _release("v1.5.0", link="stable-link")]

    with _serve_releases(releases):
        cu.check_if_new_update()

    env.download.assert_called_once_with(url="beta-link")


def test_stable_install_upgrades_to_newer_stable(env):
    with _serve_releases([_release("v1.5.0", link="stable-link")]):
        cu.check_if_new_update()

    env.download.assert_called_once_with(url="stable-link")


def test_up_to_date_install_downloads_nothing(env):
    env.monkeypatch.setenv("BAZARR_VERSION", "1.5.0")

    with _serve_releases([_release("v1.5.0")]):
        cu.check_if_new_update()

    env.download.assert_not_called()


def test_prerelease_install_rolls_back_to_stable_on_master(env):
    env.monkeypatch.setenv("BAZARR_VERSION", "2.0.0-beta")

    with _serve_releases([_release("v1.5.0", link="stable-link")]):
        cu.check_if_new_update()

    env.download.assert_called_once_with(url="stable-link")


def test_no_update_argument_disables_download(env):
    env.monkeypatch.setattr(cu.args, "no_update", True)

    with _serve_releases([_release("v1.5.0")]):
        cu.check_if_new_update()

    env.download.assert_not_called()


def test_unknown_branch_stops_before_contacting_github(env):
    env.settings.general["branch"] = "experimental"

    with mock.patch.object(cu.requests, "get") as get:
        cu.check_if_new_update()

    get.assert_not_called()
    env.download.assert_not_called()


@pytest.mark.xfail(
    strict=True,
    reason="On Python older than 3.10, check_if_new_update's stable branch calls next(...) without "
           "assigning the result to `release`, and its generator only accepts releases older than 1.3.1. "
           "A current stable release therefore raises StopIteration instead of being offered. Found while "
           "writing these tests.",
)
def test_deprecated_python_offers_stable_release(env, monkeypatch):
    monkeypatch.setattr(cu, "deprecated_python_version", lambda: True)

    with _serve_releases([_release("v1.5.0", link="stable-link")]):
        cu.check_if_new_update()

    env.download.assert_called_once_with(url="stable-link")


# download_release

def test_download_release_saves_zip_then_applies(env, monkeypatch):
    apply = mock.MagicMock()
    monkeypatch.setattr(cu, "apply_update", apply)

    with mock.patch.object(cu.requests, "get", return_value=_response(content=b"zipbytes")) as get:
        real_download_release(url="https://example.test/release.zip")

    get.assert_called_once()
    assert (env.root / "update" / "bazarr.zip").read_bytes() == b"zipbytes"
    apply.assert_called_once()


# update_cleaner

@pytest.fixture
def install_tree(tmp_path):
    install = tmp_path / "install"
    config = tmp_path / "config"
    files = {
        "bazarr.py": "new",
        "stale.py": "old",
        "notes.pyc": "compiled",
        "nssm.exe": "service",
        "venv/lib.py": "venv",
        "frontend/build/index.html": "new",
        "frontend/build/old.js": "old",
    }
    for name, content in files.items():
        path = install / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    config.mkdir()

    release = tmp_path / "bazarr.zip"
    with ZipFile(release, "w") as archive:
        archive.writestr("bazarr.py", "new")
        archive.writestr("frontend/", "")
        archive.writestr("frontend/build/", "")
        archive.writestr("frontend/build/index.html", "new")
    return SimpleNamespace(install=install, config=config, release=release)


def test_update_cleaner_removes_only_files_missing_from_release(install_tree):
    cu.update_cleaner(zipfile=str(install_tree.release), bazarr_dir=str(install_tree.install),
                      config_dir=str(install_tree.config))

    install = install_tree.install
    assert (install / "bazarr.py").exists()
    assert (install / "frontend" / "build" / "index.html").exists()
    assert not (install / "stale.py").exists()
    assert not (install / "frontend" / "build" / "old.js").exists()


def test_update_cleaner_keeps_ignored_files_and_directories(install_tree):
    cu.update_cleaner(zipfile=str(install_tree.release), bazarr_dir=str(install_tree.install),
                      config_dir=str(install_tree.config))

    install = install_tree.install
    assert (install / "notes.pyc").exists()
    assert (install / "nssm.exe").exists()
    assert (install / "venv" / "lib.py").exists()
