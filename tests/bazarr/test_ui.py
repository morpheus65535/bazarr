"""
Test for Bazarr UI functionality including authentication decorators.
"""
import pytest
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