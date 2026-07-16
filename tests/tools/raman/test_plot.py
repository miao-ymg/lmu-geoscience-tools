import pytest
import pandas as pd
import matplotlib.pyplot as plt
from tools.raman.plot import plot_raman

def test_plot_raman():
    df = pd.DataFrame({
        'Raman Shift': [100.0, 200.0, 300.0],
        'Intensity': [50.0, 150.0, 75.0]
    })
    
    fig = plot_raman(df, dark_mode=True)
    assert isinstance(fig, plt.Figure)
    
    ax = fig.axes[0]
    # Check labels
    assert ax.get_xlabel() == 'Raman Shift (cm$^{-1}$)'
    assert ax.get_ylabel() == 'Intensity (counts)'
    
    # Check that a line was plotted
    lines = ax.get_lines()
    assert len(lines) > 0
