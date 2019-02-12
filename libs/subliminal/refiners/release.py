# -*- coding: utf-8 -*-
import logging
import os

from guessit import guessit

logger = logging.getLogger(__name__)

MOVIE_ATTRIBUTES = {'title': 'title', 'year': 'year', 'format': 'format', 'release_group': 'release_group',
                    'resolution': 'screen_size',  'video_codec': 'video_codec', 'audio_codec': 'audio_codec'}
EPISODE_ATTRIBUTES = {'series': 'title', 'season': 'season', 'episode': 'episode', 'title': 'episode_title',
                      'year': 'year', 'format': 'format', 'release_group': 'release_group', 'resolution': 'screen_size',
                      'video_codec': 'video_codec', 'audio_codec': 'audio_codec'}


def refine(video, release_name=None, release_file=None, extension='release', **kwargs):
    """Refine a video by using the original release name.
    The refiner will first try:
    - Read the file video_name.<extension> seeking for a release name
    - If no release name, it will read the file release file seeking for a release name
    - If no release name, it will use the release_name passed as an argument
    - If no release name, then no change in the video object is made

    When a release name is found, the video object will be enhanced using the guessit properties extracted from it.

    Several :class:`~subliminal.video.Video` attributes can be found:

      * :attr:`~subliminal.video.Video.title`
      * :attr:`~subliminal.video.Video.series`
      * :attr:`~subliminal.video.Video.season`
      * :attr:`~subliminal.video.Video.episode`
      * :attr:`~subliminal.video.Video.year`
      * :attr:`~subliminal.video.Video.format`
      * :attr:`~subliminal.video.Video.release_group`
      * :attr:`~subliminal.video.Video.resolution`
      * :attr:`~subliminal.video.Video.video_codec`
      * :attr:`~subliminal.video.Video.audio_codec`

    :param video: the video to refine.
    :param str release_name: the release name to be used.
    :param str release_file: the release file to be used
    :param str extension: the release file extension.

    """
    logger.debug('Starting release refiner [extension=%s, release_name=%s, release_file=%s]',
                 extension, release_name, release_file)
    dirpath, filename = os.path.split(video.name)
    dirpath = dirpath or '.'
    fileroot, fileext = os.path.splitext(filename)
    release_file = get_release_file(dirpath, fileroot, extension) or release_file
    release_name = get_release_name(release_file) or release_name

    if not release_name:
        logger.debug('No release name for %s', video.name)
        return

    release_path = os.path.join(dirpath, release_name + fileext)
    logger.debug('Guessing using %s', release_path)

    guess = guessit(release_path)
    attributes = MOVIE_ATTRIBUTES if guess.get('type') == 'movie' else EPISODE_ATTRIBUTES
    for key, value in attributes.items():
        old_value = getattr(video, key)
        new_value = guess.get(value)

        if new_value and old_value != new_value:
            setattr(video, key, new_value)
            logger.debug('Attribute %s changed from %s to %s', key, old_value, new_value)


def get_release_file(dirpath, filename, extension):
    """
    Given a `dirpath`, `filename` and `extension`, it returns the release file that should contain the original
    release name.

    Args:
        dirpath: the file base folder
        filename: the file name without extension
        extension: the file extension

    Returns: the release file if the file exists
    """
    release_file = os.path.join(dirpath, filename + '.' + extension)

    # skip if info file doesn't exist
    if os.path.isfile(release_file):
        logger.debug('Found release file %s', release_file)
        return release_file


def get_release_name(release_file):
    """
    Given a `release_file` it will return the release name

    Args:
        release_file: the text file that contains the release name

    Returns: the release name
    """
    if not release_file:
        return

    with open(release_file, 'r') as f:
        release_name = f.read().strip()

    # skip if no release name was found
    if not release_name:
        logger.warning('Release file %s does not contain a release name', release_file)

    return release_name
