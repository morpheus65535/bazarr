import importlib
import os

import pytest

from pint import UnitRegistry

# Conditionally import NumPy, Dask, and Distributed
np = pytest.importorskip("numpy", reason="NumPy is not available")
dask = pytest.importorskip("dask", reason="Dask is not available")
distributed = pytest.importorskip("distributed", reason="Distributed is not available")

from dask.distributed import Client  # isort:skip
from distributed.client import futures_of  # isort:skip
from distributed.utils_test import cluster, gen_cluster, loop  # isort:skip

loop = loop  # flake8

ureg = UnitRegistry(force_ndarray_like=True)
units_ = "kilogram"


def add_five(q):
    return q + 5 * ureg(units_)


@pytest.fixture
def dask_array():
    return dask.array.arange(0, 25, chunks=5, dtype=float).reshape((5, 5))


@pytest.fixture
def numpy_array():
    return np.arange(0, 25, dtype=float).reshape((5, 5)) + 5


def test_is_dask_collection(dask_array):
    """Test that a pint.Quantity wrapped Dask array is a Dask collection."""
    q = ureg.Quantity(dask_array, units_)
    assert dask.is_dask_collection(q)


def test_is_not_dask_collection(numpy_array):
    """Test that other pint.Quantity wrapped objects are not Dask collections."""
    q = ureg.Quantity(numpy_array, units_)
    assert not dask.is_dask_collection(q)


def test_dask_scheduler(dask_array):
    """Test that a pint.Quantity wrapped Dask array has the correct default scheduler."""
    q = ureg.Quantity(dask_array, units_)

    scheduler = q.__dask_scheduler__
    scheduler_name = f"{scheduler.__module__}.{scheduler.__name__}"

    true_name = "dask.threaded.get"

    assert scheduler == dask.array.Array.__dask_scheduler__
    assert scheduler_name == true_name


def test_dask_tokenize(dask_array):
    """Test that a pint.Quantity wrapped Dask array has a unique token."""
    dask_token = dask.base.tokenize(dask_array)
    q = ureg.Quantity(dask_array, units_)

    assert dask.base.tokenize(dask_array) != dask.base.tokenize(q)
    assert dask.base.tokenize(dask_array) == dask_token


def test_dask_optimize(dask_array):
    """Test that a pint.Quantity wrapped Dask array can be optimized."""
    q = ureg.Quantity(dask_array, units_)

    assert q.__dask_optimize__ == dask.array.Array.__dask_optimize__


def test_compute(dask_array, numpy_array):
    """Test the compute() method on a pint.Quantity wrapped Dask array."""
    q = ureg.Quantity(dask_array, units_)

    comps = add_five(q)
    res = comps.compute()

    assert np.all(res.m == numpy_array)
    assert not dask.is_dask_collection(res)
    assert res.units == units_
    assert q.magnitude is dask_array


def test_persist(dask_array, numpy_array):
    """Test the persist() method on a pint.Quantity wrapped Dask array."""
    q = ureg.Quantity(dask_array, units_)

    comps = add_five(q)
    res = comps.persist()

    assert np.all(res.m == numpy_array)
    assert dask.is_dask_collection(res)
    assert res.units == units_
    assert q.magnitude is dask_array


@pytest.mark.skipif(
    importlib.util.find_spec("graphviz") is None, reason="GraphViz is not available"
)
def test_visualize(dask_array):
    """Test the visualize() method on a pint.Quantity wrapped Dask array."""
    q = ureg.Quantity(dask_array, units_)

    comps = add_five(q)
    res = comps.visualize()

    assert res is None
    # These commands only work on Unix and Windows
    assert os.path.exists("mydask.png")
    os.remove("mydask.png")


def test_compute_persist_equivalent(dask_array, numpy_array):
    """Test that compute() and persist() return the same numeric results."""
    q = ureg.Quantity(dask_array, units_)

    comps = add_five(q)
    res_compute = comps.compute()
    res_persist = comps.persist()

    assert np.all(res_compute == res_persist)
    assert res_compute.units == res_persist.units == units_


@pytest.mark.parametrize("method", ["compute", "persist", "visualize"])
def test_exception_method_not_implemented(numpy_array, method):
    """Test exception handling for convenience methods on a pint.Quantity wrapped
    object that is not a dask.array.Array object.
    """
    q = ureg.Quantity(numpy_array, units_)

    exctruth = (
        f"Method {method} only implemented for objects of"
        " <class 'dask.array.core.Array'>, not"
        " <class 'numpy.ndarray'>"
    )
    with pytest.raises(AttributeError, match=exctruth):
        obj_method = getattr(q, method)
        obj_method()


def test_distributed_compute(loop, dask_array, numpy_array):
    """Test compute() for distributed machines."""
    q = ureg.Quantity(dask_array, units_)

    with cluster() as (s, [a, b]):
        with Client(s["address"], loop=loop):
            comps = add_five(q)
            res = comps.compute()

            assert np.all(res.m == numpy_array)
            assert not dask.is_dask_collection(res)
            assert res.units == units_

    assert q.magnitude is dask_array


def test_distributed_persist(loop, dask_array):
    """Test persist() for distributed machines."""
    q = ureg.Quantity(dask_array, units_)

    with cluster() as (s, [a, b]):
        with Client(s["address"], loop=loop):
            comps = add_five(q)
            persisted_q = comps.persist()

            comps_truth = dask_array + 5
            persisted_truth = comps_truth.persist()

            assert np.all(persisted_q.m == persisted_truth)
            assert dask.is_dask_collection(persisted_q)
            assert persisted_q.units == units_

    assert q.magnitude is dask_array


@gen_cluster(client=True, timeout=None)
async def test_async(c, s, a, b):
    """Test asynchronous operations."""
    da = dask.array.arange(0, 25, chunks=5, dtype=float).reshape((5, 5))
    q = ureg.Quantity(da, units_)

    x = q + ureg.Quantity(5, units_)
    y = x.persist()
    assert str(y)

    assert dask.is_dask_collection(y)
    assert len(x.__dask_graph__()) > len(y.__dask_graph__())

    assert not futures_of(x)
    assert futures_of(y)

    future = c.compute(y)
    w = await future
    assert not dask.is_dask_collection(w)

    truth = np.arange(0, 25, dtype=float).reshape((5, 5)) + 5
    assert np.all(truth == w.m)
