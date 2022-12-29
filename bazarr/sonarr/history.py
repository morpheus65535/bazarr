# coding=utf-8

import time
from datetime import datetime

from app.database import TableHistory
from app.event_handler import event_stream


def history_log(action, sonarr_series_id, sonarr_episode_id, description, video_path=None, language=None, provider=None,
                score=None, subs_id=None, subtitles_path=None):
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
