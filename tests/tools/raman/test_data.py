import os
import pytest
from tools.raman.data import load_and_validate_data

def test_load_and_validate_data(tmp_path):
    # Create a mock data file
    content = """# Some header
# Another header
53,0749	610,25
54,9771	686,092
56,8789	744,684
"""
    file_path = tmp_path / "mock_raman.txt"
    file_path.write_text(content)
    
    df, error = load_and_validate_data(str(file_path))
    
    assert error is None
    assert df is not None
    assert len(df) == 3
    assert list(df.columns) == ['Raman Shift', 'Intensity']
    assert df.iloc[0]['Raman Shift'] == 53.0749
    assert df.iloc[0]['Intensity'] == 610.25

def test_load_invalid_data(tmp_path):
    content = """# Only headers
# No data
"""
    file_path = tmp_path / "mock_invalid.txt"
    file_path.write_text(content)
    
    df, error = load_and_validate_data(str(file_path))
    
    assert error is not None
    assert df is None
