# coding=utf-8

from datetime import datetime

from app.database import TableHistoryMovie
from app.event_handler import event_stream


def history_log_movie(action, radarr_id, description, video_path=None, language=None, provider=None, score=None,
                      subs_id=None, subtitles_path=None):
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
