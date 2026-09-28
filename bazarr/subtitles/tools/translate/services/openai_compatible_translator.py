# coding=utf-8

import json
import logging
import os
import re

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
        base_url = self._setting('openai_base_url', '').strip().rstrip('/')
        model = self._setting('openai_model', '').strip()
        if not base_url or not model:
            raise ValueError('OpenAI-compatible translator requires a base URL and model')
        if base_url.endswith('/chat/completions'):
            url = base_url
        else:
            url = base_url + '/chat/completions'
        target = language_from_alpha3(self.to_lang)
        if not target:
            raise ValueError(f'Unknown target language code: {self.to_lang}')
        payload = {
            'model': model,
            'messages': [
                {'role': 'system', 'content': (
                    f'Translate subtitle cues from {language_from_alpha2(self.from_lang)} to {target}. '
                    'Return only a JSON array of strings, exactly one translated string for each input cue, '
                    'in the same order. Preserve meaning, names, line breaks where useful, and do not add commentary.'
                )},
                {'role': 'user', 'content': json.dumps(cues, ensure_ascii=False)},
            ],
            'temperature': 0.1,
            'max_tokens': max(512, len(cues) * 128),
            'chat_template_kwargs': {'enable_thinking': False},
        }
        headers = {'Content-Type': 'application/json'}
        token = self._setting('openai_api_key', '').strip()
        if token:
            headers['Authorization'] = f'Bearer {token}'
        response = requests.post(url, json=payload, headers=headers,
                                 timeout=int(self._setting('openai_timeout', 180)))
        response.raise_for_status()
        result = response.json()['choices'][0]
        content = result.get('message', {}).get('content')
        if result.get('finish_reason') != 'stop' or not content:
            raise RuntimeError('Translator returned an incomplete response')
        match = re.search(r'\[[\s\S]*\]', content)
        if not match:
            raise RuntimeError('Translator response did not contain a JSON array')
        translated = json.loads(match.group())
        if len(translated) != len(cues) or not all(isinstance(x, str) for x in translated):
            raise RuntimeError('Translator returned an invalid number or type of subtitle cues')
        return translated

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
