# coding=utf-8

from apprise import Apprise, AppriseAsset
import logging

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
        .values(notifiers_added))


def get_notifier_providers():
    return database.execute(
        select(TableSettingsNotifier.name, TableSettingsNotifier.url)
        .where(TableSettingsNotifier.enabled == 1))\
        .all()


def send_notifications(sonarr_series_id, sonarr_episode_id, message):
    providers = get_notifier_providers()
    if not len(providers):
        return
    series = database.execute(
        select(TableShows.title, TableShows.year)
        .where(TableShows.sonarrSeriesId == sonarr_series_id))\
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
        select(TableEpisodes.title, TableEpisodes.season, TableEpisodes.episode)
        .where(TableEpisodes.sonarrEpisodeId == sonarr_episode_id))\
        .first()
    if not episode:
        return

    asset = AppriseAsset(async_mode=False)

    apobj = Apprise(asset=asset)

    for provider in providers:
        if provider.url is not None:
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
        select(TableMovies.title, TableMovies.year)
        .where(TableMovies.radarrId == radarr_id))\
        .first()
    if not movie:
        return
    movie_title = movie.title
    movie_year = movie.year
    if movie_year not in [None, '', '0']:
        movie_year = f' ({movie_year})'
    else:
        movie_year = ''

    asset = AppriseAsset(async_mode=False)

    apobj = Apprise(asset=asset)

    for provider in providers:
        if provider.url is not None:
            apobj.add(provider.url)

    apobj.notify(
        title='Bazarr notification',
        body=f"{movie_title}{movie_year} : {message}",
    )
