from wraptor.decorators import timeout, throttle, memoize
import pytest

with_decorators = pytest.mark.parametrize("decorator", [
    timeout, throttle, memoize
])

@with_decorators
def test_called_with_args(decorator):
    test_args = [1, 2, [1, 2, 3], { 'asdf': 5 }]
    test_kwargs = { 'a': 1, 'b': [1, 2, 3] }

    @decorator()
    def fn(*args, **kwargs):
        assert tuple(test_args) == args
        assert test_kwargs == kwargs

    fn(*test_args, **test_kwargs)
