# coding=utf-8

import os
import shlex
import sys
import logging

from app.config import settings


def pp_replace(pp_command: str, episode: str, subtitles: str, language: str | None, language_code2: str | None,
               language_code3: str | None, episode_language: str | None, episode_language_code2: str | None,
               episode_language_code3: str | None, score: float, subtitle_id: object, provider: str,
               uploader: str | None, release_info: object, series_id: int | str | None,
               episode_id: int | str | None) -> list[str]:
    """
    Build the argument list for a post-processing command by substituting
    template placeholders with concrete values.

    The command string is tokenized using shell-like splitting (POSIX rules
    on non-Windows systems, non-POSIX rules on Windows). Each token is then
    stripped of surrounding double quotes. Tokens that consist entirely of a
    placeholder of the form ``{{name}}`` are replaced with the corresponding
    value derived from the supplied parameters; placeholders that are unknown
    or resolve to an empty value are dropped from the result. All other tokens
    are kept verbatim.

    Supported placeholders include the episode directory, full episode path,
    episode file name without extension, subtitles path, subtitle language
    name and two/three-letter codes (including variants with ``:`` replaced
    by ``.``), episode language name and codes, score, subtitle identifier,
    provider, uploader, release information, series identifier and episode
    identifier. Values are converted to strings before substitution.

    :param pp_command: Post-processing command string containing optional
        ``{{...}}`` placeholders to be substituted.
    :param episode: Path to the episode media file.
    :param subtitles: Path to the subtitles file.
    :param language: Human-readable name of the subtitles language.
    :param language_code2: Two-letter code of the subtitles language.
    :param language_code3: Three-letter code of the subtitles language.
    :param episode_language: Human-readable name of the episode audio
        language.
    :param episode_language_code2: Two-letter code of the episode audio
        language.
    :param episode_language_code3: Three-letter code of the episode audio
        language.
    :param score: Matching score of the downloaded subtitles.
    :param subtitle_id: Provider-specific identifier of the subtitles.
    :param provider: Name of the subtitles provider.
    :param uploader: Name of the subtitles uploader.
    :param release_info: Release information associated with the subtitles.
    :param series_id: Identifier of the series the episode belongs to.
    :param episode_id: Identifier of the episode.
    :return: List of command arguments with placeholders replaced by their
        resolved values, suitable for passing to a process launcher.
    """
    # Provider IDs and release details are opaque values used only for string substitution.
    values_matches = {
        '{{directory}}': os.path.dirname(episode),
        '{{episode}}': episode,
        '{{episode_name}}': os.path.splitext(os.path.basename(episode))[0],
        '{{subtitles}}': str(subtitles),
        '{{subtitles_language}}': str(language),
        '{{subtitles_language_code2}}': str(language_code2),
        '{{subtitles_language_code3}}': str(language_code3),
        '{{subtitles_language_code2_dot}}': str(language_code2).replace(':', '.'),
        '{{subtitles_language_code3_dot}}': str(language_code3).replace(':', '.'),
        '{{episode_language}}': str(episode_language),
        '{{episode_language_code2}}': str(episode_language_code2),
        '{{episode_language_code3}}': str(episode_language_code3),
        '{{score}}': str(score),
        '{{subtitle_id}}': str(subtitle_id),
        '{{provider}}': str(provider),
        '{{uploader}}': str(uploader),
        '{{release_info}}': str(release_info),
        '{{series_id}}': str(series_id),
        '{{episode_id}}': str(episode_id)
    }

    args = shlex.split(pp_command, posix=False if os.name == 'nt' else True)

    pp_args = []
    for arg in args:
        arg = arg.strip('"')
        if arg.startswith('{{') and arg.endswith('}}'):
            matched_value = values_matches.get(arg)
            if matched_value:
                pp_args.append(matched_value)
        else:
            pp_args.append(arg)

    return pp_args


def set_chmod(subtitles_path: str) -> None:
    """
    Apply the configured file permission mode to a subtitles file.

    The permission mode is read from the application settings and is only
    applied when running on a non-Windows platform and when permission
    changing is enabled in the general settings. If these conditions are
    not met, the function does nothing.

    :param subtitles_path: Path to the subtitles file whose permissions
        should be updated.
    :return: None
    """
    # apply chmod if required
    chmod = int(settings.general.chmod, 8) if not sys.platform.startswith(
        'win') and settings.general.chmod_enabled else None
    if chmod:
        logging.debug(f"BAZARR setting permission to {chmod} on {subtitles_path} after custom post-processing.")
        os.chmod(subtitles_path, chmod)
