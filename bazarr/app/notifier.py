# coding=utf-8

from apprise import Apprise, AppriseAsset
import logging
import re
from urllib.parse import quote

from .database import TableSettingsNotifier, TableEpisodes, TableShows, TableMovies, database, insert, delete, select


def update_notifier():
    # define apprise object
    a = Apprise()

    # Retrieve all the details
    results = a.details()

    notifiers_added = []
    notifiers_kept = []

    notifiers_in_db = [row.name for row in
                       database.execute(
                           select(TableSettingsNotifier.name))
                       .all()]

    for x in results['schemas']:
        if x['service_name'] not in notifiers_in_db:
            notifiers_added.append({'name': str(x['service_name']), 'enabled': 0})
            logging.debug(f'Adding new notifier agent: {x["service_name"]}')
        else:
            notifiers_kept.append(x['service_name'])

    notifiers_to_delete = [item for item in notifiers_in_db if item not in notifiers_kept]

    for item in notifiers_to_delete:
        database.execute(
            delete(TableSettingsNotifier)
            .where(TableSettingsNotifier.name == item))

    database.execute(
        insert(TableSettingsNotifier)
        .values(notifiers_added)
        .on_conflict_do_nothing())


def get_notifier_providers():
    return database.execute(
        select(TableSettingsNotifier.name, TableSettingsNotifier.url)
        .where(
            TableSettingsNotifier.enabled == 1,
            TableSettingsNotifier.url.is_not(None),
        ))\
        .all()


def send_notifications(sonarr_series_id, sonarr_episode_id, message):
    providers = get_notifier_providers()
    if not len(providers):
        return
    series = database.execute(
        select(TableShows)
        .where(TableShows.sonarrSeriesId == sonarr_series_id))\
        .scalars()\
        .first()
    if not series:
        return
    series_title = series.title
    series_year = series.year
    if series_year not in [None, '', '0']:
        series_year = f' ({series_year})'
    else:
        series_year = ''
    episode = database.execute(
        select(TableEpisodes)
        .where(TableEpisodes.sonarrEpisodeId == sonarr_episode_id))\
        .scalars()\
        .first()
    if not episode:
        return

    media_variables = {}
    media_variables.update(_build_media_variables(series, 'series'))
    media_variables.update(_build_media_variables(episode, 'episode'))

    asset = AppriseAsset(async_mode=False)

    apobj = Apprise(asset=asset)

    for provider in providers:
        if provider.name in {"Form", "XML", "JSON"}:
            apobj.add(_expand_notifier_url(provider.url, media_variables))
        else:
            apobj.add(provider.url)

    apobj.notify(
        title='Bazarr notification',
        body=f"{series_title}{series_year} - S{episode.season:02d}E{episode.episode:02d} - {episode.title} : {message}",
    )


def send_notifications_movie(radarr_id, message):
    providers = get_notifier_providers()
    if not len(providers):
        return
    movie = database.execute(
        select(TableMovies)
        .where(TableMovies.radarrId == radarr_id))\
        .scalars()\
        .first()
    if not movie:
        return
    movie_title = movie.title
    movie_year = movie.year
    if movie_year not in [None, '', '0']:
        movie_year = f' ({movie_year})'
    else:
        movie_year = ''

    media_variables = _build_media_variables(movie, 'movie')

    asset = AppriseAsset(async_mode=False)

    apobj = Apprise(asset=asset)

    for provider in providers:
        if provider.name in {"Form", "XML", "JSON"}:
            apobj.add(_expand_notifier_url(provider.url, media_variables))
        else:
            apobj.add(provider.url)

    apobj.notify(
        title='Bazarr notification',
        body=f"{movie_title}{movie_year} : {message}",
    )


def _build_media_variables(record, prefix):
    if record is None or not prefix:
        return {}

    return {f'bazarr_{prefix}_{key}': value for key, value in record.to_dict().items()}


def _expand_notifier_url(url, media_variables):
    if url is None or not media_variables:
        return url

    # Looks for {bazarr_*} placeholders in the URL string
    placeholder_pattern = re.compile(r'\{(bazarr_[A-Za-z0-9_]+)\}')

    def replace(match):
        key = match.group(1)
        if key not in media_variables:
            return ''

        value = media_variables[key]
        if value is None:
            return ''

        return quote(str(value), safe='')

    return placeholder_pattern.sub(replace, url)
