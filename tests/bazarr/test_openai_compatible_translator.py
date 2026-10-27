import pytest

from bazarr.subtitles.tools.translate.services import openai_compatible_translator


def _service():
    return openai_compatible_translator.OpenAICompatibleTranslatorService(
        source_srt_file='in.srt', dest_srt_file='out.srt', to_lang='pol', media_type='episode',
        sonarr_series_id=1, sonarr_episode_id=2, radarr_id=None, forced=False, hi=False,
        video_path='video.mkv', from_lang='en', orig_to_lang='pl')


def _settings(mocker):
    for name, value in {'openai_base_url': 'http://model/v1', 'openai_model': 'local-model',
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
    assert post.call_args.args[0] == 'http://model/v1/chat/completions'
    payload = post.call_args.kwargs['json']
    assert payload['model'] == 'local-model'
    assert payload['chat_template_kwargs'] == {'enable_thinking': False}
    assert 'exactly 1 cue' in payload['messages'][0]['content']
    assert payload['messages'][1]['content'] == '[{"id": 1, "text": "Hello"}]'


@pytest.mark.parametrize(('base_url', 'expected_url'), [
    ('http://model', 'http://model/v1/chat/completions'),
    ('http://model/v1/', 'http://model/v1/chat/completions'),
    ('http://model/v1/chat/completions', 'http://model/v1/chat/completions'),
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
        base_url='http://model/v1', model='local-model', api_key='test-key', timeout=12)

    assert translation == 'Bonjour'
    assert post.call_args.args[0] == 'http://model/v1/chat/completions'
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
            base_url='http://model/v1', model='local-model', api_key='', timeout=12)


def test_connection_test_reports_unusable_translation(mocker):
    _settings(mocker)
    mocker.patch.object(openai_compatible_translator.requests, 'post',
                        return_value=_response(mocker, '[{"id":2,"text":"Bonjour"}]'))

    with pytest.raises(RuntimeError, match='unusable translation'):
        openai_compatible_translator.test_openai_compatible_connection(
            base_url='http://model/v1', model='local-model', api_key='', timeout=12)


def test_connection_test_reports_authentication_errors_without_echoing_key(mocker):
    response = mocker.Mock(status_code=401)
    error = openai_compatible_translator.requests.exceptions.HTTPError(response=response)
    mocker.patch.object(openai_compatible_translator.requests, 'post', side_effect=error)

    with pytest.raises(RuntimeError, match='Authentication failed') as raised:
        openai_compatible_translator.test_openai_compatible_connection(
            base_url='http://model/v1', model='local-model', api_key='secret', timeout=12)

    assert 'secret' not in str(raised.value)
