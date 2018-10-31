# coding=utf-8

import logging

from subliminal.video import Episode, Movie
from subliminal.score import get_scores

logger = logging.getLogger(__name__)


FPS_EQUALITY = (
    (23.976, 23.98, 24.0),
)


def framerate_equal(source, check):
    if source == check:
        return True

    source = float(source)
    check = float(check)
    if source == check:
        return True

    for equal_fps_tuple in FPS_EQUALITY:
        if check in equal_fps_tuple and source in equal_fps_tuple:
            return True

    return False


def compute_score(matches, subtitle, video, hearing_impaired=None):
    """Compute the score of the `subtitle` against the `video` with `hearing_impaired` preference.
    
    patch: 
        - remove upper bounds of score
        - re-add matches argument and remove get_matches from here

    :func:`compute_score` uses the :meth:`Subtitle.get_matches <subliminal.subtitle.Subtitle.get_matches>` method and
    applies the scores (either from :data:`episode_scores` or :data:`movie_scores`) after some processing.

    :param subtitle: the subtitle to compute the score of.
    :type subtitle: :class:`~subliminal.subtitle.Subtitle`
    :param video: the video to compute the score against.
    :type video: :class:`~subliminal.video.Video`
    :param bool hearing_impaired: hearing impaired preference.
    :return: score of the subtitle.
    :rtype: int

    """
    logger.info('%r: Computing score for video %r with %r', subtitle, video, dict(hearing_impaired=hearing_impaired))

    # get the scores dict
    scores = get_scores(video)
    # logger.debug('Using scores %r', scores)

    is_episode = isinstance(video, Episode)
    is_movie = isinstance(video, Movie)

    episode_hash_valid_if = {"series", "season", "episode", "format"}
    movie_hash_valid_if = {"video_codec", "format"}

    # on hash match, discard everything else
    if subtitle.hash_verifiable:
        if 'hash' in matches:
            # hash is error-prone, try to fix that
            hash_valid_if = episode_hash_valid_if if is_episode else movie_hash_valid_if

            # don't validate hashes of specials, as season and episode tend to be wrong
            if is_movie or not video.is_special:
                if hash_valid_if <= set(matches):
                    # series, season and episode matched, hash is valid
                    logger.debug('%r: Using valid hash, as %s are correct (%r) and (%r)', subtitle, hash_valid_if, matches,
                                 video)
                    matches &= {'hash'}
                else:
                    # no match, invalidate hash
                    logger.debug('%r: Ignoring hash as other matches are wrong (missing: %r) and (%r)', subtitle,
                                 hash_valid_if - matches, video)
                    matches -= {"hash"}
    elif 'hash' in matches:
        logger.debug('%r: Hash not verifiable for this provider. Keeping it', subtitle)
        matches &= {'hash'}

    # handle equivalent matches
    if is_episode:
        if 'title' in matches:
            logger.debug('Adding title match equivalent')
            matches.add('episode')
        if 'series_imdb_id' in matches:
            logger.debug('Adding series_imdb_id match equivalent')
            matches |= {'series', 'year'}
        if 'imdb_id' in matches:
            logger.debug('Adding imdb_id match equivalents')
            matches |= {'series', 'year', 'season', 'episode'}
        if 'tvdb_id' in matches:
            logger.debug('Adding tvdb_id match equivalents')
            matches |= {'series', 'year', 'season', 'episode', 'title'}
        if 'series_tvdb_id' in matches:
            logger.debug('Adding series_tvdb_id match equivalents')
            matches |= {'series', 'year'}

        # specials
        if video.is_special and 'title' in matches and 'series' in matches \
                and 'year' in matches:
            logger.debug('Adding special title match equivalent')
            matches |= {'season', 'episode'}

    elif is_movie:
        if 'imdb_id' in matches:
            logger.debug('Adding imdb_id match equivalents')
            matches |= {'title', 'year'}

    # handle hearing impaired
    if hearing_impaired is not None and subtitle.hearing_impaired == hearing_impaired:
        logger.debug('Matched hearing_impaired')
        matches.add('hearing_impaired')

    # compute the score
    score = sum((scores.get(match, 0) for match in matches))
    logger.info('%r: Computed score %r with final matches %r', subtitle, score, matches)

    return score
