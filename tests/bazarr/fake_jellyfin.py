"""Fake Jellyfin client for testing.

Returns configurable data that is validated against the OpenAPI spec on every call.
Both requests and responses are validated — if you pass bad params or configure
bad fixture data, it fails immediately.
"""

import json
import os

from jsonschema import validate, RefResolver

# Spec downloaded from https://api.jellyfin.org/openapi/jellyfin-openapi-stable.json

OPENAPI_PATH = os.path.join(os.path.dirname(__file__), "fixtures", "jellyfin-openapi.json")

_spec = None
_resolver = None


def _load_spec():
    global _spec, _resolver
    if _spec is None:
        with open(OPENAPI_PATH) as f:
            _spec = json.load(f)
        _resolver = RefResolver.from_schema(_spec)
    return _spec, _resolver


def _has_spec():
    return os.path.exists(OPENAPI_PATH)


def validate_response(data, path, method="get", status="200"):
    """Validate data against the OpenAPI response schema."""
    spec, resolver = _load_spec()
    content = spec["paths"][path][method]["responses"][status]["content"]
    schema = list(content.values())[0]["schema"]
    validate(instance=data, schema=schema, resolver=resolver)


def _validate_params(params, path, method="get"):
    """Validate that query params are recognized by the spec."""
    spec, _ = _load_spec()
    op = spec["paths"].get(path, {}).get(method, {})
    valid_params = {p["name"] for p in op.get("parameters", [])}
    unknown = set(params.keys()) - valid_params
    if unknown:
        raise ValueError(f"Unknown params for {method.upper()} {path}: {unknown}. Valid: {valid_params}")


def _validate_enum(value, path, method, param_name):
    """Validate a param value against its enum in the spec."""
    spec, _ = _load_spec()
    op = spec["paths"].get(path, {}).get(method, {})
    for p in op.get("parameters", []):
        if p["name"] == param_name:
            schema = p.get("schema", {})
            enum = schema.get("enum")
            if not enum:
                for item in schema.get("allOf", []):
                    ref = item.get("$ref", "")
                    if ref:
                        name = ref.split("/")[-1]
                        enum = spec["components"]["schemas"].get(name, {}).get("enum")
            if enum and value not in enum:
                raise ValueError(f"Invalid value '{value}' for {param_name}. Valid: {enum}")


def _validate_request_body(data, path, method="post"):
    """Validate request body against the spec schema."""
    spec, resolver = _load_spec()
    op = spec["paths"].get(path, {}).get(method, {})
    body_content = op.get("requestBody", {}).get("content", {})
    if body_content:
        schema = list(body_content.values())[0]["schema"]
        validate(instance=data, schema=schema, resolver=resolver)


def _validate_fields(fields_str):
    """Validate that requested fields are valid ItemFields enum values."""
    spec, _ = _load_spec()
    item_fields = spec["components"]["schemas"].get("ItemFields", {}).get("enum", [])
    if item_fields:
        for field in fields_str.split(","):
            field = field.strip()
            if field and field not in item_fields:
                raise ValueError(f"Invalid field '{field}'. Valid: {item_fields}")


def make_movie(id="movie-1", name="Test Movie", imdb_id="tt0000001",
               tmdb_id="12345", path="/media/movies/Test Movie (2020)/Test Movie (2020).mkv"):
    return {
        "Name": name,
        "Id": id,
        "Type": "Movie",
        "Path": path,
        "ProviderIds": {
            **({"Imdb": imdb_id} if imdb_id else {}),
            **({"Tmdb": tmdb_id} if tmdb_id else {}),
        },
        "MediaStreams": [],
    }


def make_series(id="series-1", name="Test Show", imdb_id="tt0000002",
                tvdb_id="100", path="/media/shows/Test Show (2020)"):
    return {
        "Name": name,
        "Id": id,
        "Type": "Series",
        "Path": path,
        "ProviderIds": {
            **({"Imdb": imdb_id} if imdb_id else {}),
            **({"Tvdb": str(tvdb_id)} if tvdb_id else {}),
        },
        "MediaStreams": [],
    }


def make_episode(id="ep-1", name="Episode 1", index=1):
    return {
        "Id": id,
        "Name": name,
        "IndexNumber": index,
        "Type": "Episode",
        "ProviderIds": {},
    }


class FakeJellyfinClient:
    """Drop-in replacement for JellyfinClient with OpenAPI validation.

    Validates both requests (params, body, enums) and responses (schema)
    against Jellyfin's OpenAPI spec on every call.

    Usage:
        client = FakeJellyfinClient()
        client.items = [make_movie(imdb_id="tt123")]
        client.episodes = {"series-1": {1: [make_episode()]}}
    """

    def __init__(self):
        self.base_url = "http://fake-jellyfin:8096"
        self.session = None

        self.system_info = {
            "ServerName": "TestServer",
            "Version": "10.12.0",
            "Id": "abc123",
            "LocalAddress": "http://192.168.1.100:8096",
            "OperatingSystem": "Linux",
            "ProductName": "Jellyfin Server",
            "StartupWizardCompleted": True,
            "HasPendingRestart": False,
            "IsShuttingDown": False,
            "SupportsLibraryMonitor": True,
        }

        self.libraries = [
            {
                "Name": "Movies",
                "Locations": ["/media/movies"],
                "CollectionType": "movies",
                "ItemId": "lib-movies",
            },
            {
                "Name": "Shows",
                "Locations": ["/media/shows"],
                "CollectionType": "tvshows",
                "ItemId": "lib-shows",
            },
        ]

        self.items = []
        self.episodes = {}  # {"series-1": {1: [make_episode(), ...]}}

        # Track calls for assertions
        self.refresh_item_calls = []
        self.report_media_updated_calls = []

    def get_system_info(self) -> dict:
        if _has_spec():
            validate_response(self.system_info, "/System/Info")
        return self.system_info

    def get_libraries(self) -> list:
        if _has_spec():
            validate_response(self.libraries, "/Library/VirtualFolders")
        return self.libraries

    def get_items(self, params: dict) -> list:
        if _has_spec():
            _validate_params(params, "/Items")
            if "fields" in params:
                _validate_fields(params["fields"])
        response = {
            "Items": self.items,
            "TotalRecordCount": len(self.items),
            "StartIndex": 0,
        }
        if _has_spec():
            validate_response(response, "/Items")
        return response["Items"]

    def get_episodes(self, series_id: str, season: int) -> list:
        params = {"season": season, "fields": "ProviderIds"}
        if _has_spec():
            _validate_params(params, "/Shows/{seriesId}/Episodes")
            _validate_fields(params["fields"])
        episodes = self.episodes.get(series_id, {}).get(season, [])
        response = {
            "Items": episodes,
            "TotalRecordCount": len(episodes),
            "StartIndex": 0,
        }
        if _has_spec():
            validate_response(response, "/Shows/{seriesId}/Episodes")
        return response["Items"]

    def refresh_item(self, item_id: str) -> None:
        if _has_spec():
            _validate_enum("ValidationOnly", "/Items/{itemId}/Refresh", "post", "metadataRefreshMode")
        self.refresh_item_calls.append(item_id)

    def report_media_updated(self, path: str) -> None:
        body = {"Updates": [{"Path": path, "UpdateType": "Modified"}]}
        if _has_spec():
            _validate_request_body(body, "/Library/Media/Updated")
        self.report_media_updated_calls.append(path)

    def get(self, path, params=None):
        raise RuntimeError(f"FakeJellyfinClient.get() called with {path} — use the high-level methods instead")

    def post(self, path, json=None, params=None):
        raise RuntimeError(f"FakeJellyfinClient.post() called with {path} — use the high-level methods instead")
