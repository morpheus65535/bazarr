import pytest

from pint import UnitRegistry

# Conditionally import NumPy and any upcast type libraries
np = pytest.importorskip("numpy", reason="NumPy is not available")
sparse = pytest.importorskip("sparse", reason="sparse is not available")
da = pytest.importorskip("dask.array", reason="Dask is not available")

# Set up unit registry and sample
ureg = UnitRegistry(force_ndarray_like=True)
q_base = (np.arange(25).reshape(5, 5).T + 1) * ureg.kg


# Define identity function for use in tests
def identity(x):
    return x


@pytest.fixture(params=["sparse", "masked_array", "dask_array"])
def array(request):
    """Generate 5x5 arrays of given type for tests."""
    if request.param == "sparse":
        # Create sample sparse COO as a permutation matrix.
        coords = [[0, 1, 2, 3, 4], [1, 3, 0, 2, 4]]
        data = [1.0] * 5
        return sparse.COO(coords, data, shape=(5, 5))
    elif request.param == "masked_array":
        # Create sample masked array as an upper triangular matrix.
        return np.ma.masked_array(
            np.arange(25, dtype=np.float).reshape((5, 5)),
            mask=np.logical_not(np.triu(np.ones((5, 5)))),
        )
    elif request.param == "dask_array":
        return da.arange(25, chunks=5, dtype=float).reshape((5, 5))


@pytest.mark.parametrize(
    "op, magnitude_op, unit_op",
    [
        pytest.param(identity, identity, identity, id="identity"),
        pytest.param(
            lambda x: x + 1 * ureg.m, lambda x: x + 1, identity, id="addition"
        ),
        pytest.param(
            lambda x: x - 20 * ureg.cm, lambda x: x - 0.2, identity, id="subtraction"
        ),
        pytest.param(
            lambda x: x * (2 * ureg.s),
            lambda x: 2 * x,
            lambda u: u * ureg.s,
            id="multiplication",
        ),
        pytest.param(
            lambda x: x / (1 * ureg.s), identity, lambda u: u / ureg.s, id="division"
        ),
        pytest.param(lambda x: x ** 2, lambda x: x ** 2, lambda u: u ** 2, id="square"),
        pytest.param(lambda x: x.T, lambda x: x.T, identity, id="transpose"),
        pytest.param(np.mean, np.mean, identity, id="mean ufunc"),
        pytest.param(np.sum, np.sum, identity, id="sum ufunc"),
        pytest.param(np.sqrt, np.sqrt, lambda u: u ** 0.5, id="sqrt ufunc"),
        pytest.param(
            lambda x: np.reshape(x, (25,)),
            lambda x: np.reshape(x, (25,)),
            identity,
            id="reshape function",
        ),
        pytest.param(np.amax, np.amax, identity, id="amax function"),
    ],
)
def test_univariate_op_consistency(op, magnitude_op, unit_op, array):
    q = ureg.Quantity(array, "meter")
    res = op(q)
    assert np.all(res.magnitude == magnitude_op(array))  # Magnitude check
    assert res.units == unit_op(q.units)  # Unit check
    assert q.magnitude is array  # Immutability check


@pytest.mark.parametrize(
    "op, unit",
    [
        pytest.param(lambda x, y: x * y, ureg("kg m"), id="multiplication"),
        pytest.param(lambda x, y: x / y, ureg("m / kg"), id="division"),
        pytest.param(np.multiply, ureg("kg m"), id="multiply ufunc"),
    ],
)
def test_bivariate_op_consistency(op, unit, array):
    q = ureg.Quantity(array, "meter")
    res = op(q, q_base)
    assert np.all(res.magnitude == op(array, q_base.magnitude))  # Magnitude check
    assert res.units == unit  # Unit check
    assert q.magnitude is array  # Immutability check


@pytest.mark.parametrize(
    "op",
    [
        pytest.param(
            lambda a, u: a * u,
            id="array-first",
            marks=pytest.mark.xfail(reason="upstream issue numpy/numpy#15200"),
        ),
        pytest.param(lambda a, u: u * a, id="unit-first"),
    ],
)
@pytest.mark.parametrize(
    "unit",
    [pytest.param(ureg.m, id="Unit"), pytest.param(ureg("meter"), id="Quantity")],
)
def test_array_quantity_creation_by_multiplication(op, unit, array):
    assert type(op(array, unit)) == ureg.Quantity
