# coding=utf-8

import datetime

from subliminal.refiners.tvdb import Episode, logger, search_series, series_re, sanitize, get_series, \
    get_series_episode, region, tvdb_client

from util import fix_session_bases

TVDB_SEASON_EXPIRATION_TIME = datetime.timedelta(days=1).total_seconds()

fix_session_bases(tvdb_client.session)


@region.cache_on_arguments(expiration_time=TVDB_SEASON_EXPIRATION_TIME)
def is_season_fully_aired(series_id, season):
    """Get series.

    :param int id: id of the series.
    :return: the series data.
    :rtype: dict

    """
    result = tvdb_client.query_series_episodes(series_id, aired_season=season)

    # fixme: timezone unclear.
    now = datetime.date.today()
    if result:
        for data in result['data']:
            if data['firstAired']:
                aired_at = datetime.datetime.strptime(data['firstAired'], '%Y-%m-%d').date()
                if aired_at > now:
                    return False
    else:
        return
    return True


def refine(video, **kwargs):
    """Refine a video by searching `TheTVDB <http://thetvdb.com/>`_.

    .. note::

        This refiner only work for instances of :class:`~subliminal.video.Episode`.

    Several attributes can be found:

      * :attr:`~subliminal.video.Episode.series`
      * :attr:`~subliminal.video.Episode.year`
      * :attr:`~subliminal.video.Episode.series_imdb_id`
      * :attr:`~subliminal.video.Episode.series_tvdb_id`
      * :attr:`~subliminal.video.Episode.title`
      * :attr:`~subliminal.video.Video.imdb_id`
      * :attr:`~subliminal.video.Episode.tvdb_id`

    """
    # only deal with Episode videos
    if not isinstance(video, Episode):
        logger.error('Can only refine episodes')
        return

    # exit if the information is complete
    if video.series_tvdb_id and video.tvdb_id:
        logger.debug('No need to search')
        return

    # search the series
    logger.info('Searching series %r', video.series)
    results = search_series(video.series.lower())
    if not results:
        logger.warning('No results for series')
        return
    logger.debug('Found %d results', len(results))

    # search for exact matches
    matching_results = []
    for result in results:
        matching_result = {}

        # use seriesName and aliases
        series_names = [result['seriesName']]
        series_names.extend(result['aliases'])

        # parse the original series as series + year or country
        original_match = series_re.match(result['seriesName']).groupdict()

        # parse series year
        series_year = None
        if result['firstAired']:
            series_year = datetime.datetime.strptime(result['firstAired'], '%Y-%m-%d').year

        # discard mismatches on year
        if video.year and series_year and video.year != series_year:
            logger.debug('Discarding series %r mismatch on year %d', result['seriesName'], series_year)
            continue

        # iterate over series names
        for series_name in series_names:
            # parse as series and year
            series, year, country = series_re.match(series_name).groups()
            if year:
                year = int(year)

            # discard mismatches on year
            if year and (video.original_series or video.year != year):
                logger.debug('Discarding series name %r mismatch on year %d', series, year)
                continue

            # match on sanitized series name
            if sanitize(series) == sanitize(video.series):
                logger.debug('Found exact match on series %r', series_name)
                matching_result['match'] = {'series': original_match['series'], 'year': series_year,
                                            'original_series': original_match['year'] is None}
                break

        # add the result on match
        if matching_result:
            matching_result['data'] = result
            matching_results.append(matching_result)

    # exit if we don't have exactly 1 matching result
    if not matching_results:
        logger.warning('No matching series found')
        return
    if len(matching_results) > 1:
        logger.error('Multiple matches found')
        return

    # get the series
    matching_result = matching_results[0]
    series = get_series(matching_result['data']['id'])

    # add series information
    logger.debug('Found series %r', series)
    video.series = matching_result['match']['series']
    video.alternative_series.extend(series['aliases'])
    video.year = matching_result['match']['year']
    video.original_series = matching_result['match']['original_series']
    video.series_tvdb_id = series['id']
    video.series_imdb_id = series['imdbId'] or None

    # get the episode
    logger.info('Getting series episode %dx%d', video.season, video.episode)
    episode = get_series_episode(video.series_tvdb_id, video.season, video.episode)
    if not episode:
        logger.warning('No results for episode')
        return

    # add episode information
    logger.debug('Found episode %r', episode)
    video.tvdb_id = episode['id']
    video.title = episode['episodeName'] or None
    video.imdb_id = episode['imdbId'] or None

    # get season fully aired information
    season_fully_aired = is_season_fully_aired(video.series_tvdb_id, video.season)
    if season_fully_aired is not None:
        video.season_fully_aired = season_fully_aired
