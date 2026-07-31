import pytest
import pandas as pd
import matplotlib.pyplot as plt
from tools.raman.plot import plot_raman

def test_plot_raman():
    df1 = pd.DataFrame({
        'Raman Shift': [100.0, 200.0, 300.0, 400.0],
        'Intensity': [50.0, 150.0, 75.0, 50.0]
    })
    
    df2 = pd.DataFrame({
        'Raman Shift': [100.0, 200.0, 300.0, 400.0],
        'Intensity': [60.0, 160.0, 85.0, 60.0]
    })
    
    dfs_dict = {'file1.txt': df1, 'file2.txt': df2}
    
    fig = plot_raman(dfs_dict, dark_mode=True)
    assert isinstance(fig, plt.Figure)
    
    ax = fig.axes[0]
    # Check labels
    assert ax.get_xlabel() == 'Raman Shift (cm$^{-1}$)'
    assert ax.get_ylabel() == 'Intensity (Counts)'
    
    # Check that a line was plotted
    lines = ax.get_lines()
    assert len(lines) > 0
