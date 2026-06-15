# -*- coding: utf-8 -*-
import os
import pkgutil
from importlib.metadata import distributions
from pathlib import Path

import pytest

os.environ.setdefault("BAZARR_VERSION", "v0.0.0-test")
os.environ.setdefault("SZ_USER_AGENT", "pytest")

# Reuse Bazarr's normal import bootstrap instead of maintaining a test-only
# sys.path setup in parallel.
import bazarr.app.libs  # noqa: F401

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import Session

PROJECT_ROOT = Path(__file__).resolve().parents[1]

pytest_plugins = ("tests.bazarr.wanted_search_fixtures",)


def pytest_report_header(config):
    conflicting_packages = _get_conflicting("libs")
    if conflicting_packages:
        return f"Conflicting packages detected:\n{conflicting_packages}"


def _get_conflicting(path):
    libs_packages = []
    for _, package_name, _ in pkgutil.iter_modules([str(PROJECT_ROOT / path)]):
        libs_packages.append(package_name)

    installed_packages = distributions()
    package_names = [package.metadata["Name"].lower() for package in installed_packages if package.metadata.get("Name")]
    unique_package_names = set(package_names)

    conflicting = []
    for installed in unique_package_names:
        if installed in libs_packages:
            conflicting.append(installed)

    return conflicting


@pytest.fixture(scope="session")
def transactional_engine():
    engine = create_engine(
        "sqlite://",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def transactional_connection(transactional_engine):
    connection = transactional_engine.connect()
    transaction = connection.begin()
    try:
        yield connection
    finally:
        if transaction.is_active:
            transaction.rollback()
        connection.close()


@pytest.fixture
def transactional_session(transactional_connection):
    session = Session(
        bind=transactional_connection,
        future=True,
        join_transaction_mode="create_savepoint",
    )

    try:
        yield session
    finally:
        session.close()
