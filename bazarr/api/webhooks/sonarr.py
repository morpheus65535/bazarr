# coding=utf-8
import logging

from flask_restx import Resource, Namespace, fields

from app.database import TableEpisodes, TableShows, database, select
from sonarr.sync.episodes import sync_one_episode
from subtitles.mass_download import episode_download_subtitles
from subtitles.indexer.series import store_subtitles
from utilities.path_mappings import path_mappings


from ..utils import authenticate


api_ns_webhooks_sonarr = Namespace(
    "Webhooks Sonarr",
    description="Webhooks to trigger subtitles search based on Sonarr webhooks",
)


@api_ns_webhooks_sonarr.route("webhooks/sonarr")
class WebHooksSonarr(Resource):
    episode_model = api_ns_webhooks_sonarr.model(
        "SonarrEpisode",
        {
            "id": fields.Integer(required=True, description="Episode ID"),
        },
        strict=False,
    )

    episode_file_model = api_ns_webhooks_sonarr.model(
        "SonarrEpisodeFile",
        {
            "id": fields.Integer(required=True, description="Episode file ID"),
        },
        strict=False,
    )

    sonarr_webhook_model = api_ns_webhooks_sonarr.model(
        "SonarrWebhook",
        {
            "episodes": fields.List(
                fields.Nested(episode_model),
                required=False,
                description="List of episodes. Can be used to sync episodes from Sonarr if not found in Bazarr.",
            ),
            "episodeFiles": fields.List(
                fields.Nested(episode_file_model),
                required=False,
                description="List of episode files; required for anything other than test hooks",
            ),
            "eventType": fields.String(
                required=True,
                description="Type of Sonarr event (e.g. Test, Download, etc.)",
            ),
        },
        strict=False,
    )

    @authenticate
    @api_ns_webhooks_sonarr.expect(sonarr_webhook_model, validate=True)
    @api_ns_webhooks_sonarr.response(200, "Success")
    @api_ns_webhooks_sonarr.response(401, "Not Authenticated")
    def post(self):
        """Search for missing subtitles based on Sonarr webhooks"""
        args = api_ns_webhooks_sonarr.payload
        event_type = args.get("eventType")

        logging.debug(f"Received Sonarr webhook event: {event_type}")

        if event_type == "Test":
            message = "Received test hook, skipping database search."
            logging.debug(message)
            return message, 200

        # Sonarr hooks only differentiate a download starting vs. ending by
        # the inclusion of episodeFiles in the payload.
        sonarr_episode_file_ids = [e.get("id") for e in args.get("episodeFiles", [])]

        if not sonarr_episode_file_ids:
            message = "No episode file IDs found in the webhook request. Nothing to do."
            logging.debug(message)
            # Sonarr reports the webhook as 'unhealthy' and requires
            # user interaction if we return anything except 200s.
            return message, 200

        sonarr_episode_ids = [e.get("id") for e in args.get("episodes", [])]

        if len(sonarr_episode_ids) != len(sonarr_episode_file_ids):
            logging.debug(
                "Episode IDs and episode file IDs are different lengths, ignoring episode IDs."
            )
            sonarr_episode_ids = []

        for i, efid in enumerate(sonarr_episode_file_ids):
            q = (
                select(TableEpisodes.sonarrEpisodeId, TableEpisodes.path)
                .select_from(TableEpisodes)
                .join(TableShows)
                .where(TableEpisodes.episode_file_id == efid)
            )

            episode = database.execute(q).first()
            if not episode and sonarr_episode_ids:
                logging.debug(
                    "No episode found for episode file ID %s, attempting to sync from Sonarr.",
                    efid,
                )
                sync_one_episode(sonarr_episode_ids[i])
                episode = database.execute(q).first()
            if not episode:
                logging.debug(
                    "No episode found for episode file ID %s, skipping.", efid
                )
                continue

            store_subtitles(episode.path, path_mappings.path_replace(episode.path))
            episode_download_subtitles(no=episode.sonarrEpisodeId, send_progress=True)

        return "Finished processing subtitles.", 200
