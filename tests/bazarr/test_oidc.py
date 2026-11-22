# -*- coding: utf-8 -*-
"""Exercise browser login against signed tokens and an independent mock provider."""

import base64
import hashlib
import json
import time
from types import SimpleNamespace
from urllib.parse import parse_qs, urlencode, urlsplit

import pytest
import rsa
from jinja2 import DictLoader
from jose import jwk, jwt

from api import api_bp
from app import oidc, form_sessions

ISSUER = 'https://id.example.test'
CALLBACK = 'https://bazarr.example.test/bazarr/auth/oidc/callback'
BASE_URL = 'https://bazarr.example.test'


@pytest.fixture(scope='module')
def signing_key():
    public, private = rsa.newkeys(2048)
    return public.save_pkcs1(), private.save_pkcs1()


@pytest.fixture
def provider(requests_mock, signing_key):
    public, private = signing_key
    metadata = {
        'issuer': ISSUER,
        'authorization_endpoint': ISSUER + '/authorize',
        'token_endpoint': ISSUER + '/token',
        'jwks_uri': ISSUER + '/jwks',
        'id_token_signing_alg_values_supported': ['RS256', 'ES256'],
        'code_challenge_methods_supported': ['S256'],
        'token_endpoint_auth_methods_supported': ['none', 'client_secret_basic', 'client_secret_post'],
    }
    public_jwk = jwk.construct(public, 'RS256').to_dict()
    public_jwk.update(kid='test-key', use='sig', alg='RS256')
    state = SimpleNamespace(metadata=metadata, jwks={'keys': [public_jwk]}, overrides={},
                            omit=[], algorithm='RS256', private=private, authorization=None, calls=[], scope=None)
    requests_mock.get(ISSUER + '/.well-known/openid-configuration', json=lambda *_: state.metadata)
    requests_mock.get(ISSUER + '/jwks', json=lambda *_: state.jwks)

    def exchange(request, context):
        body = parse_qs(request.text)
        state.calls.append(request)
        assert body['code'] == ['authorization-code']
        assert body['redirect_uri'] == [CALLBACK]
        verifier = body['code_verifier'][0]
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode('ascii')).digest()).rstrip(b'=').decode()
        assert challenge == state.authorization['code_challenge'][0]
        claims = {
            'iss': ISSUER, 'aud': 'bazarr', 'sub': 'allowed-subject',
            'nonce': state.authorization['nonce'][0], 'iat': int(time.time()), 'exp': int(time.time()) + 300,
        }
        claims.update(state.overrides)
        for key in state.omit:
            claims.pop(key, None)
        token = {'access_token': 'provider-access-token', 'token_type': 'Bearer',
                 'id_token': jwt.encode(claims, state.private, algorithm=state.algorithm, headers={'kid': 'test-key'})}
        if state.scope is not None:
            token['scope'] = state.scope
        return token

    requests_mock.post(ISSUER + '/token', json=exchange)
    return state


@pytest.fixture
def oidc_app(monkeypatch):
    from app import config, ui
    from app import app as app_module

    auth = config.settings.auth
    saved = dict(auth)
    saved_base_url = config.settings.general.base_url
    config.settings.general.base_url = '/bazarr'
    auth.update({'type': 'oidc', 'apikey': 'test-api-key', 'oidc_issuer': ISSUER,
                 'oidc_client_id': 'bazarr', 'oidc_redirect_uri': CALLBACK,
                 'oidc_allowed_subjects': ['allowed-subject'], 'oidc_client_secret_file': ''})
    monkeypatch.setattr(config, 'base_url', '/bazarr')
    monkeypatch.setattr(ui, 'base_url', '/bazarr')
    monkeypatch.setattr(app_module, 'base_url', '/bazarr')
    monkeypatch.delenv('BAZARR_OIDC_CLIENT_SECRET', raising=False)
    oidc._pending.clear()
    oidc._providers.clear()
    form_sessions.revoke_all_form_sessions()
    from app.database import database
    database.close()
    app = app_module.create_app()
    app.config.update(TESTING=True, SECRET_KEY='oidc-test-session-key')
    app.jinja_loader = DictLoader({'index.html': '{{ BAZARR_SERVER_INJECT | tojson }}'})
    app.register_blueprint(oidc.oidc_bp, url_prefix='/bazarr')
    app.register_blueprint(ui.ui_bp, url_prefix='/bazarr')
    app.register_blueprint(api_bp, url_prefix='/bazarr/api')

    @app.get('/protected')
    @ui.check_login
    def protected():
        return 'protected-content'

    @app.post('/form-session')
    def form_session():
        form_sessions.start_form_session()
        return '', 204

    yield app
    auth.clear()
    auth.update(saved)
    config.settings.general.base_url = saved_base_url
    oidc._pending.clear()
    oidc._providers.clear()
    form_sessions.revoke_all_form_sessions()


def start(client, provider, return_to='/series?wanted=true'):
    response = client.get('/bazarr/auth/oidc/login', query_string={'returnTo': return_to}, base_url=BASE_URL)
    assert response.status_code == 302
    assert response.location.startswith(ISSUER + '/authorize?')
    provider.authorization = parse_qs(urlsplit(response.location).query)
    return response


def finish(client, provider, **params):
    query = {'state': provider.authorization['state'][0], 'code': 'authorization-code', 'iss': ISSUER}
    query.update(params)
    return client.get('/bazarr/auth/oidc/callback?' + urlencode(query), base_url=BASE_URL)


def injected(client):
    return json.loads(client.get('/bazarr/', base_url=BASE_URL).text)


def test_login_uses_pkce_nonce_and_secure_cookie(oidc_app, provider):
    client = oidc_app.test_client()
    response = start(client, provider)
    params = provider.authorization
    assert params['client_id'] == ['bazarr']
    assert params['redirect_uri'] == [CALLBACK]
    assert params['response_type'] == ['code']
    assert params['scope'] == ['openid']
    assert params['code_challenge_method'] == ['S256']
    assert params['nonce'][0]
    cookie = response.headers['Set-Cookie']
    assert 'Secure' in cookie and 'HttpOnly' in cookie and 'SameSite=Lax' in cookie
    assert oidc._pending[params['state'][0]].client._code_verifier not in cookie


def test_valid_identity_gets_session_and_return_path(oidc_app, provider):
    provider.scope = 'openid'
    client = oidc_app.test_client()
    assert 'apiKey' not in injected(client)
    start(client, provider)
    response = finish(client, provider)
    assert response.location == '/bazarr/series?wanted=true'
    assert client.get('/protected', base_url=BASE_URL).status_code == 200
    assert injected(client)['apiKey'] == 'test-api-key'
    with client.session_transaction(base_url=BASE_URL) as browser_session:
        assert browser_session['oidc_subject'] == 'allowed-subject'
        assert 'provider-access-token' not in json.dumps(dict(browser_session))
        assert 'oidc_state' not in browser_session
    assert response.headers['Cache-Control'] == 'no-store'
    assert response.headers['Referrer-Policy'] == 'no-referrer'


def test_unexpected_granted_scope_returns_login_error(oidc_app, provider, monkeypatch):
    monkeypatch.delenv('OAUTHLIB_RELAX_TOKEN_SCOPE', raising=False)
    provider.scope = 'openid profile'
    client = oidc_app.test_client()
    start(client, provider)

    assert finish(client, provider).location == '/bazarr/login?oidcError=failed'
    assert 'apiKey' not in injected(client)


@pytest.mark.parametrize('overrides', [
    {'iss': 'https://attacker.example'}, {'aud': 'another-client'}, {'sub': 'another-subject'},
    {'nonce': 'wrong-nonce'}, {'nonce': None}, {'exp': int(time.time()) - 300},
    {'iat': int(time.time()) + 3600}, {'nbf': int(time.time()) + 3600},
    {'aud': ['bazarr', 'another-client']}, {'azp': 'another-client'},
])
def test_invalid_claims_do_not_create_session(oidc_app, provider, overrides):
    provider.overrides.update(overrides)
    client = oidc_app.test_client()
    start(client, provider)
    response = finish(client, provider)
    assert response.location.startswith('/bazarr/login?oidcError=')
    assert client.get('/protected', base_url=BASE_URL).status_code == 401
    assert 'apiKey' not in injected(client)


@pytest.mark.parametrize('claim', ['iss', 'aud', 'sub', 'exp', 'iat', 'nonce'])
def test_required_claims_cannot_be_omitted(oidc_app, provider, claim):
    provider.omit = [claim]
    client = oidc_app.test_client()
    start(client, provider)
    assert 'oidcError=failed' in finish(client, provider).location
    assert 'apiKey' not in injected(client)


def test_subject_denial_has_safe_error_message(oidc_app, provider):
    provider.overrides['sub'] = '<script>private-subject</script>'
    client = oidc_app.test_client()
    start(client, provider)
    response = finish(client, provider)
    assert response.location == '/bazarr/login?oidcError=denied'
    assert 'private-subject' not in response.text


@pytest.mark.parametrize('params', [{'state': ''}, {'state': 'wrong-state'}, {'code': ''},
                                   {'error': 'access_denied'}, {'iss': 'https://attacker.example'}])
def test_invalid_callback_does_not_exchange_code(oidc_app, provider, params):
    client = oidc_app.test_client()
    start(client, provider)
    assert 'oidcError=failed' in finish(client, provider, **params).location
    assert not provider.calls


def test_another_browser_cannot_use_callback(oidc_app, provider):
    start(oidc_app.test_client(), provider)
    other = oidc_app.test_client()
    assert 'oidcError=failed' in finish(other, provider).location
    assert not provider.calls


def test_callback_cannot_be_replayed_even_with_saved_cookie(oidc_app, provider):
    client = oidc_app.test_client()
    start(client, provider)
    cookie = client.get_cookie('session', domain='bazarr.example.test').value
    finish(client, provider)
    client.set_cookie('session', cookie, domain='bazarr.example.test')
    assert 'oidcError=failed' in finish(client, provider).location
    assert len(provider.calls) == 1


def test_expired_login_cannot_exchange_code(oidc_app, provider, monkeypatch):
    client = oidc_app.test_client()
    start(client, provider)
    now = time.monotonic()
    monkeypatch.setattr(oidc.time, 'monotonic', lambda: now + oidc._LOGIN_MAX_AGE + 1)
    assert 'oidcError=failed' in finish(client, provider).location
    assert not provider.calls


def test_configuration_change_invalidates_pending_login(oidc_app, provider):
    from app.config import settings
    client = oidc_app.test_client()
    start(client, provider)
    settings.auth.oidc_client_id = 'changed-client'
    assert 'oidcError=failed' in finish(client, provider).location
    assert not provider.calls


def test_allowlist_change_invalidates_existing_session(oidc_app, provider):
    from app.config import settings
    client = oidc_app.test_client()
    start(client, provider)
    finish(client, provider)
    settings.auth.oidc_allowed_subjects = ['another-subject']
    assert client.get('/protected', base_url=BASE_URL).status_code == 401
    assert 'apiKey' not in injected(client)


def test_password_session_cannot_bypass_oidc(oidc_app):
    client = oidc_app.test_client()
    client.post('/form-session', base_url=BASE_URL)
    assert client.get('/protected', base_url=BASE_URL).status_code == 401
    assert 'apiKey' not in injected(client)


def test_password_login_is_disabled_in_oidc_mode(oidc_app):
    client = oidc_app.test_client()
    response = client.post('/bazarr/api/system/account', base_url=BASE_URL,
                           json={'action': 'login', 'username': 'admin', 'password': 'admin'})
    assert response.status_code == 403


def test_logout_revokes_saved_cookie(oidc_app, provider):
    client = oidc_app.test_client()
    start(client, provider)
    finish(client, provider)
    cookie = client.get_cookie('session', domain='bazarr.example.test').value
    assert client.post('/bazarr/api/system/account', json={'action': 'logout'}, base_url=BASE_URL).status_code == 204
    client.set_cookie('session', cookie, domain='bazarr.example.test')
    assert client.get('/protected', base_url=BASE_URL).status_code == 401


def test_api_keys_still_work_and_cookie_alone_does_not_authenticate_api(oidc_app, provider, monkeypatch):
    monkeypatch.setattr('api.files.files_sonarr.browse_sonarr_filesystem', lambda: None)
    client = oidc_app.test_client()
    start(client, provider)
    finish(client, provider)
    assert client.get('/bazarr/api/files/sonarr', base_url=BASE_URL).status_code == 401
    assert client.get('/bazarr/api/files/sonarr', headers={'X-API-KEY': 'test-api-key'}, base_url=BASE_URL).status_code == 200


@pytest.mark.parametrize('target', ['https://attacker.example', '//attacker.example', '/\\attacker.example',
                                  '/%5cattacker.example', '/login', '/auth/oidc/login', '/%0d%0aLocation:evil'])
def test_return_path_cannot_leave_bazarr_or_loop(oidc_app, provider, target):
    client = oidc_app.test_client()
    start(client, provider, return_to=target)
    assert finish(client, provider).location == '/bazarr/'


def test_discovery_issuer_mismatch_fails_closed(oidc_app, provider):
    provider.metadata['issuer'] = 'https://attacker.example'
    client = oidc_app.test_client()
    response = client.get('/bazarr/auth/oidc/login', base_url=BASE_URL)
    assert 'oidcError=failed' in response.location
    assert 'apiKey' not in injected(client)


@pytest.mark.parametrize('field', ['authorization_endpoint', 'token_endpoint', 'jwks_uri'])
def test_discovery_rejects_non_https_endpoints(oidc_app, provider, field):
    provider.metadata[field] = 'http://provider.example/'
    response = oidc_app.test_client().get('/bazarr/auth/oidc/login', base_url=BASE_URL)
    assert 'oidcError=failed' in response.location


def test_plain_pkce_provider_is_rejected(oidc_app, provider):
    provider.metadata['code_challenge_methods_supported'] = ['plain']
    response = oidc_app.test_client().get('/bazarr/auth/oidc/login', base_url=BASE_URL)
    assert 'oidcError=failed' in response.location


def test_rotated_signing_key_is_loaded(oidc_app, provider):
    public, private = rsa.newkeys(2048)
    client = oidc_app.test_client()
    start(client, provider)
    provider.private = private.save_pkcs1()
    key = jwk.construct(public.save_pkcs1(), 'RS256').to_dict()
    key.update(kid='test-key', alg='RS256')
    provider.jwks = {'keys': [key]}
    assert finish(client, provider).location == '/bazarr/series?wanted=true'


def test_wrong_signature_is_rejected(oidc_app, provider):
    _, private = rsa.newkeys(2048)
    provider.private = private.save_pkcs1()
    client = oidc_app.test_client()
    start(client, provider)
    assert 'oidcError=failed' in finish(client, provider).location


def test_symmetric_algorithm_is_rejected(oidc_app, provider):
    provider.algorithm = 'HS256'
    provider.private = 'attacker-secret'
    provider.metadata['id_token_signing_alg_values_supported'].append('HS256')
    client = oidc_app.test_client()
    start(client, provider)
    assert 'oidcError=failed' in finish(client, provider).location


def test_ecdsa_signatures_are_supported(oidc_app, provider):
    from ecdsa import SigningKey, NIST256p
    key = SigningKey.generate(curve=NIST256p)
    provider.private = key.to_pem().decode()
    provider.algorithm = 'ES256'
    public = jwk.construct(key.verifying_key.to_pem().decode(), 'ES256').to_dict()
    public.update(kid='test-key', alg='ES256')
    provider.jwks = {'keys': [public]}
    client = oidc_app.test_client()
    start(client, provider)
    assert finish(client, provider).location == '/bazarr/series?wanted=true'


def test_confidential_client_uses_basic_auth(oidc_app, provider, monkeypatch):
    monkeypatch.setenv('BAZARR_OIDC_CLIENT_SECRET', 'test-client-secret')
    client = oidc_app.test_client()
    start(client, provider)
    finish(client, provider)
    expected = base64.b64encode(b'bazarr:test-client-secret').decode()
    assert provider.calls[0].headers['Authorization'] == 'Basic ' + expected
    assert 'client_secret' not in parse_qs(provider.calls[0].text)


def test_token_redirect_does_not_forward_credentials(oidc_app, provider, requests_mock, monkeypatch):
    monkeypatch.setenv('BAZARR_OIDC_CLIENT_SECRET', 'test-client-secret')
    requests_mock.post(ISSUER + '/token', status_code=307, headers={'Location': 'https://attacker.example/token'})
    client = oidc_app.test_client()
    start(client, provider)
    assert 'oidcError=failed' in finish(client, provider).location
    assert not any(call.hostname == 'attacker.example' for call in requests_mock.request_history)


def test_saved_secret_file_takes_precedence_and_stays_private(oidc_app, provider, monkeypatch, tmp_path,
                                                              memory_session):
    from app import config
    from app import database as db_module

    monkeypatch.setattr(config, 'write_config', lambda: None)
    monkeypatch.setattr(db_module, 'database', memory_session)
    secret_file = tmp_path / 'client-secret'
    secret_file.write_text('file-test-secret\n')
    monkeypatch.setenv('BAZARR_OIDC_CLIENT_SECRET', 'env-test-secret')
    config.save_settings([('settings-auth-oidc_client_secret_file', str(secret_file))])
    client = oidc_app.test_client()
    start(client, provider)
    finish(client, provider)
    expected = base64.b64encode(b'bazarr:file-test-secret').decode()
    assert provider.calls[0].headers['Authorization'] == 'Basic ' + expected
    assert 'file-test-secret' not in json.dumps(config.get_settings())
    assert 'env-test-secret' not in json.dumps(config.get_settings())


@pytest.mark.parametrize('contents, message', [
    (None, 'must be able to read'),
    (b' \n', 'file is empty'),
    (b'\xff', 'must be able to read'),
])
def test_invalid_client_secret_file_cannot_be_saved(oidc_app, monkeypatch, tmp_path, contents, message):
    from app import config
    from dynaconf.validator import ValidationError

    secret_file = tmp_path / 'client-secret'
    if contents is not None:
        secret_file.write_bytes(contents)
    writes = []
    monkeypatch.setattr(config, 'write_config', lambda: writes.append(True))
    monkeypatch.setattr(config.settings, 'reload', lambda: None)

    with pytest.raises(ValidationError, match=message):
        config.save_settings([('settings-auth-oidc_client_secret_file', str(secret_file))])

    assert not writes


def test_confidential_client_can_use_client_secret_post(oidc_app, provider, monkeypatch):
    monkeypatch.setenv('BAZARR_OIDC_CLIENT_SECRET', 'test-client-secret')
    provider.metadata['token_endpoint_auth_methods_supported'] = ['client_secret_post']
    client = oidc_app.test_client()
    start(client, provider)
    assert finish(client, provider).location == '/bazarr/series?wanted=true'
    assert 'Authorization' not in provider.calls[0].headers
    assert parse_qs(provider.calls[0].text)['client_secret'] == ['test-client-secret']


@pytest.mark.parametrize('field, value', [('oidc_client_id', '000123'),
                                         ('oidc_allowed_subjects', ['another-subject'])])
def test_saving_oidc_configuration_revokes_sessions(oidc_app, provider, monkeypatch, memory_session, field, value):
    from app import config
    from app import database as db_module
    monkeypatch.setattr(config, 'write_config', lambda: None)
    monkeypatch.setattr(db_module, 'database', memory_session)
    client = oidc_app.test_client()
    start(client, provider)
    finish(client, provider)

    config.save_settings([('settings-auth-' + field, value)])

    assert config.settings.auth[field] == value
    assert client.get('/protected', base_url=BASE_URL).status_code == 401


def test_empty_subject_list_cannot_be_saved(oidc_app, monkeypatch, memory_session):
    from app import config
    from app import database as db_module
    from dynaconf.validator import ValidationError
    writes = []
    monkeypatch.setattr(config, 'write_config', lambda: writes.append(True))
    monkeypatch.setattr(config.settings, 'reload', lambda: None)
    monkeypatch.setattr(db_module, 'database', memory_session)
    with pytest.raises(ValidationError, match='at least one allowed subject'):
        config.save_settings([('settings-auth-oidc_allowed_subjects', [])])
    assert not writes


@pytest.mark.parametrize('changes', [
    {'oidc_issuer': 'http://issuer.example'}, {'oidc_issuer': 'https://issuer.example?query=true'},
    {'oidc_redirect_uri': 'https://bazarr.example.test/auth/oidc/callback'},
    {'oidc_allowed_subjects': []}, {'oidc_allowed_subjects': ['']}, {'oidc_client_id': ''},
])
def test_invalid_configuration_is_rejected(changes):
    auth = SimpleNamespace(oidc_issuer=ISSUER, oidc_redirect_uri=CALLBACK,
                           oidc_client_id='bazarr', oidc_allowed_subjects=['allowed-subject'])
    for name, value in changes.items():
        setattr(auth, name, value)
    with pytest.raises(ValueError):
        oidc.validate_oidc_configuration(auth, '/bazarr')
