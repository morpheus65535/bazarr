import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from bazarr.subtitles.tools.translate.services import openai_compatible_translator


def _service():
    return openai_compatible_translator.OpenAICompatibleTranslatorService(
        source_srt_file='in.srt', dest_srt_file='out.srt', to_lang='pol', media_type='episode',
        sonarr_series_id=1, sonarr_episode_id=2, radarr_id=None, forced=False, hi=False,
        video_path='video.mkv', from_lang='en', orig_to_lang='pl')


def _settings(mocker):
    for name, value in {'openai_base_url': 'http://127.0.0.1/v1', 'openai_model': 'local-model',
                        'openai_api_key': '', 'openai_timeout': 30}.items():
        mocker.patch.object(openai_compatible_translator.settings.translator, name, value, create=True)


def _response(mocker, content, finish_reason='stop'):
    response = mocker.Mock()
    response.json.return_value = {'choices': [{'finish_reason': finish_reason,
                                               'message': {'content': content}}]}
    return response


def test_openai_compatible_request_and_validation(mocker):
    _settings(mocker)
    post = mocker.patch.object(openai_compatible_translator.requests, 'post',
                               return_value=_response(mocker, '[{"id":1,"text":"Cześć"}]'))
    assert _service()._translate_batch(['Hello']) == ['Cześć']
    assert post.call_args.args[0] == 'http://127.0.0.1/v1/chat/completions'
    payload = post.call_args.kwargs['json']
    assert payload['model'] == 'local-model'
    assert payload['chat_template_kwargs'] == {'enable_thinking': False}
    assert 'exactly 1 cue' in payload['messages'][0]['content']
    assert payload['messages'][1]['content'] == '[{"id": 1, "text": "Hello"}]'


@pytest.mark.parametrize(('base_url', 'expected_url'), [
    ('http://127.0.0.1', 'http://127.0.0.1/v1/chat/completions'),
    ('http://127.0.0.1/v1/', 'http://127.0.0.1/v1/chat/completions'),
    ('http://127.0.0.1/v1/chat/completions', 'http://127.0.0.1/v1/chat/completions'),
])
def test_chat_completions_url_supports_bare_host_version_and_full_endpoint(mocker, base_url, expected_url):
    post = mocker.patch.object(openai_compatible_translator.requests, 'post',
                               return_value=_response(mocker, '[{"id":1,"text":"Bonjour"}]'))

    openai_compatible_translator._request_translation(
        cues=['Hello'], base_url=base_url, model='local-model', api_key='', timeout=30,
        from_lang='en', to_lang='fra')

    assert post.call_args.args[0] == expected_url


def test_rejects_truncated_response(mocker):
    _settings(mocker)
    mocker.patch.object(openai_compatible_translator.requests, 'post',
                        return_value=_response(mocker, '[{"id":1,"text":"Hej"}]', finish_reason='length'))
    with pytest.raises(RuntimeError, match='incomplete'):
        _service()._translate_batch(['Hello'])


def test_mismatched_batch_is_retried_as_smaller_batches(mocker):
    _settings(mocker)
    post = mocker.patch.object(
        openai_compatible_translator.requests,
        'post',
        side_effect=[
            _response(mocker, '[{"id":1,"text":"Merged translation"}]'),
            _response(mocker, '[{"id":1,"text":"Still merged"}]'),
            _response(mocker, '[{"id":1,"text":"Premier"}]'),
            _response(mocker, '[{"id":1,"text":"Deuxième"}]'),
        ],
    )

    result = _service()._translate_batch(['First cue', 'Second cue'])

    assert result == ['Premier', 'Deuxième']
    assert post.call_count == 4
    assert 'exactly these fields' in post.call_args_list[0].kwargs['json']['messages'][0]['content']
    correction_prompt = post.call_args_list[1].kwargs['json']['messages'][0]['content']
    assert 'previous response was invalid' in correction_prompt
    assert 'missing IDs [2]' in correction_prompt


def test_translations_are_mapped_by_cue_id_not_response_order(mocker):
    _settings(mocker)
    mocker.patch.object(
        openai_compatible_translator.requests,
        'post',
        return_value=_response(mocker, '[{"id":2,"text":"Deuxième"},{"id":1,"text":"Premier"}]'),
    )

    assert _service()._translate_batch(['First cue', 'Second cue']) == ['Premier', 'Deuxième']


def test_count_mismatch_reprompts_same_batch_before_accepting_translation(mocker):
    _settings(mocker)
    post = mocker.patch.object(
        openai_compatible_translator.requests,
        'post',
        side_effect=[
            _response(mocker, '[{"id":1,"text":"Only one"}]'),
            _response(mocker, '[{"id":1,"text":"Premier"},{"id":2,"text":"Deuxième"}]'),
        ],
    )

    result = _service()._translate_batch(['First cue', 'Second cue'])

    assert result == ['Premier', 'Deuxième']
    assert post.call_count == 2
    correction_prompt = post.call_args_list[1].kwargs['json']['messages'][0]['content']
    assert 'previous response was invalid' in correction_prompt
    assert 'missing IDs [2]' in correction_prompt


def test_invalid_response_is_reprompted_before_failing(mocker):
    _settings(mocker)
    post = mocker.patch.object(
        openai_compatible_translator.requests,
        'post',
        side_effect=[
            _response(mocker, 'I will translate these cues now.'),
            _response(mocker, '[{"id":1,"text":"Bonjour"}]'),
        ],
    )

    assert _service()._translate_batch(['Hello']) == ['Bonjour']
    assert post.call_count == 2
    assert 'previous response was invalid' in post.call_args_list[1].kwargs['json']['messages'][0]['content']


def test_single_cue_count_mismatch_is_reported(mocker):
    _settings(mocker)
    post = mocker.patch.object(openai_compatible_translator.requests, 'post',
                               return_value=_response(mocker, '[]'))

    with pytest.raises(openai_compatible_translator.CueIdentityMismatchError, match=r'missing IDs \[1\]'):
        _service()._translate_batch(['Hello'])
    assert post.call_count == 2


def test_invalid_json_is_rejected(mocker):
    _settings(mocker)
    mocker.patch.object(openai_compatible_translator.requests, 'post',
                        return_value=_response(mocker, 'not json'))
    with pytest.raises(RuntimeError, match='JSON array'):
        _service()._translate_batch(['Hello'])


def test_connection_test_uses_supplied_settings(mocker):
    response = _response(mocker, '[{"id":1,"text":"Bonjour"}]')
    post = mocker.patch.object(openai_compatible_translator.requests, 'post', return_value=response)

    translation = openai_compatible_translator.test_openai_compatible_connection(
        base_url='http://127.0.0.1/v1', model='local-model', api_key='test-key', timeout=12)

    assert translation == 'Bonjour'
    assert post.call_args.args[0] == 'http://127.0.0.1/v1/chat/completions'
    assert post.call_args.kwargs['timeout'] == 12
    assert post.call_args.kwargs['headers']['Authorization'] == 'Bearer test-key'
    payload = post.call_args.kwargs['json']
    assert payload['model'] == 'local-model'
    assert payload['messages'][1]['content'] == '[{"id": 1, "text": "Hello"}]'


def test_malformed_chat_completion_envelope_is_not_split_or_reprompted(mocker):
    _settings(mocker)
    response = mocker.Mock()
    response.json.return_value = {'choices': [{'finish_reason': 'stop', 'message': None}]}
    post = mocker.patch.object(openai_compatible_translator.requests, 'post', return_value=response)

    with pytest.raises(openai_compatible_translator.ChatCompletionFormatError):
        _service()._translate_batch(['First cue', 'Second cue'])
    assert post.call_count == 1


def test_connection_test_reports_malformed_envelope(mocker):
    response = mocker.Mock()
    response.json.return_value = {'error': {'message': 'model not loaded'}}
    mocker.patch.object(openai_compatible_translator.requests, 'post', return_value=response)

    with pytest.raises(RuntimeError, match='invalid Chat Completions response'):
        openai_compatible_translator.test_openai_compatible_connection(
            base_url='http://127.0.0.1/v1', model='local-model', api_key='', timeout=12)


def test_connection_test_reports_unusable_translation(mocker):
    _settings(mocker)
    mocker.patch.object(openai_compatible_translator.requests, 'post',
                        return_value=_response(mocker, '[{"id":2,"text":"Bonjour"}]'))

    with pytest.raises(RuntimeError, match='unusable translation'):
        openai_compatible_translator.test_openai_compatible_connection(
            base_url='http://127.0.0.1/v1', model='local-model', api_key='', timeout=12)


def test_connection_test_reports_authentication_errors_without_echoing_key(mocker):
    response = mocker.Mock(status_code=401)
    error = openai_compatible_translator.requests.exceptions.HTTPError(response=response)
    mocker.patch.object(openai_compatible_translator.requests, 'post', side_effect=error)

    with pytest.raises(RuntimeError, match='Authentication failed') as raised:
        openai_compatible_translator.test_openai_compatible_connection(
            base_url='http://127.0.0.1/v1', model='local-model', api_key='secret', timeout=12)

    assert 'secret' not in str(raised.value)


@pytest.mark.parametrize('base_url', [
    'http://127.0.0.1:1234/v1',
    'http://192.168.1.10:8000/v1',
    'http://10.0.0.5/v1',
    'http://[::1]:8000/v1',
    'https://203.0.113.10/v1',
])
def test_endpoint_validation_allows_local_private_and_public_addresses(base_url):
    openai_compatible_translator._validate_endpoint_url(base_url)


@pytest.mark.parametrize('base_url', [
    'http://169.254.169.254/latest/meta-data/',
    'http://[fe80::1]/v1',
    'http://[::ffff:169.254.169.254]/v1',
    'http://[fd00:ec2::254]/v1',
    'http://0.0.0.0/v1',
    'http://224.0.0.1/v1',
    'http://[ff02::1]/v1',
    'http://100.100.100.200/v1',
    'file:///etc/passwd',
    'gopher://127.0.0.1/',
    'http://user:secret@127.0.0.1/v1',
    'http:///v1',
])
def test_endpoint_validation_rejects_unsafe_urls(base_url):
    with pytest.raises(ValueError):
        openai_compatible_translator._validate_endpoint_url(base_url)


def test_endpoint_validation_checks_every_resolved_address(mocker):
    mocker.patch.object(openai_compatible_translator.socket, 'getaddrinfo', return_value=[
        (2, 1, 6, '', ('127.0.0.1', 80)),
        (2, 1, 6, '', ('169.254.169.254', 80)),
    ])
    with pytest.raises(ValueError, match='disallowed address'):
        openai_compatible_translator._validate_endpoint_url('http://metadata.internal/v1')


def test_connection_test_rejects_disallowed_endpoint_before_sending(mocker):
    post = mocker.patch.object(openai_compatible_translator.requests, 'post')

    with pytest.raises(ValueError, match='disallowed address'):
        openai_compatible_translator.test_openai_compatible_connection(
            base_url='http://169.254.169.254/v1', model='local-model', api_key='', timeout=12)
    assert post.call_count == 0


@pytest.fixture
def serve_redirecting_endpoint():
    servers = []

    def serve(location):
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                self.rfile.read(int(self.headers['Content-Length']))
                if self.path == '/v1/chat/completions':
                    self.send_response(307)
                    self.send_header('Location', location)
                    self.send_header('Content-Length', '0')
                    self.end_headers()
                    return
                body = json.dumps({'choices': [{'finish_reason': 'stop',
                                                'message': {'content': '[{"id":1,"text":"Bonjour"}]'}}]}).encode()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format, *args):
                pass

        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        servers.append(server)
        return f'http://127.0.0.1:{server.server_port}/v1'

    yield serve
    for server in servers:
        server.shutdown()
        server.server_close()


def test_redirect_to_allowed_address_is_followed(serve_redirecting_endpoint):
    base_url = serve_redirecting_endpoint('/other/chat/completions')

    assert openai_compatible_translator._request_translation(
        cues=['Hello'], base_url=base_url, model='local-model', api_key='', timeout=5,
        from_lang='en', to_lang='fra') == ['Bonjour']


def test_redirect_to_disallowed_address_is_refused(serve_redirecting_endpoint):
    base_url = serve_redirecting_endpoint('http://169.254.169.254/latest/meta-data/')

    with pytest.raises(ValueError, match='disallowed address'):
        openai_compatible_translator._request_translation(
            cues=['Hello'], base_url=base_url, model='local-model', api_key='', timeout=5,
            from_lang='en', to_lang='fra')


@pytest.fixture
def serve_strict_endpoint():
    """Serve a Chat Completions endpoint that rejects unknown body fields, like Groq does."""
    requests_seen = []
    servers = []

    def serve():
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                payload = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                requests_seen.append(payload)
                if 'chat_template_kwargs' in payload:
                    status = 400
                    body = {'error': {'message': "property 'chat_template_kwargs' is unsupported",
                                      'type': 'invalid_request_error'}}
                else:
                    status = 200
                    body = {'choices': [{'finish_reason': 'stop',
                                         'message': {'content': '[{"id":1,"text":"Bonjour"}]'}}]}
                encoded = json.dumps(body).encode()
                self.send_response(status)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)

            def log_message(self, format, *args):
                pass

        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        servers.append(server)
        return f'http://127.0.0.1:{server.server_port}/v1'

    yield serve, requests_seen
    for server in servers:
        server.shutdown()
        server.server_close()


def test_strict_endpoint_is_retried_without_chat_template_kwargs(serve_strict_endpoint):
    serve, requests_seen = serve_strict_endpoint
    base_url = serve()

    assert openai_compatible_translator.test_openai_compatible_connection(
        base_url=base_url, model='strict-model', api_key='', timeout=5) == 'Bonjour'
    assert [('chat_template_kwargs' in payload) for payload in requests_seen] == [True, False]
    assert requests_seen[0]['messages'] == requests_seen[1]['messages']


def test_other_bad_requests_are_not_retried(mocker):
    response = mocker.Mock(status_code=400, text='{"error": {"message": "model not found"}}')
    response.raise_for_status.side_effect = openai_compatible_translator.requests.exceptions.HTTPError(
        response=response)
    post = mocker.patch.object(openai_compatible_translator.requests, 'post', return_value=response)

    with pytest.raises(RuntimeError, match='HTTP 400'):
        openai_compatible_translator.test_openai_compatible_connection(
            base_url='http://127.0.0.1/v1', model='missing-model', api_key='', timeout=5)
    assert post.call_count == 1


def test_rejected_chat_template_kwargs_is_not_resent_for_later_batches(serve_strict_endpoint, mocker):
    serve, requests_seen = serve_strict_endpoint
    base_url = serve()
    service = openai_compatible_translator.OpenAICompatibleTranslatorService(
        source_srt_file='', dest_srt_file='', to_lang='fra', media_type='episode', sonarr_series_id=None,
        sonarr_episode_id=None, radarr_id=None, forced=False, hi=False, video_path='', from_lang='en',
        orig_to_lang='en')
    settings_values = {'openai_base_url': base_url, 'openai_model': 'strict-model', 'openai_api_key': '',
                       'openai_timeout': 5}
    mocker.patch.object(openai_compatible_translator.OpenAICompatibleTranslatorService, '_setting',
                        staticmethod(lambda name, default: settings_values.get(name, default)))

    assert service._request_with_retry(['Hello']) == ['Bonjour']
    assert service._request_with_retry(['Hello']) == ['Bonjour']
    assert service._request_with_retry(['Hello']) == ['Bonjour']
    assert [('chat_template_kwargs' in payload) for payload in requests_seen] == [True, False, False, False]
