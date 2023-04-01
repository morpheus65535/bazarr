# coding=utf-8

from datetime import datetime

from app.database import TableHistory, database, insert
from app.event_handler import event_stream


def history_log(action, sonarr_series_id, sonarr_episode_id, result, fake_provider=None, fake_score=None):
    description = result.message
    video_path = result.path
    language = result.language_code
    provider = fake_provider or result.provider
    score = fake_score or result.score
    subs_id = result.subs_id
    subtitles_path = result.subs_path

    database.execute(insert(TableHistory).values(
        action=action,
        sonarrSeriesId=sonarr_series_id,
        sonarrEpisodeId=sonarr_episode_id,
        timestamp=datetime.now(),
        description=description,
        video_path=video_path,
        language=language,
        provider=provider,
        score=score,
        subs_id=subs_id,
        subtitles_path=subtitles_path
    ))
    database.coomit()
    event_stream(type='episode-history')
