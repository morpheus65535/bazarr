# coding=utf-8
"""
oauthlib.oauth2.rfc6749.errors
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Error used both by OAuth 2 clients and providers to represent the spec
defined error responses for all four core grant types.
"""
from __future__ import unicode_literals

import json

from oauthlib.common import add_params_to_uri, urlencode


class OAuth2Error(Exception):
    error = None
    status_code = 400
    description = ''

    def __init__(self, description=None, uri=None, state=None,
                 status_code=None, request=None):
        """
        description:    A human-readable ASCII [USASCII] text providing
                        additional information, used to assist the client
                        developer in understanding the error that occurred.
                        Values for the "error_description" parameter MUST NOT
                        include characters outside the set
                        x20-21 / x23-5B / x5D-7E.

        uri:    A URI identifying a human-readable web page with information
                about the error, used to provide the client developer with
                additional information about the error.  Values for the
                "error_uri" parameter MUST conform to the URI- Reference
                syntax, and thus MUST NOT include characters outside the set
                x21 / x23-5B / x5D-7E.

        state:  A CSRF protection value received from the client.

        request:  Oauthlib Request object
        """
        if description is not None:
            self.description = description

        message = '(%s) %s' % (self.error, self.description)
        if request:
            message += ' ' + repr(request)
        super(OAuth2Error, self).__init__(message)

        self.uri = uri
        self.state = state

        if status_code:
            self.status_code = status_code

        if request:
            self.redirect_uri = request.redirect_uri
            self.client_id = request.client_id
            self.scopes = request.scopes
            self.response_type = request.response_type
            self.response_mode = request.response_mode
            self.grant_type = request.grant_type
            if not state:
                self.state = request.state
        else:
            self.redirect_uri = None
            self.client_id = None
            self.scopes = None
            self.response_type = None
            self.response_mode = None
            self.grant_type = None

    def in_uri(self, uri):
        fragment = self.response_mode == "fragment"
        return add_params_to_uri(uri, self.twotuples, fragment)

    @property
    def twotuples(self):
        error = [('error', self.error)]
        if self.description:
            error.append(('error_description', self.description))
        if self.uri:
            error.append(('error_uri', self.uri))
        if self.state:
            error.append(('state', self.state))
        return error

    @property
    def urlencoded(self):
        return urlencode(self.twotuples)

    @property
    def json(self):
        return json.dumps(dict(self.twotuples))


class TokenExpiredError(OAuth2Error):
    error = 'token_expired'


class InsecureTransportError(OAuth2Error):
    error = 'insecure_transport'
    description = 'OAuth 2 MUST utilize https.'


class MismatchingStateError(OAuth2Error):
    error = 'mismatching_state'
    description = 'CSRF Warning! State not equal in request and response.'


class MissingCodeError(OAuth2Error):
    error = 'missing_code'


class MissingTokenError(OAuth2Error):
    error = 'missing_token'


class MissingTokenTypeError(OAuth2Error):
    error = 'missing_token_type'


class FatalClientError(OAuth2Error):
    """
    Errors during authorization where user should not be redirected back.

    If the request fails due to a missing, invalid, or mismatching
    redirection URI, or if the client identifier is missing or invalid,
    the authorization server SHOULD inform the resource owner of the
    error and MUST NOT automatically redirect the user-agent to the
    invalid redirection URI.

    Instead the user should be informed of the error by the provider itself.
    """
    pass


class InvalidRequestFatalError(FatalClientError):
    """
    For fatal errors, the request is missing a required parameter, includes
    an invalid parameter value, includes a parameter more than once, or is
    otherwise malformed.
    """
    error = 'invalid_request'


class InvalidRedirectURIError(InvalidRequestFatalError):
    description = 'Invalid redirect URI.'


class MissingRedirectURIError(InvalidRequestFatalError):
    description = 'Missing redirect URI.'


class MismatchingRedirectURIError(InvalidRequestFatalError):
    description = 'Mismatching redirect URI.'


class InvalidClientIdError(InvalidRequestFatalError):
    description = 'Invalid client_id parameter value.'


class MissingClientIdError(InvalidRequestFatalError):
    description = 'Missing client_id parameter.'


class InvalidRequestError(OAuth2Error):
    """
    The request is missing a required parameter, includes an invalid
    parameter value, includes a parameter more than once, or is
    otherwise malformed.
    """
    error = 'invalid_request'


class MissingResponseTypeError(InvalidRequestError):
    description = 'Missing response_type parameter.'


class AccessDeniedError(OAuth2Error):
    """
    The resource owner or authorization server denied the request.
    """
    error = 'access_denied'
    status_code = 401


class UnsupportedResponseTypeError(OAuth2Error):
    """
    The authorization server does not support obtaining an authorization
    code using this method.
    """
    error = 'unsupported_response_type'


class InvalidScopeError(OAuth2Error):
    """
    The requested scope is invalid, unknown, or malformed.
    """
    error = 'invalid_scope'
    status_code = 401


class ServerError(OAuth2Error):
    """
    The authorization server encountered an unexpected condition that
    prevented it from fulfilling the request.  (This error code is needed
    because a 500 Internal Server Error HTTP status code cannot be returned
    to the client via a HTTP redirect.)
    """
    error = 'server_error'


class TemporarilyUnavailableError(OAuth2Error):
    """
    The authorization server is currently unable to handle the request
    due to a temporary overloading or maintenance of the server.
    (This error code is needed because a 503 Service Unavailable HTTP
    status code cannot be returned to the client via a HTTP redirect.)
    """
    error = 'temporarily_unavailable'


class InvalidClientError(OAuth2Error):
    """
    Client authentication failed (e.g. unknown client, no client
    authentication included, or unsupported authentication method).
    The authorization server MAY return an HTTP 401 (Unauthorized) status
    code to indicate which HTTP authentication schemes are supported.
    If the client attempted to authenticate via the "Authorization" request
    header field, the authorization server MUST respond with an
    HTTP 401 (Unauthorized) status code, and include the "WWW-Authenticate"
    response header field matching the authentication scheme used by the
    client.
    """
    error = 'invalid_client'
    status_code = 401


class InvalidGrantError(OAuth2Error):
    """
    The provided authorization grant (e.g. authorization code, resource
    owner credentials) or refresh token is invalid, expired, revoked, does
    not match the redirection URI used in the authorization request, or was
    issued to another client.
    """
    error = 'invalid_grant'
    status_code = 401


class UnauthorizedClientError(OAuth2Error):
    """
    The authenticated client is not authorized to use this authorization
    grant type.
    """
    error = 'unauthorized_client'
    status_code = 401


class UnsupportedGrantTypeError(OAuth2Error):
    """
    The authorization grant type is not supported by the authorization
    server.
    """
    error = 'unsupported_grant_type'


class UnsupportedTokenTypeError(OAuth2Error):
    """
    The authorization server does not support the revocation of the
    presented token type.  I.e. the client tried to revoke an access token
    on a server not supporting this feature.
    """
    error = 'unsupported_token_type'


class FatalOpenIDClientError(FatalClientError):
    pass


class OpenIDClientError(OAuth2Error):
    pass


class InteractionRequired(OpenIDClientError):
    """
    The Authorization Server requires End-User interaction to proceed.

    This error MAY be returned when the prompt parameter value in the
    Authentication Request is none, but the Authentication Request cannot be
    completed without displaying a user interface for End-User interaction.
    """
    error = 'interaction_required'
    status_code = 401


class LoginRequired(OpenIDClientError):
    """
    The Authorization Server requires End-User authentication.

    This error MAY be returned when the prompt parameter value in the
    Authentication Request is none, but the Authentication Request cannot be
    completed without displaying a user interface for End-User authentication.
    """
    error = 'login_required'
    status_code = 401


class AccountSelectionRequired(OpenIDClientError):
    """
    The End-User is REQUIRED to select a session at the Authorization Server.

    The End-User MAY be authenticated at the Authorization Server with
    different associated accounts, but the End-User did not select a session.
    This error MAY be returned when the prompt parameter value in the
    Authentication Request is none, but the Authentication Request cannot be
    completed without displaying a user interface to prompt for a session to
    use.
    """
    error = 'account_selection_required'


class ConsentRequired(OpenIDClientError):
    """
    The Authorization Server requires End-User consent.

    This error MAY be returned when the prompt parameter value in the
    Authentication Request is none, but the Authentication Request cannot be
    completed without displaying a user interface for End-User consent.
    """
    error = 'consent_required'
    status_code = 401


class InvalidRequestURI(OpenIDClientError):
    """
    The request_uri in the Authorization Request returns an error or
    contains invalid data.
    """
    error = 'invalid_request_uri'
    description = 'The request_uri in the Authorization Request returns an ' \
                  'error or contains invalid data.'


class InvalidRequestObject(OpenIDClientError):
    """
    The request parameter contains an invalid Request Object.
    """
    error = 'invalid_request_object'
    description = 'The request parameter contains an invalid Request Object.'


class RequestNotSupported(OpenIDClientError):
    """
    The OP does not support use of the request parameter.
    """
    error = 'request_not_supported'
    description = 'The request parameter is not supported.'


class RequestURINotSupported(OpenIDClientError):
    """
    The OP does not support use of the request_uri parameter.
    """
    error = 'request_uri_not_supported'
    description = 'The request_uri parameter is not supported.'


class RegistrationNotSupported(OpenIDClientError):
    """
    The OP does not support use of the registration parameter.
    """
    error = 'registration_not_supported'
    description = 'The registration parameter is not supported.'


class InvalidTokenError(OAuth2Error):
    """
    The access token provided is expired, revoked, malformed, or
    invalid for other reasons.  The resource SHOULD respond with
    the HTTP 401 (Unauthorized) status code.  The client MAY
    request a new access token and retry the protected resource
    request.
    """
    error = 'invalid_token'
    status_code = 401
    description = ("The access token provided is expired, revoked, malformed, "
                   "or invalid for other reasons.")


class InsufficientScopeError(OAuth2Error):
    """
    The request requires higher privileges than provided by the
    access token.  The resource server SHOULD respond with the HTTP
    403 (Forbidden) status code and MAY include the "scope"
    attribute with the scope necessary to access the protected
    resource.
    """
    error = 'insufficient_scope'
    status_code = 403
    description = ("The request requires higher privileges than provided by "
                   "the access token.")


def raise_from_error(error, params=None):
    import inspect
    import sys
    kwargs = {
        'description': params.get('error_description'),
        'uri': params.get('error_uri'),
        'state': params.get('state')
    }
    for _, cls in inspect.getmembers(sys.modules[__name__], inspect.isclass):
        if cls.error == error:
            raise cls(**kwargs)
