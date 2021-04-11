import math
from datetime import datetime, timedelta

import pytest

from pint.compat import eq, isnan, zero_or_nan

from .helpers import requires_numpy


@pytest.mark.parametrize("check_all", [False, True])
def test_eq(check_all):
    assert eq(0, 0, check_all)
    assert not eq(0, 1, check_all)


@requires_numpy()
def test_eq_numpy():
    import numpy as np

    assert eq(np.array([1, 2]), np.array([1, 2]), True)
    assert not eq(np.array([1, 2]), np.array([1, 3]), True)
    np.testing.assert_equal(
        eq(np.array([1, 2]), np.array([1, 2]), False), np.array([True, True])
    )
    np.testing.assert_equal(
        eq(np.array([1, 2]), np.array([1, 3]), False), np.array([True, False])
    )

    # Mixed numpy/scalar
    assert eq(1, np.array([1, 1]), True)
    assert eq(np.array([1, 1]), 1, True)
    assert not eq(1, np.array([1, 2]), True)
    assert not eq(np.array([1, 2]), 1, True)


@pytest.mark.parametrize("check_all", [False, True])
def test_isnan(check_all):
    assert not isnan(0, check_all)
    assert not isnan(0.0, check_all)
    assert isnan(math.nan, check_all)
    assert not isnan(datetime(2000, 1, 1), check_all)
    assert not isnan(timedelta(seconds=1), check_all)
    assert not isnan("foo", check_all)


@requires_numpy()
def test_isnan_numpy():
    import numpy as np

    assert isnan(np.nan, True)
    assert isnan(np.nan, False)
    assert not isnan(np.array([0, 0]), True)
    assert isnan(np.array([0, np.nan]), True)
    assert not isnan(np.array(["A", "B"]), True)
    np.testing.assert_equal(
        isnan(np.array([1, np.nan]), False), np.array([False, True])
    )
    np.testing.assert_equal(
        isnan(np.array(["A", "B"]), False), np.array([False, False])
    )


@requires_numpy()
def test_isnan_nat():
    import numpy as np

    a = np.array(["2000-01-01", "NaT"], dtype="M8")
    b = np.array(["2000-01-01", "2000-01-02"], dtype="M8")
    assert isnan(a, True)
    assert not isnan(b, True)
    np.testing.assert_equal(isnan(a, False), np.array([False, True]))
    np.testing.assert_equal(isnan(b, False), np.array([False, False]))

    # Scalar numpy.datetime64
    assert not isnan(a[0], True)
    assert not isnan(a[0], False)
    assert isnan(a[1], True)
    assert isnan(a[1], False)


@pytest.mark.parametrize("check_all", [False, True])
def test_zero_or_nan(check_all):
    assert zero_or_nan(0, check_all)
    assert zero_or_nan(math.nan, check_all)
    assert not zero_or_nan(1, check_all)
    assert not zero_or_nan(datetime(2000, 1, 1), check_all)
    assert not zero_or_nan(timedelta(seconds=1), check_all)
    assert not zero_or_nan("foo", check_all)


@requires_numpy()
def test_zero_or_nan_numpy():
    import numpy as np

    assert zero_or_nan(np.nan, True)
    assert zero_or_nan(np.nan, False)
    assert zero_or_nan(np.array([0, np.nan]), True)
    assert not zero_or_nan(np.array([1, np.nan]), True)
    assert not zero_or_nan(np.array([0, 1]), True)
    assert not zero_or_nan(np.array(["A", "B"]), True)
    np.testing.assert_equal(
        zero_or_nan(np.array([0, 1, np.nan]), False), np.array([True, False, True])
    )
