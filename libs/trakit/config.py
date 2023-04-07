import json
import typing

from pkg_resources import resource_stream


class Config:
    def __init__(self, config: typing.Optional[typing.Mapping[str, typing.Any]]):
        with resource_stream('trakit', 'data/config.json') as f:
            cfg: typing.Dict[str, typing.Any] = json.load(f)
        if config:
            cfg.update(config)

        self.ignored: typing.Set[str] = set(cfg.get('ignored', []))
        self.countries: typing.Mapping[str, str] = cfg.get('countries', {})
        self.languages: typing.Mapping[str, str] = cfg.get('languages', {})
        self.scripts: typing.Mapping[str, str] = cfg.get('scripts', {})
        self.regions: typing.Mapping[str, str] = cfg.get('regions', {})
        self.implicit_languages: typing.Mapping[str, str] = cfg.get('implicit-languages', {})
