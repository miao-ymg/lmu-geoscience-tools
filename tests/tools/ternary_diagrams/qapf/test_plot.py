import pytest
import pandas as pd
from src.tools.ternary_diagrams.qapf.plot import plot_qapf
import matplotlib

# Use a non-interactive backend for testing
matplotlib.use('Agg')

def test_plot_qapf():
    df = pd.DataFrame({
        'type': ['QAP', 'APF'],
        'Q': [20, 0],
        'A': [40, 50],
        'P': [40, 30],
        'F': [0, 20]
    })
    
    fig = plot_qapf(df)
    
    assert fig is not None
    # If no exception was raised, test passes
