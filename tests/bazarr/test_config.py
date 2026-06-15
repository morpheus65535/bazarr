import importlib
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
