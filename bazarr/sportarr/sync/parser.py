# coding=utf-8

import re

from app.config import settings
from utilities.path_mappings import path_mappings

# A quality name, for example WEBDL-1080p or Bluray-1080p Remux.
QUALITY_NAME = re.compile(r'^([A-Za-z]+)-(\d{3,4})p\b', re.IGNORECASE)
QUALITY_RESOLUTION = re.compile(r'^(\d{3,4})p$', re.IGNORECASE)
# Sportarr writes 2160p as 4K or UHD when the file name does.
RESOLUTION_ALIASES = {'4K': '2160p', 'UHD': '2160p'}
# The source tokens Sportarr writes into a quality built from a file name.
QUALITY_SOURCES = {'BLURAY', 'BD', 'BDREMUX', 'WEBDL', 'WEBRIP', 'WEB', 'HDTV', 'PDTV', 'SDTV', 'DVDRIP', 'DVD',
                   'TELECINE', 'HDCAM', 'CAM', 'TELESYNC', 'TS', 'RAWHD'}


def parse_quality(quality):
    """Split a Sportarr quality string into the source and the resolution.

    Sportarr sends two shapes. A grab keeps the quality name of the release,
    for example WEBDL-1080p. An import parsed from a file name joins tokens
    with spaces, for example 1080P WEBDL x264 AAC.
    """
    if not isinstance(quality, str) or not quality.strip():
        return None, None

    match = QUALITY_NAME.match(quality.strip())
    if match:
        return match.group(1), f'{match.group(2)}p'

    video_format = None
    video_resolution = None
    for token in quality.split():
        resolution = QUALITY_RESOLUTION.match(token)
        if resolution and not video_resolution:
            video_resolution = f'{resolution.group(1)}p'
        elif token.upper() in RESOLUTION_ALIASES and not video_resolution:
            video_resolution = RESOLUTION_ALIASES[token.upper()]
        elif token.upper() in QUALITY_SOURCES and not video_format:
            video_format = token
    return video_format, video_resolution


def eventParser(event, file):
    """Build one row from one playable file.

    A card ships prelims and a main card as separate files under a single
    event, and each needs its own subtitles, so the file is the unit here and
    the event is what groups them.
    """
    video_format, video_resolution = parse_quality(file.get('quality'))

    season = event.get('seasonNumber')
    if season is None:
        season_text = str(event.get('season') or '')
        date_text = str(event.get('eventDate') or '')
        season = int(season_text[:4]) if season_text[:4].isdigit() else \
            int(date_text[:4]) if date_text[:4].isdigit() else 0

    return {
        'sportarrLeagueId': event['leagueId'],
        'sportarrEventId': event['id'],
        # Stable event id from Sportarr, unlike the integer above which is
        # local to one install.
        'externalId': event.get('externalId'),
        'title': event['title'],
        'path': file['filePath'],
        'season': season,
        'episode': event.get('episodeNumber') if event.get('episodeNumber') is not None else 0,
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
    fanart = league.get('bannerUrl') or ''

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
