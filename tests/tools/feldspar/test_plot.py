"""Tests for the feldspar plot module."""
import pytest
import pandas as pd
import matplotlib
matplotlib.use('Agg')
from tools.feldspar.plot import plot_feldspar


def _sample_endmembers():
    return pd.DataFrame({
        'Ab': [0.7, 0.5, 0.3],
        'Or': [0.1, 0.3, 0.2],
        'An': [0.2, 0.2, 0.5],
    })


def test_plot_returns_figure():
    df = _sample_endmembers()
    fig = plot_feldspar(df, dark_mode=True)
    assert fig is not None
    assert len(fig.axes) > 0


def test_plot_dark_mode_bg():
    df = _sample_endmembers()
    fig = plot_feldspar(df, dark_mode=True)
    assert matplotlib.colors.to_hex(fig.get_facecolor()) == '#1e1e1e'


def test_plot_light_mode_bg():
    df = _sample_endmembers()
    fig = plot_feldspar(df, dark_mode=False)
    assert matplotlib.colors.to_hex(fig.get_facecolor()) == '#ffffff'


def test_plot_empty_dataframe():
    """An empty DataFrame must still produce a figure (just no data points)."""
    df = pd.DataFrame(columns=['Ab', 'Or', 'An'])
    fig = plot_feldspar(df, dark_mode=False)
    assert fig is not None
