"""
Test for Bazarr UI functionality including authentication decorators.
"""
import pytest
from unittest.mock import Mock, patch
from flask import Flask

from bazarr.app.ui import check_login


def test_check_login_decorator_preserves_function_signature():
    """
    Test that check_login decorator preserves the original function's signature and metadata.
    """
    def original_function(arg1, arg2, kwarg1=None):
        """Test function docstring."""
        return f"{arg1}:{arg2}:{kwarg1}"

    decorated_function = check_login(original_function)

    # Check that function metadata is preserved
    assert decorated_function.__name__ == original_function.__name__
    assert decorated_function.__doc__ == original_function.__doc__


def test_check_login_decorator_can_be_applied():
    """
    Test that check_login decorator can be successfully applied to functions.
    """
    def test_function():
        return "test_result"

    # Should not raise any exceptions when applying decorator
    decorated_function = check_login(test_function)
    assert callable(decorated_function)


def test_check_login_decorator_is_wrapper():
    """
    Test that check_login returns a wrapper function that can be called.
    """
    def original_function(value):
        return value * 2

    decorated_function = check_login(original_function)

    # Verify it's a different function (wrapped)
    assert decorated_function != original_function
    assert callable(decorated_function)
    assert decorated_function.__name__ == original_function.__name__


def test_check_login_no_authentication():
    """
    Test check_login decorator when no authentication is configured.
    """
    def test_function():
        return "success_response"

    # Mock settings for no authentication
    with patch('bazarr.app.ui.settings') as mock_settings:
        mock_settings.auth.type = None

        decorated_function = check_login(test_function)
        result = decorated_function()

        assert result == "success_response"


def test_check_login_basic_auth_success():
    """
    Test check_login decorator with valid basic authentication.
    """
    def test_function():
        return "authenticated_response"

    # Mock Flask request context with basic auth
    app = Flask(__name__)
    with app.test_request_context(headers={'Authorization': 'Basic dGVzdDp0ZXN0'}):
        with patch('bazarr.app.ui.settings') as mock_settings, \
             patch('bazarr.app.ui.check_credentials', return_value=True):

            mock_settings.auth.type = 'basic'

            decorated_function = check_login(test_function)
            result = decorated_function()

            assert result == "authenticated_response"


def test_check_login_basic_auth_failure():
    """
    Test check_login decorator with invalid basic authentication.
    """
    def test_function():
        return "should_not_reach"

    # Mock Flask request context with invalid basic auth
    app = Flask(__name__)
    with app.test_request_context(headers={'Authorization': 'Basic aW52YWxpZA=='}):
        with patch('bazarr.app.ui.settings') as mock_settings, \
             patch('bazarr.app.ui.check_credentials', return_value=False):

            mock_settings.auth.type = 'basic'

            decorated_function = check_login(test_function)
            result = decorated_function()

            # Should return 401 tuple
            assert isinstance(result, tuple)
            assert result[1] == 401
            assert result[0] == 'Unauthorized'


def test_check_login_basic_auth_missing():
    """
    Test check_login decorator when basic auth is required but not provided.
    """
    def test_function():
        return "should_not_reach"

    # Mock Flask request context without authorization header
    app = Flask(__name__)
    with app.test_request_context():
        with patch('bazarr.app.ui.settings') as mock_settings:
            mock_settings.auth.type = 'basic'

            decorated_function = check_login(test_function)
            result = decorated_function()

            # Should return 401 tuple
            assert isinstance(result, tuple)
            assert result[1] == 401
            assert result[0] == 'Unauthorized'


def test_check_login_form_auth_success():
    """
    Test check_login decorator with valid form authentication session.
    """
    def test_function():
        return "form_authenticated_response"

    # Mock Flask request context with valid session
    app = Flask(__name__)
    app.secret_key = 'test_secret'

    with app.test_request_context():
        with patch('bazarr.app.ui.settings') as mock_settings, \
             patch('bazarr.app.ui.session', {'logged_in': True}):

            mock_settings.auth.type = 'form'

            decorated_function = check_login(test_function)
            result = decorated_function()

            assert result == "form_authenticated_response"


def test_check_login_form_auth_failure():
    """
    Test check_login decorator when form auth session is invalid.
    """
    def test_function():
        return "should_not_reach"

    app = Flask(__name__)
    with app.test_request_context():
        with patch('bazarr.app.ui.settings') as mock_settings, \
             patch('bazarr.app.ui.session', {}) as mock_session, \
             patch('bazarr.app.ui.abort') as mock_abort:

            mock_settings.auth.type = 'form'
            mock_abort.return_value = ('Unauthorized', 401)

            decorated_function = check_login(test_function)
            result = decorated_function()

            # Should call abort
            mock_abort.assert_called_once_with(401, message="Unauthorized")


def test_check_login_preserves_function_arguments():
    """
    Test that check_login decorator properly passes through function arguments.
    """
    def test_function(arg1, arg2, kwarg1=None):
        return f"args:{arg1},{arg2} kwargs:{kwarg1}"

    with patch('bazarr.app.ui.settings') as mock_settings:
        mock_settings.auth.type = None

        decorated_function = check_login(test_function)
        result = decorated_function("test1", "test2", kwarg1="test_kw")

        assert result == "args:test1,test2 kwargs:test_kw"


def test_check_login_preserves_function_exceptions():
    """
    Test that check_login decorator allows function exceptions to propagate.
    """
    def test_function():
        raise ValueError("Test exception")

    with patch('bazarr.app.ui.settings') as mock_settings:
        mock_settings.auth.type = None

        decorated_function = check_login(test_function)

        with pytest.raises(ValueError, match="Test exception"):
            decorated_function()


def test_check_login_with_different_return_types():
    """
    Test that check_login decorator properly handles different return types.
    """
    test_cases = [
        ("string_result", str),
        (42, int),
        ([1, 2, 3], list),
        ({"key": "value"}, dict),
        (None, type(None)),
    ]

    with patch('bazarr.app.ui.settings') as mock_settings:
        mock_settings.auth.type = None

        for expected_value, expected_type in test_cases:
            def test_function():
                return expected_value

            decorated_function = check_login(test_function)
            result = decorated_function()

            assert result == expected_value
            assert type(result) == expected_type