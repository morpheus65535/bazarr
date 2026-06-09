# -*- coding: utf-8 -*-
import os
import pkgutil
from importlib.metadata import distributions
from pathlib import Path

import pytest

# Reuse Bazarr's normal import bootstrap instead of maintaining a test-only
# sys.path setup in parallel.
import bazarr.app.libs  # noqa: F401

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

PROJECT_ROOT = Path(__file__).resolve().parents[1]



def pytest_configure(config):
    """Tests import bazarr modules directly, skipping the startup code that normally creates the
    database directory and schema. Do the minimum of it here so the suite also runs from a fresh
    checkout (e.g. CI)."""
    os.makedirs(os.path.join(os.path.dirname(__file__), "..", "data", "db"), exist_ok=True)

    from app.database import engine, metadata

    metadata.create_all(engine)

    from languages.get_languages import load_language_in_db

    load_language_in_db()


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
def transactional_engine(tmp_path_factory):
    db_dir = tmp_path_factory.mktemp("transactional-db")
    db_path = db_dir / "tests.sqlite"
    engine = create_engine(f"sqlite:///{db_path}", future=True)
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
