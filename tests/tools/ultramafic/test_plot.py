import pytest
import pandas as pd
import matplotlib.pyplot as plt
from tools.ultramafic.plot import plot_ultramafic

class TestUltramaficPlot:
    def test_plot_returns_figure(self):
        fig = plot_ultramafic()
        assert fig is not None
        assert isinstance(fig, plt.Figure)
        
    def test_plot_with_data(self):
        df = pd.DataFrame({'Ol': [50], 'Opx': [25], 'Cpx': [25]})
        fig = plot_ultramafic(df)
        assert fig is not None
        assert isinstance(fig, plt.Figure)
