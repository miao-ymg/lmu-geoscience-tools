import pytest
import pandas as pd
from tools.ultramafic.data import extract_and_normalize, load_column_mappings

class TestUltramaficData:
    def test_pure_dunite(self):
        df = pd.DataFrame({'Ol': [100], 'Opx': [0], 'Cpx': [0]})
        result = extract_and_normalize(df)
        assert len(result) == 1
        assert result.iloc[0]['Ol'] == 100
        assert result.iloc[0]['Opx'] == 0

    def test_pure_harzburgite(self):
        df = pd.DataFrame({'Ol': [50], 'Opx': [48], 'Cpx': [2]})
        result = extract_and_normalize(df)
        assert result.iloc[0]['Ol'] == 50
        assert result.iloc[0]['Opx'] == 48
        assert result.iloc[0]['Cpx'] == 2

    def test_normalization(self):
        df = pd.DataFrame({'Ol': [50], 'Opx': [50], 'Cpx': [0]})
        result = extract_and_normalize(df)
        assert result.iloc[0]['Ol'] == 50
        assert result.iloc[0]['Opx'] == 50
        
        # Test non-100 sum
        df2 = pd.DataFrame({'Ol': [5], 'Opx': [5], 'Cpx': [0]})
        result2 = extract_and_normalize(df2)
        assert result2.iloc[0]['Ol'] == 50
        assert result2.iloc[0]['Opx'] == 50
        assert result2.iloc[0]['Cpx'] == 0

    def test_missing_columns(self):
        df = pd.DataFrame({'Ol': [100], 'Opx': [0]})
        with pytest.raises(ValueError):
            extract_and_normalize(df)

    def test_german_columns(self):
        df = pd.DataFrame({'Olivin': [40], 'Orthopyroxen': [30], 'Klinopyroxen': [30]})
        result = extract_and_normalize(df)
        assert result.iloc[0]['Ol'] == 40
        assert result.iloc[0]['Opx'] == 30
        assert result.iloc[0]['Cpx'] == 30

    def test_zero_row_skipped(self):
        df = pd.DataFrame({'Ol': [100, 0], 'Opx': [0, 0], 'Cpx': [0, 0]})
        result = extract_and_normalize(df)
        assert len(result) == 1
        assert result.iloc[0]['Ol'] == 100
