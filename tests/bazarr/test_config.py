import importlib
import os
import subprocess
import sys

from bazarr.app import config


def test_get_settings():
    assert isinstance(config.get_settings(), dict)


def test_settings_exposes_general_defaults():
    assert config.settings.general.minimum_score == 90


def test_get_args_ignores_unknown_cli_arguments(monkeypatch):
    monkeypatch.setenv("NO_CLI", "false")
    monkeypatch.setattr(sys, "argv", ["pytest", "--unknown-flag", "value"])

    module = importlib.import_module("bazarr.app.get_args")
    reloaded = importlib.reload(module)

    assert reloaded.args.config_dir.endswith("data")


def test_config_import_does_not_import_subtitles_package_side_effects():
    environment = os.environ.copy()
    environment["PYTHONPATH"] = "bazarr"
    environment.setdefault("BAZARR_VERSION", "v0.0.0-test")
    environment.setdefault("SZ_USER_AGENT", "pytest")

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import app.libs; from app.config import settings; print(type(settings).__name__)",
        ],
        check=True,
        env=environment,
        text=True,
        capture_output=True,
    )

    assert result.stdout.strip() == "LazySettings"
