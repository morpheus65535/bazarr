# -*- coding: utf-8 -*-
import os
import pkgutil
import sys

import pkg_resources

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../libs/"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../bazarr/"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../custom_libs/"))


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
    for _, package_name, _ in pkgutil.iter_modules([path]):
        libs_packages.append(package_name)

    installed_packages = pkg_resources.working_set
    package_names = [package.key for package in installed_packages]
    unique_package_names = set(package_names)

    conflicting = []
    for installed in unique_package_names:
        if installed in libs_packages:
            conflicting.append(installed)

    return conflicting
