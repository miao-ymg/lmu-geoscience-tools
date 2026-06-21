import pytest
import pandas as pd
from tools.tas.data import normalize_tas

def test_normalize_tas():
    # Example raw data (unnormalized)
    # Total sum excluding LOI is 60+10+10 = 80
    data = {
        'sio2': [60],
        'na2o': [10],
        'k2o': [10],
        'mgo': [20],
        'loi': [5] # should be ignored
    }
    df = pd.DataFrame(data)
    
    # 60 + 10 + 10 + 20 = 100 sum without loi
    
    # Wait, my sum was 100
    
    normalized_df = normalize_tas(df)
    
    assert len(normalized_df) == 1
    # 60 / 100 * 100 = 60
    assert normalized_df.iloc[0]['SiO2'] == 60.0
    # Na2O (10) + K2O (10) = 20
    assert normalized_df.iloc[0]['Total_Alkali'] == 20.0

def test_normalize_tas_ignores_invalid_rows():
    data = {
        'sio2': [60, 'invalid', 0],
        'na2o': [10, 10, 0],
        'k2o': [10, 10, 0],
        'mgo': [20, 20, 0],
        'loi': [5, 5, 5]
    }
    df = pd.DataFrame(data)
    
    normalized_df = normalize_tas(df)
    
    # Second row has 'invalid' sio2, so it should be treated as 0 and the rest normalized.
    # Actually, the parsing handles invalid by setting to 0, so sum is 10+10+20 = 40.
    # SiO2 = 0, Total_Alkali = 20 / 40 * 100 = 50.0
    # Third row has sum = 0 so it's skipped.
    assert len(normalized_df) == 2
    assert normalized_df.iloc[1]['SiO2'] == 0.0
    assert normalized_df.iloc[1]['Total_Alkali'] == 50.0
