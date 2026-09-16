# coding=utf-8

from app.config import settings
from utilities.path_mappings import path_mappings


def eventParser(event, file):
    """Build one row from one playable file.

    A card ships prelims and a main card as separate files under a single
    event, and each needs its own subtitles, so the file is the unit here and
    the event is what groups them.
    """
    video_format = None
    video_resolution = None
    if file.get('quality'):
        # Sportarr reports quality as source and resolution joined, for
        # example WEBDL-1080p, which is the shape Sonarr uses too.
        parts = file['quality'].split('-')
        video_format = parts[0]
        if len(parts) > 1:
            video_resolution = parts[1]

    return {
        'sportarrLeagueId': event['leagueId'],
        'sportarrEventId': event['id'],
        # Stable event id from Sportarr, unlike the integer above which is
        # local to one install.
        'externalId': event.get('externalId'),
        'title': event['title'],
        'path': file['filePath'],
        'season': event['seasonNumber'],
        'episode': event['episodeNumber'],
        'broadcastDate': event.get('broadcastDate') or event.get('eventDate'),
        'partName': file.get('partName'),
        # 0 keeps a single-file event distinct from a part, so the key stays
        # unique either way.
        'partNumber': file.get('partNumber') or 0,
        # Set only when a real grab produced the file. Null means there is no
        # release to match, so a consumer falls back to the file hash.
        'sceneName': file.get('releaseTitle'),
        'monitored': str(bool(event['monitored'])),
        'format': video_format,
        'resolution': video_resolution,
        'video_codec': file.get('codec'),
        'audio_codec': file.get('audioCodec'),
        # Changes when a quality upgrade replaces the file, which is how a
        # consumer knows the media changed while the path stayed the same.
        'file_id': file['id'],
        'audio_language': str(file.get('languages') or []),
        'file_size': file.get('size'),
    }


def leagueParser(league, action, tags_dict, language_profiles, league_default_profile):
    overview = league['overview'] if 'overview' in league else ''
    poster = league.get('posterUrl') or ''
    fanart = league.get('fanartUrl') or ''

    tags = [d['label'] for d in tags_dict if d['id'] in league.get('tags', [])]

    audio_language = []

    parsed_league = {
        'title': league["name"],
        'path': league["path"],
        # Sportarr's own id, stable across a remove and re-add. Matching on it
        # keeps subtitle history that keying on the integer alone would lose.
        'externalId': league.get("externalId"),
        'sportarrLeagueId': int(league["id"]),
        'overview': overview,
        'poster': poster,
        'fanart': fanart,
        'audio_language': str(audio_language),
        'sortTitle': league.get("sortTitle") or league["name"],
        'sport': league.get("sport"),
        'monitored': str(bool(league['monitored'])),
        'tags': str(tags),
    }

    if action == 'insert':
        parsed_league['profileId'] = league_default_profile

    return parsed_league
