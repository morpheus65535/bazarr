import pytest

from pint import UnitRegistry

# Conditionally import matplotlib and NumPy
plt = pytest.importorskip("matplotlib.pyplot", reason="matplotlib is not available")
np = pytest.importorskip("numpy", reason="NumPy is not available")

# Set up unit registry for matplotlib
ureg = UnitRegistry()
ureg.setup_matplotlib(True)

# Set up matplotlib
plt.switch_backend("agg")


@pytest.mark.mpl_image_compare(tolerance=0, remove_text=True)
def test_basic_plot():
    y = np.linspace(0, 30) * ureg.miles
    x = np.linspace(0, 5) * ureg.hours

    fig, ax = plt.subplots()
    ax.plot(x, y, "tab:blue")
    ax.axhline(26400 * ureg.feet, color="tab:red")
    ax.axvline(120 * ureg.minutes, color="tab:green")

    return fig


@pytest.mark.mpl_image_compare(tolerance=0, remove_text=True)
def test_plot_with_set_units():
    y = np.linspace(0, 30) * ureg.miles
    x = np.linspace(0, 5) * ureg.hours

    fig, ax = plt.subplots()
    ax.yaxis.set_units(ureg.inches)
    ax.xaxis.set_units(ureg.seconds)

    ax.plot(x, y, "tab:blue")
    ax.axhline(26400 * ureg.feet, color="tab:red")
    ax.axvline(120 * ureg.minutes, color="tab:green")

    return fig
