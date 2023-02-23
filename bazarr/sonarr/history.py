# coding=utf-8

from datetime import datetime

from app.database import TableHistory
from app.event_handler import event_stream


def history_log(action, sonarr_series_id, sonarr_episode_id, result, fake_provider=None, fake_score=None):
    description = result.message
    video_path = result.path
    language = result.language_code
    provider = fake_provider or result.provider
    score = fake_score or result.score
    subs_id = result.subs_id
    subtitles_path = result.subs_path

    TableHistory.insert({
        TableHistory.action: action,
        TableHistory.sonarrSeriesId: sonarr_series_id,
        TableHistory.sonarrEpisodeId: sonarr_episode_id,
        TableHistory.timestamp: datetime.now(),
        TableHistory.description: description,
        TableHistory.video_path: video_path,
        TableHistory.language: language,
        TableHistory.provider: provider,
        TableHistory.score: score,
        TableHistory.subs_id: subs_id,
        TableHistory.subtitles_path: subtitles_path
    }).execute()
    event_stream(type='episode-history')
