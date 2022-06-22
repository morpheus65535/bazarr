import pytest

import inspect

from bazarr.app import get_providers


def test_get_providers_auth():
    for val in get_providers.get_providers_auth().values():
        assert isinstance(val, dict)


def test_get_providers_auth_with_provider_registry():
    """Make sure all providers will be properly initialized with bazarr
    configs"""
    from subliminal_patch.extensions import provider_registry

    auths = get_providers.get_providers_auth()
    for key, val in auths.items():
        provider = provider_registry[key]
        sign = inspect.signature(provider.__init__)
        for sub_key in val.keys():
            if sub_key not in sign.parameters:
                raise ValueError(f"'{sub_key}' parameter not present in {provider}")

            assert sign.parameters[sub_key] is not None
