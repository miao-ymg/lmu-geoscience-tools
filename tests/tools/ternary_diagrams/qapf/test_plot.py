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
        'P_ratio': [0.5, 0.25],
        'F': [0, 20]
    })
    
    fig = plot_qapf(df, mode='QAPF')
    assert fig is not None

def test_plot_qap_only():
    df = pd.DataFrame({
        'type': ['QAP'],
        'Q': [20],
        'P_ratio': [0.5],
        'F': [0]
    })
    
    fig = plot_qapf(df, mode='QAP')
    assert fig is not None

def test_plot_apf_only():
    df = pd.DataFrame({
        'type': ['APF'],
        'Q': [0],
        'P_ratio': [0.5],
        'F': [20]
    })
    
    fig = plot_qapf(df, mode='APF')
    assert fig is not None
