import pytest

from pint import UnitRegistry

# Conditionally import NumPy and any upcast type libraries
np = pytest.importorskip("numpy", reason="NumPy is not available")
xr = pytest.importorskip("xarray", reason="xarray is not available")

# Set up unit registry and sample
ureg = UnitRegistry()
q = [[1.0, 2.0], [3.0, 4.0]] * ureg.m


@pytest.fixture
def da():
    return xr.DataArray(q.copy())


@pytest.fixture
def ds():
    return xr.tutorial.load_dataset("air_temperature")


def test_xarray_quantity_creation():
    with pytest.raises(TypeError) as exc:
        ureg.Quantity(xr.DataArray(np.arange(4)), "m")
        assert "Quantity cannot wrap upcast type" in str(exc)
    assert xr.DataArray(q).data is q


def test_quantification(ds):
    da = ds["air"][0]
    da.data = ureg.Quantity(da.values, da.attrs.pop("units"))
    mean = da.mean().item()
    assert mean.units == ureg.K
    assert np.isclose(mean, 274.166259765625 * ureg.K)


@pytest.mark.parametrize(
    "op",
    [
        lambda x, y: x + y,
        lambda x, y: x - (-y),
        lambda x, y: x * y,
        lambda x, y: x / (y ** -1),
    ],
)
@pytest.mark.parametrize(
    "pair",
    [
        (q, xr.DataArray(q)),
        (
            xr.DataArray([1.0, 2.0] * ureg.m, dims=("y",)),
            xr.DataArray(
                np.arange(6, dtype="float").reshape(3, 2, 1), dims=("z", "y", "x")
            )
            * ureg.km,
        ),
        (1 * ureg.m, xr.DataArray(q)),
    ],
)
def test_binary_arithmetic_commutativity(op, pair):
    z0 = op(*pair)
    z1 = op(*pair[::-1])
    z1 = z1.transpose(*z0.dims)
    assert np.all(np.isclose(z0.data, z1.data.to(z0.data.units)))


def test_eq_commutativity(da):
    assert np.all((q.T == da) == (da.transpose() == q))


def test_ne_commutativity(da):
    assert np.all((q != da.transpose()) == (da != q.T))


def test_dataset_operation_with_unit(ds):
    ds0 = ureg.K * ds.isel(time=0)
    ds1 = (ds * ureg.K).isel(time=0)
    xr.testing.assert_identical(ds0, ds1)
    assert np.isclose(ds0["air"].mean().item(), 274.166259765625 * ureg.K)


def test_dataarray_inplace_arithmetic_roundtrip(da):
    da_original = da.copy()
    q_to_modify = q.copy()
    da += q
    xr.testing.assert_identical(da, xr.DataArray([[2, 4], [6, 8]] * ureg.m))
    da -= q
    xr.testing.assert_identical(da, da_original)
    da *= ureg.m
    xr.testing.assert_identical(da, xr.DataArray(q * ureg.m))
    da /= ureg.m
    xr.testing.assert_identical(da, da_original)
    # Operating inplace with DataArray converts to DataArray
    q_to_modify += da
    q_to_modify -= da
    assert np.all(np.isclose(q_to_modify.data, q))


def test_dataarray_inequalities(da):
    xr.testing.assert_identical(
        2 * ureg.m > da, xr.DataArray([[True, False], [False, False]])
    )
    xr.testing.assert_identical(
        2 * ureg.m < da, xr.DataArray([[False, False], [True, True]])
    )
    with pytest.raises(ValueError) as exc:
        da > 2
        assert "Cannot compare Quantity and <class 'int'>" in str(exc)


def test_array_function_deferral(da):
    lower = 2 * ureg.m
    upper = 3 * ureg.m
    args = (da, lower, upper)
    assert (
        lower.__array_function__(
            np.clip, tuple(set(type(arg) for arg in args)), args, {}
        )
        is NotImplemented
    )


def test_array_ufunc_deferral(da):
    lower = 2 * ureg.m
    assert lower.__array_ufunc__(np.maximum, "__call__", lower, da) is NotImplemented
