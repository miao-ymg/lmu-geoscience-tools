import pandas as pd
import os
import sys
import yaml

# Molar masses (g/mol) for elements relevant to feldspar calculation
MOLAR_MASSES = {
    'Na': 22.990,
    'K':  39.098,
    'Ca': 40.078,
}


def _get_resource_path(filename):
    """Get absolute path to a resource file in the feldspar package.
    Works both in normal Python execution and inside a PyInstaller bundle."""
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, 'tools', 'feldspar', filename)
    else:
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)


def get_classifications():
    yaml_path = _get_resource_path('classifications.yml')
    if os.path.exists(yaml_path):
        with open(yaml_path, 'r') as f:
            return yaml.safe_load(f)
    return {}


# Load column aliases from yml
_aliases_path = _get_resource_path('column_aliases.yml')
with open(_aliases_path, 'r') as f:
    _ALIASES = yaml.safe_load(f)

# Build a flat lookup: lowercase alias string -> canonical key ('Na', 'K', 'Ca')
_ALIAS_LOOKUP = {}
_CANONICAL_MAP = {
    'SODIUM':    'Na',
    'POTASSIUM': 'K',
    'CALCIUM':   'Ca',
}
for section, canonical in _CANONICAL_MAP.items():
    for alias in _ALIASES.get(section, []):
        _ALIAS_LOOKUP[str(alias).strip().lower()] = canonical


def _resolve_column(col_name: str) -> str:
    """Map a column name to its canonical element symbol, or return the original lowercased name."""
    return _ALIAS_LOOKUP.get(str(col_name).strip().lower(), str(col_name).strip().lower())


def load_and_validate_data(file_path: str):
    """
    Loads feldspar data from an Excel or CSV file.

    Returns (df, error_message). On success, error_message is None and df
    has columns renamed to canonical symbols (Na, K, Ca) plus any extras.
    On failure, df is None and error_message is a human-readable string.
    """
    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path, header=None)
        elif file_path.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_path, header=None)
        else:
            return None, "Unsupported file type. Please upload a CSV or Excel file."
    except Exception as e:
        return None, f"Could not open file: {e}"

    # Find the header row: the first row that contains at least one known alias
    header_idx = -1
    for idx, row in df.iterrows():
        row_lower = [str(v).strip().lower() for v in row]
        if any(v in _ALIAS_LOOKUP for v in row_lower):
            header_idx = idx
            break

    if header_idx == -1:
        return None, (
            "Could not find column headers for Na/K/Ca in the file. "
            "Please check that the file contains columns for Sodium, Potassium, and Calcium."
        )

    # Set header and drop preceding rows
    df.columns = [str(c).strip() for c in df.iloc[header_idx]]
    df = df.iloc[header_idx + 1:].reset_index(drop=True)

    # Rename columns to canonical names BEFORE the unit-row check
    df = df.rename(columns=lambda c: _resolve_column(c))

    # Check that required columns are present
    required = ['Na', 'K', 'Ca']
    missing = [r for r in required if r not in df.columns]
    if missing:
        return None, (
            f"Required column(s) {missing} not found. "
            "Please make sure your file has columns for Sodium (Na), Potassium (K), and Calcium (Ca)."
        )

    # Drop unit row if the first data row is non-numeric for the Na column
    if len(df) > 0:
        try:
            float(str(df['Na'].iloc[0]).replace(',', '.'))
        except (ValueError, TypeError):
            df = df.iloc[1:].reset_index(drop=True)

    # Convert to numeric (handle European comma decimals)
    for col in required:
        df[col] = (
            df[col]
            .astype(str)
            .str.replace(',', '.', regex=False)
        )
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)

    # Drop rows where all three are zero (likely empty/filler rows)
    df = df[~((df['Na'] == 0) & (df['K'] == 0) & (df['Ca'] == 0))].reset_index(drop=True)

    if df.empty:
        return None, "No valid data rows found after parsing. Please check the file."

    return df, None


def compute_feldspar_endmembers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Given a DataFrame with mass-% columns Na, K, Ca, computes the
    mole fractions and then the three feldspar end-member proportions:

      - Albite   (Ab): mol_Na / (mol_Na + mol_K + mol_Ca)
      - Orthoclase (Or): mol_K  / (mol_Na + mol_K + mol_Ca)
      - Anorthite (An): mol_Ca / (mol_Na + mol_K + mol_Ca)

    Returns a DataFrame with columns Ab, Or, An (values in [0, 1]).
    """
    result = []

    for _, row in df.iterrows():
        mol_Na = row['Na'] / MOLAR_MASSES['Na']
        mol_K  = row['K']  / MOLAR_MASSES['K']
        mol_Ca = row['Ca'] / MOLAR_MASSES['Ca']

        total = mol_Na + mol_K + mol_Ca

        if total == 0:
            continue

        result.append({
            'Ab': mol_Na / total,
            'Or': mol_K  / total,
            'An': mol_Ca / total,
        })

    result = pd.DataFrame(result)

    # Classify points
    classifications = get_classifications().get('Default', {})
    classes = []
    for _, row in result.iterrows():
        an, or_ = row['An'] * 100.0, row['Or'] * 100.0
        ab = row['Ab'] * 100.0
        
        # Calculate ratios safely
        an_ratio = (an / (an + ab) * 100.0) if (an + ab) > 1e-9 else 0.0
        or_ratio = (or_ / (or_ + ab) * 100.0) if (or_ + ab) > 1e-9 else 0.0
        ab_ratio = (or_ / (or_ + an) * 100.0) if (or_ + an) > 1e-9 else 0.0
        or_perp = (or_ - ab + 100.0) / 2.0
        
        assigned = "None"
        for class_rule in classifications:
            c_name = class_rule['name']
            match = True
            
            if 'polygon' in class_rule:
                poly = class_rule['polygon']
                poly_pts = [(p['An'], p['Or']) for p in poly]
                inside = False
                n = len(poly_pts)
                p1x, p1y = poly_pts[0]
                for i in range(1, n + 1):
                    p2x, p2y = poly_pts[i % n]
                    if min(p1y, p2y) < or_ <= max(p1y, p2y):
                        if an <= max(p1x, p2x):
                            if p1y != p2y:
                                xints = (or_ - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                            if p1x == p2x or an <= xints:
                                inside = not inside
                    p1x, p1y = p2x, p2y
                if not inside:
                    match = False
            else:
                if 'An' in class_rule:
                    if not (class_rule['An'][0] - 1e-5 <= an <= class_rule['An'][1] + 1e-5):
                        match = False
                if match and 'Or' in class_rule:
                    if not (class_rule['Or'][0] - 1e-5 <= or_ <= class_rule['Or'][1] + 1e-5):
                        match = False
                if match and 'An_ratio' in class_rule:
                    if not (class_rule['An_ratio'][0] - 1e-5 <= an_ratio <= class_rule['An_ratio'][1] + 1e-5):
                        match = False
                if match and 'Or_ratio' in class_rule:
                    if not (class_rule['Or_ratio'][0] - 1e-5 <= or_ratio <= class_rule['Or_ratio'][1] + 1e-5):
                        match = False
                if match and 'Ab_ratio' in class_rule:
                    if not (class_rule['Ab_ratio'][0] - 1e-5 <= ab_ratio <= class_rule['Ab_ratio'][1] + 1e-5):
                        match = False
                if match and 'Or_perp' in class_rule:
                    if not (class_rule['Or_perp'][0] - 1e-5 <= or_perp <= class_rule['Or_perp'][1] + 1e-5):
                        match = False
                    
            if match:
                assigned = c_name
                break
                
        classes.append(assigned)
        
    result['Classification'] = classes
    
    return result
