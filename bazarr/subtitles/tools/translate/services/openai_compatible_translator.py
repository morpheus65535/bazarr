# coding=utf-8

import json
import logging
import os
import re
from urllib.parse import urlsplit, urlunsplit

import pysubs2
import requests
from retry.api import retry

from app.config import settings
from app.jobs_queue import jobs_queue
from languages.get_languages import language_from_alpha2, language_from_alpha3
from radarr.history import history_log_movie
from sonarr.history import history_log
from ..core.translator_utils import add_translator_info, create_process_result

logger = logging.getLogger(__name__)


class InvalidTranslationResponseError(RuntimeError):
    pass


class CueIdentityMismatchError(InvalidTranslationResponseError):
    def __init__(self, expected_ids, actual_ids, duplicate_ids):
        missing = sorted(expected_ids - actual_ids)
        unexpected = sorted(actual_ids - expected_ids)
        details = []
        if missing:
            details.append(f'missing IDs {missing}')
        if unexpected:
            details.append(f'unexpected IDs {unexpected}')
        if duplicate_ids:
            details.append(f'duplicate IDs {sorted(duplicate_ids)}')
        super().__init__('Translator returned an invalid cue mapping: ' + ', '.join(details))


def _chat_completions_url(base_url):
    parsed_url = urlsplit(base_url.strip())
    path = parsed_url.path.rstrip('/')
    if path.endswith('/chat/completions'):
        endpoint_path = path
    elif not path:
        endpoint_path = '/v1/chat/completions'
    else:
        endpoint_path = f'{path}/chat/completions'
    return urlunsplit(parsed_url._replace(path=endpoint_path))


def _request_translation(cues, base_url, model, api_key, timeout, from_lang, to_lang, retry_instruction=None):
    base_url = base_url.strip()
    model = model.strip()
    if not base_url or not model:
        raise ValueError('OpenAI-compatible translator requires a base URL and model')
    url = _chat_completions_url(base_url)

    target = language_from_alpha3(to_lang)
    if not target:
        raise ValueError(f'Unknown target language code: {to_lang}')
    cue_count = len(cues)
    cue_label = 'cue' if cue_count == 1 else 'cues'
    expected_ids = set(range(1, cue_count + 1))
    system_prompt = (
        f'Translate each subtitle cue from {language_from_alpha2(from_lang)} to {target} independently. '
        f'The input contains exactly {cue_count} {cue_label}, each with a numeric ID. Return only a JSON array '
        'of objects with exactly these fields: "id" (the unchanged input ID) and "text" (the translation). '
        'Return every input ID exactly once; do not combine, split, omit, duplicate, or reorder cues. '
        'Preserve meaning, names, and line breaks within each cue. Return no commentary.'
    )
    if retry_instruction:
        system_prompt += f' {retry_instruction}'
    cue_payload = [{'id': index, 'text': cue} for index, cue in enumerate(cues, start=1)]
    payload = {
        'model': model,
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': json.dumps(cue_payload, ensure_ascii=False)},
        ],
        'temperature': 0.1,
        'max_tokens': max(512, len(cues) * 128),
        'chat_template_kwargs': {'enable_thinking': False},
    }
    headers = {'Content-Type': 'application/json'}
    token = (api_key or '').strip()
    if token:
        headers['Authorization'] = f'Bearer {token}'
    response = requests.post(url, json=payload, headers=headers, timeout=int(timeout))
    response.raise_for_status()
    result = response.json()['choices'][0]
    content = result.get('message', {}).get('content')
    if result.get('finish_reason') != 'stop' or not content:
        raise InvalidTranslationResponseError('Translator returned an incomplete response')
    match = re.search(r'\[[\s\S]*\]', content)
    if not match:
        raise InvalidTranslationResponseError('Translator response did not contain a JSON array')
    try:
        translated = json.loads(match.group())
    except json.JSONDecodeError as error:
        raise InvalidTranslationResponseError('Translator response contained invalid JSON') from error
    if not isinstance(translated, list):
        raise InvalidTranslationResponseError('Translator response must be a JSON array')

    translations_by_id = {}
    duplicate_ids = []
    for item in translated:
        if not isinstance(item, dict) or type(item.get('id')) is not int or not isinstance(item.get('text'), str):
            raise InvalidTranslationResponseError('Each translated cue must contain an integer id and string text')
        cue_id = item['id']
        if cue_id in translations_by_id:
            duplicate_ids.append(cue_id)
        else:
            translations_by_id[cue_id] = item['text']

    actual_ids = set(translations_by_id)
    if actual_ids != expected_ids or duplicate_ids:
        raise CueIdentityMismatchError(expected_ids, actual_ids, duplicate_ids)
    return [translations_by_id[index] for index in range(1, cue_count + 1)]


def test_openai_compatible_connection(base_url, model, api_key='', timeout=30):
    """Send one small translation request to verify the configured endpoint and model."""
    if not base_url or not base_url.strip():
        raise ValueError('Enter an API base URL before testing the connection')
    if not model or not model.strip():
        raise ValueError('Enter a model name before testing the connection')

    try:
        result = _request_translation(
            cues=['Hello'],
            base_url=base_url,
            model=model,
            api_key=api_key,
            timeout=timeout,
            from_lang='en',
            to_lang='fra')
    except requests.exceptions.HTTPError as error:
        status_code = error.response.status_code if error.response is not None else None
        if status_code in (401, 403):
            raise RuntimeError('Authentication failed; check the API key') from None
        if status_code is not None:
            raise RuntimeError(f'The endpoint returned HTTP {status_code}') from None
        raise RuntimeError('The endpoint rejected the test request') from None
    except json.JSONDecodeError:
        raise RuntimeError('The endpoint returned an invalid Chat Completions response') from None
    except requests.exceptions.RequestException:
        raise RuntimeError('Could not reach the endpoint; check its URL and timeout') from None
    except (KeyError, IndexError, TypeError, ValueError):
        raise RuntimeError('The endpoint returned an invalid Chat Completions response') from None

    return result[0]


class OpenAICompatibleTranslatorService:
    """Translate subtitle cues through an OpenAI Chat Completions-compatible endpoint."""

    def __init__(self, source_srt_file, dest_srt_file, to_lang, media_type, sonarr_series_id,
                 sonarr_episode_id, radarr_id, forced, hi, video_path, from_lang, orig_to_lang, **kwargs):
        self.source_srt_file = source_srt_file
        self.dest_srt_file = dest_srt_file
        self.to_lang = to_lang
        self.media_type = media_type
        self.sonarr_series_id = sonarr_series_id
        self.sonarr_episode_id = sonarr_episode_id
        self.radarr_id = radarr_id
        self.forced = forced
        self.hi = hi
        self.video_path = video_path
        self.from_lang = from_lang
        self.orig_to_lang = orig_to_lang

    @staticmethod
    def _setting(name, default):
        return getattr(settings.translator, name, default)

    @retry(exceptions=(requests.exceptions.RequestException,), tries=3, delay=1, backoff=2, jitter=(0, 1))
    def _translate_batch(self, cues):
        request_args = {
            'base_url': self._setting('openai_base_url', ''),
            'model': self._setting('openai_model', ''),
            'api_key': self._setting('openai_api_key', ''),
            'timeout': self._setting('openai_timeout', 180),
            'from_lang': self.from_lang,
            'to_lang': self.to_lang,
        }
        try:
            return _request_translation(cues=cues, **request_args)
        except InvalidTranslationResponseError as error:
            cue_count = len(cues)
            retry_instruction = (
                f'Your previous response was invalid: {error}. Retry the entire input and return only a JSON array '
                'of objects with the original integer IDs and translated text, with every input ID represented '
                'exactly once.'
            )
            logger.warning(
                'Translator returned an invalid response for a batch of %d cues; requesting a correction',
                cue_count,
            )
            try:
                return _request_translation(cues=cues, retry_instruction=retry_instruction, **request_args)
            except InvalidTranslationResponseError:
                pass

            if len(cues) <= 1:
                raise
            midpoint = len(cues) // 2
            logger.warning('Translator still returned an invalid response; retrying as smaller batches')
            return self._translate_batch(cues[:midpoint]) + self._translate_batch(cues[midpoint:])

    def translate(self, job_id=None):
        try:
            subs = pysubs2.load(self.source_srt_file, encoding='utf-8')
            cues = [line.text for line in subs]
            batch_size = max(1, int(self._setting('openai_batch_size', 12)))
            lines = [i for i, cue in enumerate(cues) if cue.strip()]
            jobs_queue.update_job_progress(job_id=job_id, progress_max=len(lines) or 1,
                                           progress_message=self.source_srt_file)
            for start in range(0, len(lines), batch_size):
                indices = lines[start:start + batch_size]
                translated = self._translate_batch([cues[i] for i in indices])
                for index, text in zip(indices, translated):
                    subs[index].text = text
                jobs_queue.update_job_progress(job_id=job_id, progress_value=start + len(indices))
            os.makedirs(os.path.dirname(self.dest_srt_file) or '.', exist_ok=True)
            subs.save(self.dest_srt_file)
            add_translator_info(self.dest_srt_file,
                                f'# Subtitles translated with {self._setting("openai_model", "OpenAI-compatible model")} # ')
            message = (f'{language_from_alpha2(self.from_lang)} subtitles translated to '
                       f'{language_from_alpha3(self.to_lang)} using OpenAI-compatible translator.')
            result = create_process_result(message, self.video_path, self.orig_to_lang, self.forced, self.hi,
                                           self.dest_srt_file, self.media_type)
            if self.media_type == 'episode':
                history_log(action=6, sonarr_series_id=self.sonarr_series_id,
                            sonarr_episode_id=self.sonarr_episode_id, result=result)
            else:
                history_log_movie(action=6, radarr_id=self.radarr_id, result=result)
            jobs_queue.update_job_progress(job_id=job_id, progress_value='max')
            return self.dest_srt_file
        except Exception as e:
            logger.error(f'BAZARR encountered an error during OpenAI-compatible translation for '
                         f'{self.source_srt_file}: {str(e)}')
            jobs_queue.update_job_progress(job_id=job_id,
                                           progress_message=f'OpenAI-compatible translation failed: {str(e)}')
            raise
