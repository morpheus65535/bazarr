# coding=utf-8
import logging

from flask_restx import Resource, Namespace, fields

from app.database import TableMovies, database, select
from radarr.sync.movies import update_one_movie
from subtitles.mass_download import movies_download_subtitles
from subtitles.indexer.movies import store_subtitles_movie
from utilities.path_mappings import path_mappings

from ..utils import authenticate


api_ns_webhooks_radarr = Namespace(
    "Webhooks Radarr",
    description="Webhooks to trigger subtitles search based on Radarr webhooks",
)


@api_ns_webhooks_radarr.route("webhooks/radarr")
class WebHooksRadarr(Resource):
    movie_model = api_ns_webhooks_radarr.model(
        "RadarrMovie",
        {
            "id": fields.Integer(required=True, description="Movie ID"),
        },
        strict=False,
    )

    movie_file_model = api_ns_webhooks_radarr.model(
        "RadarrMovieFile",
        {
            "id": fields.Integer(required=True, description="Movie file ID"),
        },
        strict=False,
    )

    radarr_webhook_model = api_ns_webhooks_radarr.model(
        "RadarrWebhook",
        {
            "eventType": fields.String(
                required=True,
                description="Type of Radarr event (e.g. MovieAdded, Test, etc)",
            ),
            "movieFile": fields.Nested(
                movie_file_model,
                required=False,
                description="Radarr movie file payload. Required for anything other than test hooks",
            ),
            "movie": fields.Nested(
                movie_model,
                required=False,
                description="Radarr movie payload. Can be used to sync movies from Radarr if not found in Bazarr",
            ),
        },
        strict=False,
    )

    @authenticate
    @api_ns_webhooks_radarr.expect(radarr_webhook_model, validate=True)
    @api_ns_webhooks_radarr.response(200, "Success")
    @api_ns_webhooks_radarr.response(401, "Not Authenticated")
    def post(self):
        """Search for missing subtitles based on Radarr webhooks"""
        args = api_ns_webhooks_radarr.payload
        event_type = args.get("eventType")

        logging.debug(f"Received Radarr webhook event: {event_type}")

        if event_type == "Test":
            message = "Received test hook, skipping database search."
            logging.debug(message)
            return message, 200

        movie_file_id = args.get("movieFile", {}).get("id")

        if not movie_file_id:
            message = "No movie file ID found in the webhook request. Nothing to do."
            logging.debug(message)
            # Radarr reports the webhook as 'unhealthy' and requires
            # user interaction if we return anything except 200s.
            return message, 200

        # This webhook is often faster than the database update,
        # so we update the movie first if we can.
        radarr_id = args.get("movie", {}).get("id")

        q = select(TableMovies.radarrId, TableMovies.path).where(
            TableMovies.movie_file_id == movie_file_id
        )

        movie = database.execute(q).first()
        if not movie and radarr_id:
            logging.debug(
                f"No movie matching file ID {movie_file_id} found in the database. Attempting to sync from Radarr."
            )
            update_one_movie(radarr_id, "updated")
            movie = database.execute(q).first()
        if not movie:
            message = f"No movie matching file ID {movie_file_id} found in the database. Nothing to do."
            logging.debug(message)
            return message, 200

        store_subtitles_movie(movie.path, path_mappings.path_replace_movie(movie.path))
        movies_download_subtitles(no=movie.radarrId)

        return "Finished processing subtitles.", 200
