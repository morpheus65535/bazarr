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
                               return_value=_response(mocker, '["Cześć"]'))
    assert _service()._translate_batch(['Hello']) == ['Cześć']
    assert post.call_args.args[0] == 'http://model/v1/chat/completions'
    payload = post.call_args.kwargs['json']
    assert payload['model'] == 'local-model'
    assert payload['chat_template_kwargs'] == {'enable_thinking': False}


def test_rejects_truncated_response(mocker):
    _settings(mocker)
    mocker.patch.object(openai_compatible_translator.requests, 'post',
                        return_value=_response(mocker, '["Hej"]', finish_reason='length'))
    with pytest.raises(RuntimeError, match='incomplete'):
        _service()._translate_batch(['Hello'])


def test_invalid_json_is_rejected(mocker):
    _settings(mocker)
    mocker.patch.object(openai_compatible_translator.requests, 'post',
                        return_value=_response(mocker, 'not json'))
    with pytest.raises(RuntimeError, match='JSON array'):
        _service()._translate_batch(['Hello'])
