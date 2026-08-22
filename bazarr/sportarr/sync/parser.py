# coding=utf-8

from app.config import settings
from utilities.path_mappings import path_mappings


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
