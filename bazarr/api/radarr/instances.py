# coding=utf-8

import logging
import requests

from flask_restx import Resource, Namespace, fields

from app.database import (TableRadarrInstances, database, select, insert, update, delete,
                          get_radarr_instances)
from radarr.info import url_radarr_from_instance, is_radarr_instance_legacy
from constants import HEADERS
from ..utils import authenticate

api_ns_radarr_instances = Namespace(
    "Radarr Instances",
    description="Manage multiple Radarr instances for multi-library support",
)

instance_model = api_ns_radarr_instances.model(
    "RadarrInstance",
    {
        "id": fields.Integer(readonly=True, description="Instance ID"),
        "name": fields.String(required=True, description="Display name for this instance"),
        "ip": fields.String(required=True, description="Radarr host IP or hostname"),
        "port": fields.Integer(required=True, description="Radarr port"),
        "base_url": fields.String(description="Radarr base URL", default="/"),
        "ssl": fields.Boolean(description="Use SSL", default=False),
        "apikey": fields.String(required=True, description="Radarr API key"),
        "http_timeout": fields.Integer(description="HTTP timeout in seconds", default=60),
        "enabled": fields.Boolean(description="Whether this instance is enabled", default=True),
        "full_update": fields.String(description="Full update frequency (Daily/Weekly/Manually)", default="Daily"),
        "full_update_day": fields.Integer(description="Day of week for weekly full update (0-6)", default=6),
        "full_update_hour": fields.Integer(description="Hour for daily/weekly full update", default=4),
        "movies_sync": fields.Integer(description="Movie sync interval in minutes", default=60),
        "movies_sync_on_live": fields.Boolean(description="Sync movies on SignalR event", default=True),
        "only_monitored": fields.Boolean(description="Only sync monitored movies", default=False),
        "sync_only_monitored_movies": fields.Boolean(description="Skip unmonitored during sync", default=False),
        "defer_search_signalr": fields.Boolean(description="Defer subtitle search after SignalR event", default=False),
        "use_ffprobe_cache": fields.Boolean(description="Use ffprobe cache", default=True),
    }
)

test_result_model = api_ns_radarr_instances.model(
    "RadarrInstanceTestResult",
    {
        "status": fields.String(description="ok or error"),
        "version": fields.String(description="Radarr version if reachable"),
        "message": fields.String(description="Error message if not reachable"),
    }
)


def _row_to_dict(row):
    d = row.to_dict()
    # Convert integer booleans to Python bools for nicer JSON
    for bool_field in ('ssl', 'enabled', 'movies_sync_on_live', 'only_monitored',
                       'sync_only_monitored_movies', 'defer_search_signalr', 'use_ffprobe_cache'):
        if bool_field in d:
            d[bool_field] = bool(d[bool_field])
    return d


def _payload_to_db(payload):
    """Convert API payload to DB dict (booleans -> int for SQLite)."""
    db_dict = {}
    bool_fields = ('ssl', 'enabled', 'movies_sync_on_live', 'only_monitored',
                   'sync_only_monitored_movies', 'defer_search_signalr', 'use_ffprobe_cache')
    for key, value in payload.items():
        if key == 'id':
            continue
        if key in bool_fields:
            db_dict[key] = 1 if value else 0
        else:
            db_dict[key] = value
    if 'excluded_tags' not in db_dict:
        db_dict['excluded_tags'] = '[]'
    return db_dict


@api_ns_radarr_instances.route("radarr/instances")
class RadarrInstancesList(Resource):
    @authenticate
    @api_ns_radarr_instances.marshal_list_with(instance_model)
    @api_ns_radarr_instances.response(200, "Success")
    @api_ns_radarr_instances.response(401, "Not Authenticated")
    def get(self):
        """List all configured Radarr instances."""
        rows = database.execute(
            select(TableRadarrInstances).order_by(TableRadarrInstances.id)
        ).scalars().all()
        return [_row_to_dict(row) for row in rows]

    @authenticate
    @api_ns_radarr_instances.expect(instance_model, validate=False)
    @api_ns_radarr_instances.response(201, "Instance created")
    @api_ns_radarr_instances.response(400, "Bad request")
    @api_ns_radarr_instances.response(401, "Not Authenticated")
    def post(self):
        """Add a new Radarr instance."""
        payload = api_ns_radarr_instances.payload or {}
        db_dict = _payload_to_db(payload)

        try:
            result = database.execute(
                insert(TableRadarrInstances).values(**db_dict)
            )
            new_id = result.inserted_primary_key[0]
        except Exception as e:
            logging.exception("BAZARR Error creating Radarr instance")
            return {"message": str(e)}, 400

        # Start SignalR client for the new instance
        try:
            from app.signalr_client import radarr_signalr_client
            from app.config import settings
            if settings.general.use_radarr:
                new_row = database.execute(
                    select(TableRadarrInstances).where(TableRadarrInstances.id == new_id)
                ).scalar_one_or_none()
                if new_row and new_row.enabled:
                    radarr_signalr_client.add_instance(new_row.to_dict())
        except Exception:
            logging.exception("BAZARR Could not start SignalR for new Radarr instance")

        return {"id": new_id, "message": "Instance created successfully"}, 201


@api_ns_radarr_instances.route("radarr/instances/<int:instance_id>")
class RadarrInstanceItem(Resource):
    @authenticate
    @api_ns_radarr_instances.marshal_with(instance_model)
    @api_ns_radarr_instances.response(200, "Success")
    @api_ns_radarr_instances.response(401, "Not Authenticated")
    @api_ns_radarr_instances.response(404, "Instance not found")
    def get(self, instance_id):
        """Get a specific Radarr instance by ID."""
        row = database.execute(
            select(TableRadarrInstances).where(TableRadarrInstances.id == instance_id)
        ).scalar_one_or_none()
        if not row:
            api_ns_radarr_instances.abort(404, f"Radarr instance {instance_id} not found")
        return _row_to_dict(row)

    @authenticate
    @api_ns_radarr_instances.expect(instance_model, validate=False)
    @api_ns_radarr_instances.response(200, "Instance updated")
    @api_ns_radarr_instances.response(400, "Bad request")
    @api_ns_radarr_instances.response(401, "Not Authenticated")
    @api_ns_radarr_instances.response(404, "Instance not found")
    def put(self, instance_id):
        """Update a Radarr instance."""
        row = database.execute(
            select(TableRadarrInstances).where(TableRadarrInstances.id == instance_id)
        ).scalar_one_or_none()
        if not row:
            api_ns_radarr_instances.abort(404, f"Radarr instance {instance_id} not found")

        payload = api_ns_radarr_instances.payload or {}
        db_dict = _payload_to_db(payload)

        try:
            database.execute(
                update(TableRadarrInstances).values(**db_dict)
                .where(TableRadarrInstances.id == instance_id)
            )
        except Exception as e:
            logging.exception("BAZARR Error updating Radarr instance")
            return {"message": str(e)}, 400

        # Restart SignalR client for this instance
        try:
            from app.signalr_client import radarr_signalr_client
            from app.config import settings
            if settings.general.use_radarr:
                updated_row = database.execute(
                    select(TableRadarrInstances).where(TableRadarrInstances.id == instance_id)
                ).scalar_one_or_none()
                if updated_row:
                    if updated_row.enabled:
                        radarr_signalr_client.add_instance(updated_row.to_dict())
                    else:
                        radarr_signalr_client.remove_instance(instance_id)
        except Exception:
            logging.exception("BAZARR Could not restart SignalR for updated Radarr instance")

        return {"message": "Instance updated successfully"}, 200

    @authenticate
    @api_ns_radarr_instances.response(200, "Instance deleted")
    @api_ns_radarr_instances.response(400, "Cannot delete primary instance")
    @api_ns_radarr_instances.response(401, "Not Authenticated")
    @api_ns_radarr_instances.response(404, "Instance not found")
    def delete(self, instance_id):
        """Delete a Radarr instance (and all its movies from the database)."""
        if instance_id == 1:
            return {"message": "Cannot delete the primary Radarr instance (id=1). "
                               "Disable it instead or reconfigure via Settings."}, 400

        row = database.execute(
            select(TableRadarrInstances).where(TableRadarrInstances.id == instance_id)
        ).scalar_one_or_none()
        if not row:
            api_ns_radarr_instances.abort(404, f"Radarr instance {instance_id} not found")

        # Stop SignalR client for this instance
        try:
            from app.signalr_client import radarr_signalr_client
            radarr_signalr_client.remove_instance(instance_id)
        except Exception:
            logging.exception("BAZARR Could not stop SignalR for deleted Radarr instance")

        # The ON DELETE CASCADE will remove movies from this instance automatically
        try:
            database.execute(
                delete(TableRadarrInstances).where(TableRadarrInstances.id == instance_id)
            )
        except Exception as e:
            logging.exception("BAZARR Error deleting Radarr instance")
            return {"message": str(e)}, 400

        return {"message": f"Radarr instance {instance_id} deleted successfully"}, 200


@api_ns_radarr_instances.route("radarr/instances/<int:instance_id>/test")
class RadarrInstanceTest(Resource):
    @authenticate
    @api_ns_radarr_instances.marshal_with(test_result_model)
    @api_ns_radarr_instances.response(200, "Test result")
    @api_ns_radarr_instances.response(401, "Not Authenticated")
    @api_ns_radarr_instances.response(404, "Instance not found")
    def get(self, instance_id):
        """Test connectivity to a Radarr instance."""
        row = database.execute(
            select(TableRadarrInstances).where(TableRadarrInstances.id == instance_id)
        ).scalar_one_or_none()
        if not row:
            api_ns_radarr_instances.abort(404, f"Radarr instance {instance_id} not found")

        instance = row.to_dict()
        legacy = is_radarr_instance_legacy(instance)
        base_url = url_radarr_from_instance(instance)
        apikey = instance.get('apikey', '')
        timeout = int(instance.get('http_timeout', 60))

        try:
            url = f"{base_url}/api/v3/system/status?apikey={apikey}"
            r = requests.get(url, timeout=timeout, verify=False, headers=HEADERS)
            r.raise_for_status()
            version = r.json().get('version', 'unknown')
            return {"status": "ok", "version": version, "message": ""}
        except requests.exceptions.ConnectionError as e:
            return {"status": "error", "version": "", "message": f"Connection error: {e}"}
        except requests.exceptions.Timeout:
            return {"status": "error", "version": "", "message": "Connection timed out"}
        except Exception as e:
            return {"status": "error", "version": "", "message": str(e)}
