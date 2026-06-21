import pytest
import pandas as pd
import matplotlib
matplotlib.use('Agg')
from tools.tas.plot import plot_tas

def test_plot_tas_dark_mode():
    data = {'SiO2': [60.0, 70.0], 'Total_Alkali': [10.0, 5.0]}
    df = pd.DataFrame(data)
    
    fig = plot_tas(df, dark_mode=True)
    
    # Assert figure exists and has expected properties
    assert fig is not None
    assert len(fig.axes) > 0
    
    # Check background color
    # The figure facecolor in the plot_tas function is set to #1e1e1e
    assert matplotlib.colors.to_hex(fig.get_facecolor()) == '#1e1e1e'

def test_plot_tas_light_mode():
    data = {'SiO2': [60.0], 'Total_Alkali': [10.0]}
    df = pd.DataFrame(data)
    
    fig = plot_tas(df, dark_mode=False)
    
    assert fig is not None
    assert matplotlib.colors.to_hex(fig.get_facecolor()) == '#ffffff'

def test_plot_tas_empty_data():
    df = pd.DataFrame(columns=['SiO2', 'Total_Alkali'])
    
    fig = plot_tas(df, dark_mode=False)
    
    assert fig is not None
