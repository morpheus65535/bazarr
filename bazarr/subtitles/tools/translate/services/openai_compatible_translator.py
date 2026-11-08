# coding=utf-8

import json
import logging
import os
import re
import socket
from ipaddress import ip_address, ip_network
from urllib.parse import urljoin, urlsplit, urlunsplit

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

# Blocked even where ipaddress classifies them as private: "this network", link-local (cloud metadata
# on IPv4 and IPv6), and the AWS IPv6 metadata range.
_BLOCKED_NETWORKS = tuple(ip_network(network) for network in (
    '0.0.0.0/8', '169.254.0.0/16', 'fe80::/10', 'fd00:ec2::/32'))


class InvalidTranslationResponseError(RuntimeError):
    pass


class ChatCompletionFormatError(RuntimeError):
    # Not a subclass of InvalidTranslationResponseError: a malformed envelope is not fixed by splitting the batch.
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


def _is_allowed_address(address: str) -> bool:
    """Return whether a resolved IP address may be used as a translator endpoint.

    Loopback and private addresses are allowed because self-hosted models usually run on the LAN.
    Link-local, multicast, unspecified, and carrier-grade NAT addresses are not.

    :param address: IP address string as returned by ``socket.getaddrinfo``.
    :return: ``True`` if the address is allowed.
    """
    ip = ip_address(address)
    if ip.version == 6 and ip.ipv4_mapped:
        ip = ip.ipv4_mapped
    if ip.is_multicast or any(ip in network for network in _BLOCKED_NETWORKS):
        return False
    return ip.is_loopback or ip.is_private or ip.is_global


def _validate_endpoint_url(url: str) -> None:
    """Ensure an endpoint URL uses http(s) and that every address its host resolves to is allowed.

    Hostnames and IP literals are both accepted; ``socket.getaddrinfo`` resolves either one.

    :param url: Absolute URL to validate.
    :raises ValueError: If the URL is unsupported or resolves to a disallowed address.
    """
    parsed_url = urlsplit(url)
    if parsed_url.scheme not in ('http', 'https'):
        raise ValueError('API base URL must start with http:// or https://')
    if not parsed_url.hostname:
        raise ValueError('API base URL must include a host')
    if parsed_url.username is not None or parsed_url.password is not None:
        raise ValueError('API base URL must not include credentials')

    port = parsed_url.port or (443 if parsed_url.scheme == 'https' else 80)
    try:
        addresses = socket.getaddrinfo(parsed_url.hostname, port, type=socket.SOCK_STREAM)
    except socket.gaierror:
        raise ValueError('Could not resolve the API host') from None
    for *_, sockaddr in addresses:
        if not _is_allowed_address(sockaddr[0]):
            raise ValueError('API host resolves to a disallowed address')


def _validate_redirect(response: requests.Response, **kwargs: object) -> requests.Response:
    """Validate the target of a redirect before requests follows it.

    :param response: Response delivered for each hop of the request.
    :return: The unchanged response.
    """
    if response.is_redirect:
        _validate_endpoint_url(urljoin(response.url, response.headers['Location']))
    return response


def _request_translation(cues, base_url, model, api_key, timeout, from_lang, to_lang, retry_instruction=None,
                         capabilities=None):
    base_url = base_url.strip()
    model = model.strip()
    if not base_url or not model:
        raise ValueError('OpenAI-compatible translator requires a base URL and model')
    url = _chat_completions_url(base_url)
    _validate_endpoint_url(url)

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
    }
    if capabilities is None:
        capabilities = {}
    if capabilities.get('chat_template_kwargs', True):
        payload['chat_template_kwargs'] = {'enable_thinking': False}
    headers = {'Content-Type': 'application/json'}
    token = (api_key or '').strip()
    if token:
        headers['Authorization'] = f'Bearer {token}'
    response = requests.post(url, json=payload, headers=headers, timeout=int(timeout),
                             hooks={'response': [_validate_redirect]})
    if response.status_code == 400 and 'chat_template_kwargs' in payload and 'chat_template_kwargs' in response.text:
        # chat_template_kwargs is a vLLM/Ollama extension. Endpoints that validate the request body
        # against the OpenAI schema (Groq, Mistral, OpenAI) reject it, so send the request again without it.
        # The rejection is recorded in ``capabilities`` so later requests skip the failing attempt.
        logger.debug('Translator endpoint rejected chat_template_kwargs; retrying without it')
        capabilities['chat_template_kwargs'] = False
        del payload['chat_template_kwargs']
        response = requests.post(url, json=payload, headers=headers, timeout=int(timeout),
                                 hooks={'response': [_validate_redirect]})
    response.raise_for_status()
    try:
        choice = response.json()['choices'][0]
        finish_reason = choice.get('finish_reason')
        content = choice['message']['content']
    except (KeyError, IndexError, TypeError, AttributeError, ValueError) as error:
        raise ChatCompletionFormatError('Translator response is not a Chat Completions choice') from error
    if finish_reason != 'stop' or not isinstance(content, str) or not content:
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
    except ChatCompletionFormatError:
        raise RuntimeError('The endpoint returned an invalid Chat Completions response') from None
    except InvalidTranslationResponseError as error:
        raise RuntimeError(f'The endpoint returned an unusable translation: {error}') from None
    except requests.exceptions.RequestException:
        raise RuntimeError('Could not reach the endpoint; check its URL and timeout') from None

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
        # Endpoint features learned from earlier batches of this job, so each batch does not re-probe them.
        self._endpoint_capabilities: dict[str, bool] = {}

    @staticmethod
    def _setting(name, default):
        return getattr(settings.translator, name, default)

    @retry(exceptions=(requests.exceptions.RequestException,), tries=3, delay=1, backoff=2, jitter=(0, 1))
    def _request_with_retry(self, cues: list[str], retry_instruction: str | None = None) -> list[str]:
        """Send one translation request, retrying only transient network failures.

        :param cues: Subtitle texts to translate, in order.
        :param retry_instruction: Optional correction appended to the system prompt.
        :return: Translated texts in the same order as ``cues``.
        """
        return _request_translation(
            cues=cues,
            base_url=self._setting('openai_base_url', ''),
            model=self._setting('openai_model', ''),
            api_key=self._setting('openai_api_key', ''),
            timeout=self._setting('openai_timeout', 180),
            from_lang=self.from_lang,
            to_lang=self.to_lang,
            retry_instruction=retry_instruction,
            capabilities=self._endpoint_capabilities,
        )

    def _translate_batch(self, cues: list[str]) -> list[str]:
        """Translate a batch, requesting a correction and then splitting it if the response is invalid.

        Network retries live in ``_request_with_retry`` so that recursive splits do not multiply them.

        :param cues: Subtitle texts to translate, in order.
        :return: Translated texts in the same order as ``cues``.
        """
        try:
            return self._request_with_retry(cues)
        except InvalidTranslationResponseError as error:
            retry_instruction = (
                f'Your previous response was invalid: {error}. Retry the entire input and return only a JSON array '
                'of objects with the original integer IDs and translated text, with every input ID represented '
                'exactly once.'
            )
        logger.warning(
            'Translator returned an invalid response for a batch of %d cues; requesting a correction',
            len(cues),
        )
        try:
            return self._request_with_retry(cues, retry_instruction=retry_instruction)
        except InvalidTranslationResponseError:
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
                                f'# Subtitles translated with '
                                f'{self._setting("openai_model", "OpenAI-compatible model")} # ')
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
