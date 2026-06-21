import pytest
import pandas as pd
from src.tools.ternary_diagrams.qapf.data import normalize_qapf, load_and_validate_data
import os

def test_normalization():
    df = pd.DataFrame({
        'Q': [10, 0, 0],
        'A': [20, 30, 50],
        'P': [35, 40, 50],
        'F': [0, 10, 0]
    })
    
    normalized = normalize_qapf(df)
    
    assert len(normalized) == 3
    
    # First row is QAP
    assert normalized.iloc[0]['type'] == 'QAP'
    assert normalized.iloc[0]['Q'] == 10
    # A=20, P=35. Total=55. P_ratio = 35/55
    assert abs(normalized.iloc[0]['P_ratio'] - (35/55)) < 0.001
    
    # Second row is APF
    assert normalized.iloc[1]['type'] == 'APF'
    assert normalized.iloc[1]['F'] == 10
    # A=30, P=40. Total=70. P_ratio = 40/70
    assert abs(normalized.iloc[1]['P_ratio'] - (40/70)) < 0.001

    # Third row has no Q and no F (should fall back to QAP line with Q=0)
    assert normalized.iloc[2]['type'] == 'QAP'
    assert normalized.iloc[2]['Q'] == 0
    assert normalized.iloc[2]['P_ratio'] == 0.5

def test_validation_q_and_f():
    csv_path = 'temp_test.csv'
    pd.DataFrame({'Q': [10], 'A': [20], 'P': [30], 'F': [10]}).to_csv(csv_path, index=False)
    
    df, mode, error = load_and_validate_data(csv_path)
    
    assert df is None
    assert "Quartz and Foids cannot exist in the same rock" in error
    
    os.remove(csv_path)
    
def test_missing_columns():
    csv_path = 'temp_test.csv'
    pd.DataFrame({'Q': [10], 'P': [30]}).to_csv(csv_path, index=False)
    
    df, mode, error = load_and_validate_data(csv_path)
    
    assert df is None
    assert "Column 'A' is missing" in error
    
    os.remove(csv_path)

def test_valid_data():
    csv_path = 'temp_test.csv'
    pd.DataFrame({'Q': [10], 'A': [20], 'P': [30]}).to_csv(csv_path, index=False)
    
    df, mode, error = load_and_validate_data(csv_path)
    
    assert error is None
    assert df is not None
    assert mode == 'QAP'
    assert len(df) == 1
    
    os.remove(csv_path)

def test_aliases():
    csv_path = 'temp_test.csv'
    pd.DataFrame({'Quartz': [10], 'Alkali Feldspar': [20], 'Plagioclase': [30]}).to_csv(csv_path, index=False)
    
    df, mode, error = load_and_validate_data(csv_path)
    
    assert error is None
    assert 'Q' in df.columns
    assert 'A' in df.columns
    assert 'P' in df.columns
    
    os.remove(csv_path)
