# coding=utf-8
import logging
import os
import pickle
from typing import Literal, TypedDict, cast

from app.config import settings
from app.database import TableEpisodes, TableMovies, database, update, select, get_subtitles
from languages.custom_lang import Alpha3LanguageInfo, CustomLanguage, DetectedLanguage, LanguageInfo
from languages.get_languages import language_from_alpha3, alpha3_from_alpha2
from utilities.path_mappings import path_mappings

from knowit.api import know, KnowitException


class MediaTrack(DetectedLanguage, total=False):
    id: int | str
    forced: bool
    hearing_impaired: bool
    format: str
    codec: str | list[str]


class KnowitMetadata(TypedDict, total=False):
    audio: list[MediaTrack]
    subtitle: list[MediaTrack]
    video: list[dict[str, object]]
    container: str


class VideoMetadata(TypedDict):
    ffprobe: KnowitMetadata
    mediainfo: KnowitMetadata
    file_id: int | None
    file_size: int


class AudioReference(TypedDict):
    stream: str
    name: str
    language: str | None


class EmbeddedSubtitleReference(AudioReference):
    forced: bool
    hearing_impaired: bool


class ExternalSubtitleReference(TypedDict):
    name: str
    path: str | None
    language: str | None
    forced: bool
    hearing_impaired: bool


class SyncReferences(TypedDict):
    audio_tracks: list[AudioReference]
    embedded_subtitles_tracks: list[EmbeddedSubtitleReference]
    external_subtitles_tracks: list[ExternalSubtitleReference]


# Preserve the list format used by subtitle indexers: ID, language, forced, HI, codec.
EmbeddedSubtitle = list[str | int | bool | None]


def _handle_alpha3(detected_language: DetectedLanguage) -> str | None:
    """
    Resolve the ISO 639-2 (alpha-3) language code for a detected embedded
    language, taking custom language definitions into account.

    The language entry of the detected language is inspected first: if it is
    an ``Alpha3LanguageInfo`` instance its alpha-3 code is used directly, and
    if it is a plain string that maps to a known alpha-3 language it is
    accepted as is. Otherwise no alpha-3 code is assumed. The resulting code
    is then matched against the registered custom languages by their official
    alpha-3 code. When a custom language matches and it can be confirmed
    either through the language info itself or through the ffprobe metadata
    of the detected language, the custom language's own alpha-3 code is
    returned instead of the official one. In all other cases the originally
    resolved alpha-3 code is returned.

    :param detected_language: Mapping describing a language detected in an
        embedded media stream, including the language entry and any
        ffprobe-derived metadata.
    :return: The alpha-3 code of the matched custom language if one is
        found, otherwise the alpha-3 code resolved from the detected
        language, or ``None`` if no valid alpha-3 code could be determined.
    """
    language = detected_language.get("language")
    if isinstance(language, Alpha3LanguageInfo):
        alpha3 = language.alpha3
    elif isinstance(language, str) and language_from_alpha3(language) is not None:
        alpha3 = language
    else:
        alpha3 = None
    custom = CustomLanguage.from_value(alpha3, "official_alpha3")

    if not custom:
        return alpha3

    found = isinstance(language, LanguageInfo) and custom.language_found(language)
    if not found:
        found = custom.ffprobe_found(detected_language)

    if found:
        logging.debug("Custom embedded language found: %s", custom.name)
        return custom.alpha3

    return alpha3


def embedded_subs_reader(file: str, file_size: int, episode_file_id: int | None = None,
                         movie_file_id: int | None = None, use_cache: bool = True) -> list[EmbeddedSubtitle]:
    """
    Read embedded subtitle tracks from a video file's metadata.

    Parses the video metadata (via ffprobe or mediainfo, optionally using
    the cache) and extracts the embedded subtitle tracks found in it.
    Commentary tracks are skipped, and tracks without a defined language
    are assigned the configured default language for undefined embedded
    subtitles when one is set; otherwise they are ignored. Each resulting
    entry describes a single subtitle track with its track identifier,
    language, forced flag, hearing impaired flag and codec.

    :param file: Path to the video file whose metadata should be parsed.
    :param file_size: Size of the video file in bytes, used for cache
        validation.
    :param episode_file_id: Identifier of the episode file in the
        database, if the video belongs to a series.
    :param movie_file_id: Identifier of the movie file in the database,
        if the video is a movie.
    :param use_cache: Whether cached metadata may be used instead of
        re-parsing the file.
    :return: List of embedded subtitle entries, each containing the track
        id, language, forced flag, hearing impaired flag and codec. An
        empty list is returned when no metadata or no subtitle tracks
        are available.
    """
    data = parse_video_metadata(file, file_size, episode_file_id, movie_file_id, use_cache=use_cache)
    und_default_language = alpha3_from_alpha2(settings.general.default_und_embedded_subtitles_lang)

    subtitles_list: list[EmbeddedSubtitle] = []

    if not data:
        return subtitles_list

    cache_provider: Literal['ffprobe', 'mediainfo'] | None = None
    if "ffprobe" in data and data["ffprobe"] and "subtitle" in data["ffprobe"]:
        cache_provider = 'ffprobe'
    elif 'mediainfo' in data and data["mediainfo"] and "subtitle" in data["mediainfo"]:
        cache_provider = 'mediainfo'

    if cache_provider:
        for detected_language in data[cache_provider].get("subtitle", []):
            # Avoid commentary subtitles
            track_id = detected_language.get("id")
            name = detected_language.get("name", "").lower()
            if "commentary" in name:
                logging.debug(f"Ignoring commentary subtitle: {name}")
                continue

            if "language" not in detected_language:
                language = None
            else:
                language = _handle_alpha3(detected_language)

            if not language and und_default_language:
                logging.debug(f"Undefined language embedded subtitles track treated as {language}")
                language = und_default_language

            if not language:
                continue

            forced = detected_language.get("forced", False)
            hearing_impaired = detected_language.get("hearing_impaired", False)
            codec = detected_language.get("format")  # or None
            subtitles_list.append([track_id, language, forced, hearing_impaired, codec])

    return subtitles_list


def embedded_audio_reader(file: str, file_size: int, episode_file_id: int | None = None,
                          movie_file_id: int | None = None, use_cache: bool = True) -> list[str | None]:
    """
    Read the audio track languages embedded in a video file.

    The function retrieves the video metadata (using cached data when
    allowed), picks the first available metadata provider that exposes
    audio stream information (``ffprobe`` is preferred over ``mediainfo``),
    and then converts every detected audio track language into a language
    name. Tracks without a ``language`` key are represented by ``None``,
    tracks whose language value is ``None`` or cannot be converted to an
    alpha3 code are skipped, and duplicate languages are reported only
    once. An empty list is returned when no metadata could be obtained.

    :param file: Path to the video file whose audio tracks should be
        inspected.
    :param file_size: Size of the video file in bytes, used for metadata
        caching and validation.
    :param episode_file_id: Identifier of the episode file in the
        database, if the file belongs to a series episode.
    :param movie_file_id: Identifier of the movie file in the database,
        if the file belongs to a movie.
    :param use_cache: Whether previously cached metadata may be reused
        instead of probing the file again.
    :return: List of detected audio track languages, where ``None``
        denotes a track without any language information.
    """
    data = parse_video_metadata(file, file_size, episode_file_id, movie_file_id, use_cache=use_cache)

    audio_list: list[str | None] = []

    if not data:
        return audio_list

    cache_provider: Literal['ffprobe', 'mediainfo'] | None = None
    if "ffprobe" in data and data["ffprobe"] and "audio" in data["ffprobe"]:
        cache_provider = 'ffprobe'
    elif 'mediainfo' in data and data["mediainfo"] and "audio" in data["mediainfo"]:
        cache_provider = 'mediainfo'

    if cache_provider:
        for detected_language in data[cache_provider].get("audio", []):
            if "language" not in detected_language:
                audio_list.append(None)
                continue

            if detected_language['language'] is None:
                logging.error(f"Cannot identify audio track language for this file: {file}. Value detected is "
                              f"{detected_language['language']}.")
                continue

            alpha3 = _handle_alpha3(detected_language)
            if alpha3 is None:
                continue
            language = language_from_alpha3(alpha3)

            if language not in audio_list:
                audio_list.append(language)

    return audio_list


def subtitles_sync_references(subtitles_path: str, sonarr_episode_id: int | None = None,
                              radarr_movie_id: int | None = None) -> SyncReferences:
    """
    Collect reference tracks that can be used to synchronize a subtitles file.

    Looks up the media file associated with the given Sonarr episode or Radarr
    movie in the database, maps its path to the local filesystem and reads its
    cached video metadata (from ffprobe or mediainfo, in that order of
    preference). From that metadata it builds a list of audio tracks and a list
    of embedded text-based subtitles tracks (bitmap-based subtitles such as
    DVD or PGS are skipped, as are tracks whose language cannot be resolved).
    It then adds the external subtitles files known for the media item,
    excluding the subtitles file that is itself going to be synced. If no
    identifier is provided, the media item cannot be found, the path cannot
    be mapped or no metadata is available, empty lists are returned for every
    category.

    :param subtitles_path: Path of the subtitles file that is going to be
        synced; it is excluded from the external subtitles references.
    :param sonarr_episode_id: Sonarr identifier of the episode the subtitles
        belong to. Takes precedence over ``radarr_movie_id`` when both are
        given.
    :param radarr_movie_id: Radarr identifier of the movie the subtitles
        belong to. Only used when ``sonarr_episode_id`` is not provided.
    :return: A mapping with the keys ``audio_tracks``,
        ``embedded_subtitles_tracks`` and ``external_subtitles_tracks``, each
        holding a list of dictionaries describing the corresponding reference
        tracks (stream selector or path, name, language and, for subtitles,
        forced and hearing-impaired flags).
    """
    references_dict: SyncReferences = {'audio_tracks': [], 'embedded_subtitles_tracks': [], 'external_subtitles_tracks': []}
    data = None

    if sonarr_episode_id:
        media_data = database.execute(
            select(TableEpisodes.path, TableEpisodes.file_size, TableEpisodes.episode_file_id)
            .where(TableEpisodes.sonarrEpisodeId == sonarr_episode_id)) \
            .first()

        if not media_data:
            return references_dict

        mapped_path = path_mappings.path_replace(media_data.path)
        if mapped_path is None:
            return references_dict

        data = parse_video_metadata(mapped_path, media_data.file_size, media_data.episode_file_id, None,
                                    use_cache=True)
    elif radarr_movie_id:
        media_data = database.execute(
            select(TableMovies.path, TableMovies.file_size, TableMovies.movie_file_id)
            .where(TableMovies.radarrId == radarr_movie_id)) \
            .first()

        if not media_data:
            return references_dict

        mapped_path = path_mappings.path_replace_movie(media_data.path)
        if mapped_path is None:
            return references_dict

        data = parse_video_metadata(mapped_path, media_data.file_size, None, media_data.movie_file_id,
                                    use_cache=True)

    if not data:
        return references_dict

    cache_provider: Literal['ffprobe', 'mediainfo'] | None = None
    if "ffprobe" in data and data["ffprobe"]:
        cache_provider = 'ffprobe'
    elif 'mediainfo' in data and data["mediainfo"]:
        cache_provider = 'mediainfo'

    if cache_provider:
        if 'audio' in data[cache_provider]:
            track_id = 0
            for detected_language in data[cache_provider].get("audio", []):
                name = detected_language.get("name", "").replace("(", "").replace(")", "")

                if "language" not in detected_language:
                    language = 'Undefined'
                else:
                    alpha3 = _handle_alpha3(detected_language)
                    if alpha3 is None:
                        track_id += 1
                        continue
                    language = language_from_alpha3(alpha3)

                references_dict['audio_tracks'].append({'stream': f'a:{track_id}', 'name': name, 'language': language})

                track_id += 1

        if 'subtitle' in data[cache_provider]:
            track_id = 0
            bitmap_subs = ['dvd', 'pgs']
            for detected_language in data[cache_provider].get("subtitle", []):
                if any([x in detected_language.get("name", "").lower() for x in bitmap_subs]):
                    # skipping bitmap based subtitles
                    track_id += 1
                    continue

                name = detected_language.get("name", "").replace("(", "").replace(")", "")

                if "language" not in detected_language:
                    language = 'Undefined'
                else:
                    alpha3 = _handle_alpha3(detected_language)
                    if alpha3 is None:
                        track_id += 1
                        continue
                    language = language_from_alpha3(alpha3)

                forced = detected_language.get("forced", False)
                hearing_impaired = detected_language.get("hearing_impaired", False)

                references_dict['embedded_subtitles_tracks'].append(
                    {'stream': f's:{track_id}', 'name': name, 'language': language,  'forced': forced,
                     'hearing_impaired': hearing_impaired}
                )

                track_id += 1

        try:
            if sonarr_episode_id:
                parsed_subtitles = get_subtitles(sonarr_episode_id=sonarr_episode_id)
            elif radarr_movie_id:
                parsed_subtitles = get_subtitles(radarr_id=radarr_movie_id)
            else:
                parsed_subtitles = []
        except ValueError:
            pass
        else:
            for subtitles in parsed_subtitles:
                if subtitles['path'] and subtitles['path'] != subtitles_path:
                    references_dict['external_subtitles_tracks'].append(cast(ExternalSubtitleReference, {
                        'name': os.path.basename(subtitles['path']),
                        'path': path_mappings.path_replace(subtitles['path']) if sonarr_episode_id else
                        path_mappings.path_replace_reverse_movie(subtitles['path']),
                        'language': subtitles['name'],
                        'forced': subtitles['forced'],
                        'hearing_impaired': subtitles['hi'],
                    }))
                else:
                    # excluding subtitles that is going to be synced from the external subtitles list
                    continue

    return references_dict


def parse_video_metadata(file: str, file_size: int, episode_file_id: int | None = None,
                         movie_file_id: int | None = None, use_cache: bool = True) -> VideoMetadata | None:
    """
    Parse the metadata of a video file using the configured embedded
    subtitles parser (ffprobe or mediainfo).

    When caching is enabled, the function first looks up a previously
    pickled metadata entry stored in the database for the given episode or
    movie file. The cached value is reused only if its file size and file
    id match the provided ones and it contains data for the currently
    selected parser. Otherwise, the file is analyzed again.

    If STRM support is enabled and the given file is a ``.strm`` file, its
    content is read and used as the actual video path (typically a stream
    URL). Local paths that do not exist are reported and skipped.

    The analysis is delegated to the ``knowit`` library with the
    appropriate provider. On success, the resulting metadata is pickled
    and written back to the database as the new cache value for the
    corresponding episode or movie file.

    :param file: Path to the video file (or ``.strm`` file) to analyze.
    :param file_size: Size of the video file in bytes, used to validate
        the cache.
    :param episode_file_id: Identifier of the episode file in the
        database, if the video belongs to an episode.
    :param movie_file_id: Identifier of the movie file in the database,
        if the video belongs to a movie.
    :param use_cache: Whether to try to reuse the cached metadata stored
        in the database before analyzing the file.
    :return: The parsed video metadata, or ``None`` if the file cannot be
        found, cannot be analyzed, or no parser binary is available.
    """

    # Define default data keys value
    data: VideoMetadata = {
        "ffprobe": {},
        "mediainfo": {},
        "file_id": episode_file_id or movie_file_id,
        "file_size": file_size,
    }

    embedded_subs_parser = settings.general.embedded_subtitles_parser

    if use_cache:
        # Get the actual cache value form database
        if episode_file_id:
            cache_key = database.execute(
                select(TableEpisodes.ffprobe_cache)
                .where(TableEpisodes.episode_file_id == episode_file_id)) \
                .first()
        elif movie_file_id:
            cache_key = database.execute(
                select(TableMovies.ffprobe_cache)
                .where(TableMovies.movie_file_id == movie_file_id)) \
                .first()
        else:
            cache_key = None

        # check if we have a value for that cache key
        try:
            # Unpickle ffprobe cache
            if cache_key is None:
                raise ValueError("No video metadata cache found")
            cached_value: VideoMetadata = pickle.loads(cache_key.ffprobe_cache)
        except Exception:
            # No cached value available, we'll parse the file
            pass
        else:
            # Check if file size and file id matches and if so, we return the cached value if available for the
            # desired parser
            if cached_value is not None and cached_value['file_size'] == file_size and cached_value['file_id'] in [episode_file_id, movie_file_id]:
                if embedded_subs_parser in cached_value and cached_value[embedded_subs_parser]:
                    return cached_value
                else:
                    # no valid cache
                    pass
            else:
                # cache must be renewed
                pass

    # if not, we retrieve the metadata from the file
    from utilities.binaries import get_binary

    ffprobe_path = mediainfo_path = None
    if embedded_subs_parser == 'ffprobe':
        ffprobe_path = get_binary("ffprobe")
    elif embedded_subs_parser == 'mediainfo':
        mediainfo_path = get_binary("mediainfo")

    video_path = file
    if settings.general.enable_strm_support and file.lower().endswith('.strm') and os.path.exists(file):
        try:
            with open(file, 'r') as f:
                content = f.read().strip()
                if content:
                    video_path = content
                    logging.debug(f"Stream URL extracted from .strm file: {video_path}")
        except Exception:
            logging.exception(f"Failed to read content of .strm file: {file}")

    # see if file exists (perhaps offline)
    if not video_path.lower().startswith('http') and not os.path.exists(video_path):
        logging.error(f'Video file "{video_path}" cannot be found for analysis')
        return None

    # if we have ffprobe available
    if ffprobe_path:
        try:
            data["ffprobe"] = cast(KnowitMetadata, know(video_path=video_path,
                                                     context={"provider": "ffmpeg", "ffmpeg": ffprobe_path}))
        except KnowitException as e:
            logging.error(f"BAZARR ffprobe cannot analyze this video file {file}. Could it be corrupted? {e}")
            return None
    # or if we have mediainfo available
    elif mediainfo_path:
        try:
            data["mediainfo"] = cast(KnowitMetadata, know(video_path=video_path,
                                                       context={"provider": "mediainfo", "mediainfo": mediainfo_path}))
        except KnowitException as e:
            logging.error(f"BAZARR mediainfo cannot analyze this video file {file}. Could it be corrupted? {e}")
            return None
    # else, we warn user of missing binary
    else:
        logging.error("BAZARR require ffmpeg/ffprobe or mediainfo, please install it and make sure to choose it in "
                      "Settings-->Subtitles.")
        return None

    # we write to db the result and return the newly cached ffprobe dict
    if episode_file_id:
        database.execute(
            update(TableEpisodes)
            .values(ffprobe_cache=pickle.dumps(data, pickle.HIGHEST_PROTOCOL))
            .where(TableEpisodes.episode_file_id == episode_file_id))
    elif movie_file_id:
        database.execute(
            update(TableMovies)
            .values(ffprobe_cache=pickle.dumps(data, pickle.HIGHEST_PROTOCOL))
            .where(TableMovies.movie_file_id == movie_file_id))
    return data
