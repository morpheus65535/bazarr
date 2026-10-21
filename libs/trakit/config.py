import json
import typing
from importlib.resources import files


class Config:
    def __init__(self, config: typing.Mapping[str, typing.Any] | None):
        config_file = files(__package__).joinpath('data/config.json')
        with config_file.open('rb') as f:
            cfg: dict[str, typing.Any] = json.load(f)
        if config:
            cfg.update(config)

        self.ignored: set[str] = set(cfg.get('ignored', []))
        self.countries: typing.Mapping[str, str] = cfg.get('countries', {})
        self.languages: typing.Mapping[str, str] = cfg.get('languages', {})
        self.scripts: typing.Mapping[str, str] = cfg.get('scripts', {})
        self.regions: typing.Mapping[str, str] = cfg.get('regions', {})
        self.implicit_languages: typing.Mapping[str, str] = cfg.get('implicit-languages', {})
