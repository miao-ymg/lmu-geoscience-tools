"""
Unit tests for feldspar data loading and endmember computation.
"""
import os
import pytest
import pandas as pd
from tools.feldspar.data import load_and_validate_data, compute_feldspar_endmembers, MOLAR_MASSES


# ── Endmember computation ─────────────────────────────────────────────────────

class TestComputeFeldsparEndmembers:

    def _make_df(self, na, k, ca):
        return pd.DataFrame({'Na': [na], 'K': [k], 'Ca': [ca]})

    def test_pure_albite(self):
        """100 % Na → Ab=1, Or=0, An=0"""
        df = self._make_df(na=22.990, k=0.0, ca=0.0)
        result = compute_feldspar_endmembers(df)
        assert len(result) == 1
        assert pytest.approx(result.iloc[0]['Ab'], abs=1e-6) == 1.0
        assert pytest.approx(result.iloc[0]['Or'], abs=1e-6) == 0.0
        assert pytest.approx(result.iloc[0]['An'], abs=1e-6) == 0.0

    def test_pure_orthoclase(self):
        """100 % K → Ab=0, Or=1, An=0"""
        df = self._make_df(na=0.0, k=39.098, ca=0.0)
        result = compute_feldspar_endmembers(df)
        assert pytest.approx(result.iloc[0]['Or'], abs=1e-6) == 1.0
        assert pytest.approx(result.iloc[0]['Ab'], abs=1e-6) == 0.0
        assert pytest.approx(result.iloc[0]['An'], abs=1e-6) == 0.0

    def test_pure_anorthite(self):
        """100 % Ca → Ab=0, Or=0, An=1"""
        df = self._make_df(na=0.0, k=0.0, ca=40.078)
        result = compute_feldspar_endmembers(df)
        assert pytest.approx(result.iloc[0]['An'], abs=1e-6) == 1.0

    def test_endmembers_sum_to_one(self):
        """Ab + Or + An must always equal 1 for any valid input."""
        df = self._make_df(na=5.0, k=3.0, ca=2.0)
        result = compute_feldspar_endmembers(df)
        total = result.iloc[0]['Ab'] + result.iloc[0]['Or'] + result.iloc[0]['An']
        assert pytest.approx(total, abs=1e-9) == 1.0

    def test_zero_row_skipped(self):
        """A row where Na=K=Ca=0 should be skipped (division by zero avoided)."""
        df = pd.DataFrame({'Na': [0.0, 5.0], 'K': [0.0, 3.0], 'Ca': [0.0, 2.0]})
        result = compute_feldspar_endmembers(df)
        assert len(result) == 1

    def test_multiple_samples(self):
        """Multiple rows each produce one result row."""
        df = pd.DataFrame({
            'Na': [5.0, 3.0, 0.0],
            'K':  [3.0, 5.0, 39.098],
            'Ca': [2.0, 2.0, 0.0],
        })
        result = compute_feldspar_endmembers(df)
        assert len(result) == 3

    def test_molar_mass_used_correctly(self):
        """
        Given equal mass percentages, Ca should produce fewer moles than Na
        because Ca has a higher molar mass, so An < Ab.
        """
        df = self._make_df(na=10.0, k=0.0, ca=10.0)
        result = compute_feldspar_endmembers(df)
        # mol_Na = 10/22.99 ≈ 0.435,  mol_Ca = 10/40.08 ≈ 0.249
        # → Ab > An
        assert result.iloc[0]['Ab'] > result.iloc[0]['An']

    def test_known_values(self):
        """Cross-check against manually computed values."""
        na_mass, k_mass, ca_mass = 7.0, 0.5, 5.5
        mol_na = na_mass / MOLAR_MASSES['Na']
        mol_k  = k_mass  / MOLAR_MASSES['K']
        mol_ca = ca_mass / MOLAR_MASSES['Ca']
        total  = mol_na + mol_k + mol_ca

        df = self._make_df(na=na_mass, k=k_mass, ca=ca_mass)
        result = compute_feldspar_endmembers(df)

        assert pytest.approx(result.iloc[0]['Ab'], rel=1e-6) == mol_na / total
        assert pytest.approx(result.iloc[0]['Or'], rel=1e-6) == mol_k  / total
        assert pytest.approx(result.iloc[0]['An'], rel=1e-6) == mol_ca / total


# ── Data loading from real sample files ───────────────────────────────────────

def _sample_dir():
    """Absolute path to the feldspar example data folder."""
    return os.path.join(
        os.path.dirname(__file__),       # tests/tools/feldspar/
        '..', '..', '..',                # repo root
        'data', 'examples',
        'REM-Daten_vorbereitet_nur-Feldspar'
    )


def _sample_files():
    d = _sample_dir()
    try:
        return [
            os.path.join(d, f)
            for f in os.listdir(d)
            if f.endswith('.xlsx') and not f.startswith('~')
        ]
    except FileNotFoundError:
        return []


@pytest.mark.parametrize("filepath", _sample_files())
def test_load_real_file(filepath):
    """Each sample file must load without errors."""
    df, error = load_and_validate_data(filepath)
    assert error is None, f"Unexpected error for {os.path.basename(filepath)}: {error}"
    assert df is not None
    assert not df.empty
    for col in ['Na', 'K', 'Ca']:
        assert col in df.columns


@pytest.mark.parametrize("filepath", _sample_files())
def test_endmembers_from_real_file(filepath):
    """Endmembers computed from each real file must be in [0,1] and sum to 1."""
    df, error = load_and_validate_data(filepath)
    assert error is None
    result = compute_feldspar_endmembers(df)
    assert not result.empty
    for _, row in result.iterrows():
        total = row['Ab'] + row['Or'] + row['An']
        assert pytest.approx(total, abs=1e-6) == 1.0
        assert 0.0 <= row['Ab'] <= 1.0
        assert 0.0 <= row['Or'] <= 1.0
        assert 0.0 <= row['An'] <= 1.0
