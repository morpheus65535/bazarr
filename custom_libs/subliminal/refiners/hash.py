# -*- coding: utf-8 -*-
import logging

from ..extensions import provider_manager, default_providers
from ..utils import hash_napiprojekt, hash_opensubtitles, hash_shooter, hash_thesubdb

logger = logging.getLogger(__name__)

hash_functions = {
    'napiprojekt': hash_napiprojekt,
    'opensubtitles': hash_opensubtitles,
    'opensubtitlesvip': hash_opensubtitles,
    'shooter': hash_shooter,
    'thesubdb': hash_thesubdb
}


def refine(video, providers=None, languages=None, **kwargs):
    """Refine a video computing required hashes for the given providers.

    The following :class:`~subliminal.video.Video` attribute can be found:

      * :attr:`~subliminal.video.Video.hashes`

    """
    if video.size <= 10485760:
        logger.warning('Size is lower than 10MB: hashes not computed')
        return

    logger.debug('Computing hashes for %r', video.name)
    for name in providers or default_providers:
        provider = provider_manager[name].plugin
        if name not in hash_functions:
            continue

        if not provider.check_types(video):
            continue

        if languages and not provider.check_languages(languages):
            continue

        video.hashes[name] = hash_functions[name](video.name)

    logger.debug('Computed hashes %r', video.hashes)
