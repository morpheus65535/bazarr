# coding=utf-8

import logging
import os

from enzyme import MKV

logger = logging.getLogger(__name__)


def refine(video, embedded_subtitles=True, **kwargs):
    """Refine a video by searching its metadata.
    
    patch: remove embedded subtitle detection

    Several :class:`~subliminal.video.Video` attributes can be found:

      * :attr:`~subliminal.video.Video.resolution`
      * :attr:`~subliminal.video.Video.video_codec`
      * :attr:`~subliminal.video.Video.audio_codec`
      * :attr:`~subliminal.video.Video.subtitle_languages`

    :param bool embedded_subtitles: search for embedded subtitles.

    """
    # skip non existing videos
    if not video.exists:
        return

    # check extensions
    extension = os.path.splitext(video.name)[1]
    if extension == '.mkv':
        with open(video.name, 'rb') as f:
            mkv = MKV(f)

        # main video track
        if mkv.video_tracks:
            video_track = mkv.video_tracks[0]

            # resolution
            if video_track.height in (480, 720, 1080):
                if video_track.interlaced:
                    video.resolution = '%di' % video_track.height
                else:
                    video.resolution = '%dp' % video_track.height
                logger.debug('Found resolution %s', video.resolution)

            # video codec
            if video_track.codec_id == 'V_MPEG4/ISO/AVC':
                video.video_codec = 'h264'
                logger.debug('Found video_codec %s', video.video_codec)
            elif video_track.codec_id == 'V_MPEG4/ISO/SP':
                video.video_codec = 'DivX'
                logger.debug('Found video_codec %s', video.video_codec)
            elif video_track.codec_id == 'V_MPEG4/ISO/ASP':
                video.video_codec = 'XviD'
                logger.debug('Found video_codec %s', video.video_codec)
        else:
            logger.warning('MKV has no video track')

        # main audio track
        if mkv.audio_tracks:
            audio_track = mkv.audio_tracks[0]
            # audio codec
            if audio_track.codec_id == 'A_AC3':
                video.audio_codec = 'AC3'
                logger.debug('Found audio_codec %s', video.audio_codec)
            elif audio_track.codec_id == 'A_DTS':
                video.audio_codec = 'DTS'
                logger.debug('Found audio_codec %s', video.audio_codec)
            elif audio_track.codec_id == 'A_AAC':
                video.audio_codec = 'AAC'
                logger.debug('Found audio_codec %s', video.audio_codec)
        else:
            logger.warning('MKV has no audio track')

    else:
        logger.debug('Unsupported video extension %s', extension)
