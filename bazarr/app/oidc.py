# coding=utf-8

"""OIDC browser login. Provider tokens and PKCE verifiers stay on the server."""

import hashlib
import hmac
import json
import logging
import os
import secrets
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlsplit, urlencode

import requests
from flask import Blueprint, redirect, request, session
from jose import jwt, JWTError
from oauthlib.oauth2 import OAuth2Error
from requests_oauthlib import OAuth2Session

from .form_sessions import end_form_session, is_form_session_active, start_form_session

oidc_bp = Blueprint('oidc', __name__)
_SIGNING_ALGORITHMS = ('RS256', 'RS384', 'RS512', 'ES256', 'ES384', 'ES512')
_LOGIN_MAX_AGE = 600
_PROVIDER_MAX_AGE = 300
_MAX_PENDING_LOGINS = 1024
_lock = threading.Lock()
_pending = {}
_providers = {}

# These libraries log token response bodies at DEBUG. Authentication material must
# stay out of Bazarr's logs, including when application debug logging is enabled.
logging.getLogger('requests_oauthlib').setLevel(logging.WARNING)
logging.getLogger('oauthlib').setLevel(logging.WARNING)


@dataclass
class PendingLogin:
    client: OAuth2Session
    nonce: str
    fingerprint: str
    return_to: str
    expires: float


def _https_url(value):
    try:
        parsed = urlsplit(value)
        return (parsed.scheme == 'https' and bool(parsed.hostname) and not parsed.username
                and not parsed.password and not parsed.fragment)
    except (TypeError, ValueError):
        return False


def validate_oidc_configuration(auth, base_url):
    """Validate before enabling OIDC, without contacting the provider."""
    issuer = auth.oidc_issuer
    callback = auth.oidc_redirect_uri
    if not _https_url(issuer) or urlsplit(issuer).query:
        raise ValueError('OIDC issuer must be an HTTPS URL without a query or fragment')
    if (not _https_url(callback) or urlsplit(callback).query
            or urlsplit(callback).path != base_url.rstrip('/') + '/auth/oidc/callback'):
        raise ValueError('OIDC redirect URI must be HTTPS and use the Bazarr base URL followed by /auth/oidc/callback')
    if not auth.oidc_client_id or not isinstance(auth.oidc_client_id, str):
        raise ValueError('OIDC client ID is required')
    if (not auth.oidc_allowed_subjects
            or not all(isinstance(subject, str) and subject.strip() for subject in auth.oidc_allowed_subjects)):
        raise ValueError('OIDC requires at least one allowed subject (sub)')


def _configuration():
    from .config import settings, base_url

    if settings.auth.type != 'oidc':
        raise ValueError('OIDC is disabled')
    validate_oidc_configuration(settings.auth, base_url)
    secret = os.environ.get('BAZARR_OIDC_CLIENT_SECRET', '')
    if settings.auth.oidc_client_secret_file:
        secret = Path(settings.auth.oidc_client_secret_file).read_text(encoding='utf-8').strip()
    return {
        'issuer': settings.auth.oidc_issuer,
        'client_id': settings.auth.oidc_client_id,
        'client_secret': secret,
        'redirect_uri': settings.auth.oidc_redirect_uri,
        'subjects': list(settings.auth.oidc_allowed_subjects),
        'base_url': base_url,
    }


def _fingerprint(config):
    return hashlib.sha256(json.dumps(config, sort_keys=True).encode('utf-8')).hexdigest()


def _get_json(url):
    if not _https_url(url):
        raise ValueError('OIDC provider endpoints must use HTTPS')
    response = requests.get(url, timeout=10, allow_redirects=False)
    if response.status_code != 200:
        raise ValueError('OIDC provider did not return a successful response')
    data = response.json()
    if not isinstance(data, dict):
        raise ValueError('Invalid OIDC provider response')
    return data


def _provider(issuer, refresh=False):
    with _lock:
        cached = _providers.get(issuer)
        if not refresh and cached and cached[0] > time.monotonic():
            return cached[1], cached[2]

    metadata = _get_json(issuer.rstrip('/') + '/.well-known/openid-configuration')
    if metadata.get('issuer') != issuer:
        raise ValueError('OIDC discovery issuer does not match the configured issuer')
    for field in ('authorization_endpoint', 'token_endpoint', 'jwks_uri'):
        if not _https_url(metadata.get(field)):
            raise ValueError('OIDC discovery contains an invalid HTTPS endpoint')
    if 'S256' not in metadata.get('code_challenge_methods_supported', ['S256']):
        raise ValueError('OIDC provider must support PKCE with S256')
    jwks = _get_json(metadata['jwks_uri'])
    if not isinstance(jwks.get('keys'), list) or not jwks['keys']:
        raise ValueError('OIDC provider did not return signing keys')
    with _lock:
        # Only the currently used provider needs to be retained after a config change.
        _providers.clear()
        _providers[issuer] = (time.monotonic() + _PROVIDER_MAX_AGE, metadata, jwks)
    return metadata, jwks


def _validate_id_token(token, config, nonce, metadata, jwks):
    header = jwt.get_unverified_header(token['id_token'])
    algorithm = header.get('alg')
    if (algorithm not in _SIGNING_ALGORITHMS
            or algorithm not in metadata.get('id_token_signing_alg_values_supported', ['RS256'])):
        raise ValueError('OIDC signing algorithm is not supported')
    keys = [key for key in jwks['keys'] if isinstance(key, dict)
            and key.get('use', 'sig') == 'sig' and 'verify' in key.get('key_ops', ['verify'])
            and key.get('alg', algorithm) == algorithm
            and (not header.get('kid') or key.get('kid') == header['kid'])]
    if not keys:
        raise JWTError('No matching OIDC signing key')
    claims = jwt.decode(token['id_token'], {'keys': keys}, algorithms=[algorithm],
                        issuer=config['issuer'], audience=config['client_id'],
                        access_token=token.get('access_token'),
                        options={'require_iss': True, 'require_sub': True, 'require_aud': True,
                                 'require_exp': True, 'require_iat': True})
    if not isinstance(claims.get('nonce'), str) or not hmac.compare_digest(claims['nonce'], nonce):
        raise ValueError('OIDC nonce does not match')
    audiences = claims['aud'] if isinstance(claims['aud'], list) else [claims['aud']]
    if ((len(audiences) > 1 and claims.get('azp') != config['client_id'])
            or ('azp' in claims and claims['azp'] != config['client_id'])):
        raise ValueError('OIDC authorized party does not match')
    if claims['iat'] > time.time() + 60:
        raise ValueError('OIDC token was issued in the future')
    if not claims['sub']:
        raise ValueError('OIDC subject is empty')
    if claims['sub'] not in config['subjects']:
        raise PermissionError('OIDC subject is not allowed')
    return claims


def is_oidc_session_active():
    if not is_form_session_active():
        return False
    try:
        config = _configuration()
        return (session.get('oidc_config') == _fingerprint(config)
                and session.get('oidc_subject') in config['subjects'])
    except (OSError, ValueError):
        return False


def _return_path(value):
    decoded = unquote(value)
    if (not decoded.startswith('/') or decoded.startswith('//') or '\\' in decoded
            or any(ord(char) < 32 for char in decoded)
            or urlsplit(decoded).path.startswith(('/login', '/auth/'))):
        return '/'
    return value


def _error_response(error='failed'):
    from .config import base_url

    end_form_session()
    response = redirect(base_url + '/login?' + urlencode({'oidcError': error}))
    response.headers['Cache-Control'] = 'no-store'
    response.headers['Referrer-Policy'] = 'no-referrer'
    return response


@oidc_bp.after_request
def protect_login_response(response):
    response.headers['Cache-Control'] = 'no-store'
    response.headers['Referrer-Policy'] = 'no-referrer'
    return response


@oidc_bp.route('/auth/oidc/login')
def login():
    try:
        config = _configuration()
        metadata, _ = _provider(config['issuer'])
        client = OAuth2Session(config['client_id'], redirect_uri=config['redirect_uri'],
                               scope=['openid', 'profile', 'email'], pkce='S256')
        # A redirect from the token endpoint must not forward credentials elsewhere.
        client.max_redirects = 0
        nonce = secrets.token_urlsafe(32)
        authorization_url, state = client.authorization_url(metadata['authorization_endpoint'], nonce=nonce)
        now = time.monotonic()
        with _lock:
            for key in [key for key, pending in _pending.items() if pending.expires <= now]:
                _pending.pop(key).client.close()
            previous = _pending.pop(session.get('oidc_state'), None)
            if previous:
                previous.client.close()
            if len(_pending) >= _MAX_PENDING_LOGINS:
                raise ValueError('Too many pending OIDC logins')
            _pending[state] = PendingLogin(client, nonce, _fingerprint(config),
                                           _return_path(request.args.get('returnTo', '/')), now + _LOGIN_MAX_AGE)
        end_form_session()
        session['oidc_state'] = state
        return redirect(authorization_url)
    except (OSError, ValueError, TypeError, KeyError, requests.RequestException, OAuth2Error):
        logging.warning('OIDC login could not start. Check the provider and OIDC configuration.')
        return _error_response()


@oidc_bp.route('/auth/oidc/callback')
def callback():
    pending = None
    try:
        config = _configuration()
        state = request.args.get('state', '')
        browser_state = session.pop('oidc_state', '')
        if not state or not browser_state or not hmac.compare_digest(state, browser_state):
            raise ValueError('OIDC state does not match')
        with _lock:
            pending = _pending.pop(state, None)
        if (not pending or pending.expires <= time.monotonic()
                or pending.fingerprint != _fingerprint(config)):
            raise ValueError('OIDC login expired or configuration changed')
        if request.args.get('iss', config['issuer']) != config['issuer']:
            raise ValueError('OIDC authorization response issuer does not match')
        if request.args.get('error') or not request.args.get('code'):
            raise ValueError('OIDC provider did not authorize the request')
        metadata, jwks = _provider(config['issuer'])
        methods = metadata.get('token_endpoint_auth_methods_supported', ['client_secret_basic'])
        kwargs = {'include_client_id': True}
        if config['client_secret']:
            kwargs['client_secret'] = config['client_secret']
            if 'client_secret_basic' in methods:
                kwargs['include_client_id'] = False
            elif 'client_secret_post' not in methods:
                raise ValueError('OIDC client authentication method is not supported')
        elif 'none' not in methods:
            raise ValueError('OIDC provider requires a client secret')
        # Use the configured callback origin, never a Host or forwarded header.
        token = pending.client.fetch_token(metadata['token_endpoint'],
                                            authorization_response=config['redirect_uri'] + '?' + request.query_string.decode(),
                                            timeout=10, **kwargs)
        if not isinstance(token.get('id_token'), str):
            raise ValueError('OIDC provider did not return an ID token')
        try:
            claims = _validate_id_token(token, config, pending.nonce, metadata, jwks)
        except JWTError:
            # Signing keys can rotate while the discovery cache is still valid.
            metadata, jwks = _provider(config['issuer'], refresh=True)
            claims = _validate_id_token(token, config, pending.nonce, metadata, jwks)
        start_form_session()
        session['oidc_subject'] = claims['sub']
        session['oidc_config'] = _fingerprint(config)
        return redirect(config['base_url'] + pending.return_to)
    except PermissionError:
        logging.warning('OIDC login denied: subject is not in the configured allowlist.')
        return _error_response('denied')
    except (OSError, ValueError, KeyError, TypeError, requests.RequestException, OAuth2Error, JWTError):
        logging.warning('OIDC login failed. Check the provider and OIDC configuration.')
        return _error_response()
    finally:
        if pending:
            pending.client.close()
