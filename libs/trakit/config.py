import json
import typing

try:
    from importlib.resources import files
except ImportError:
    from importlib_resources import files  # type: ignore[assignment,no-redef,import-not-found]


class Config:
    def __init__(self, config: typing.Optional[typing.Mapping[str, typing.Any]]):
        config_file = files(__package__).joinpath('data/config.json')
        with config_file.open('rb') as f:
            cfg: typing.Dict[str, typing.Any] = json.load(f)
        if config:
            cfg.update(config)

        self.ignored: typing.Set[str] = set(cfg.get('ignored', []))
        self.countries: typing.Mapping[str, str] = cfg.get('countries', {})
        self.languages: typing.Mapping[str, str] = cfg.get('languages', {})
        self.scripts: typing.Mapping[str, str] = cfg.get('scripts', {})
        self.regions: typing.Mapping[str, str] = cfg.get('regions', {})
        self.implicit_languages: typing.Mapping[str, str] = cfg.get('implicit-languages', {})
