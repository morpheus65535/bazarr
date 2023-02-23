# coding=utf-8

from datetime import datetime

from app.database import TableHistoryMovie
from app.event_handler import event_stream


def history_log_movie(action, radarr_id, result, fake_provider=None, fake_score=None):
    description = result.message
    video_path = result.path
    language = result.language_code
    provider = fake_provider or result.provider
    score = fake_score or result.score
    subs_id = result.subs_id
    subtitles_path = result.subs_path

    TableHistoryMovie.insert({
        TableHistoryMovie.action: action,
        TableHistoryMovie.radarrId: radarr_id,
        TableHistoryMovie.timestamp: datetime.now(),
        TableHistoryMovie.description: description,
        TableHistoryMovie.video_path: video_path,
        TableHistoryMovie.language: language,
        TableHistoryMovie.provider: provider,
        TableHistoryMovie.score: score,
        TableHistoryMovie.subs_id: subs_id,
        TableHistoryMovie.subtitles_path: subtitles_path
    }).execute()
    event_stream(type='movie-history')
