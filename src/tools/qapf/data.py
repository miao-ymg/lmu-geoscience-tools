import pandas as pd
import os
import yaml

# Load aliases from yaml
current_dir = os.path.dirname(os.path.abspath(__file__))
yaml_path = os.path.join(current_dir, 'column_aliases.yml')
with open(yaml_path, 'r') as f:
    ALIASES = yaml.safe_load(f)

def normalize_column_name(col_name):
    """
    Given a column name, returns the standard internal name (Q, A, P, or F)
    if it matches any of the aliases. Otherwise returns the original name.
    """
    key_mapping = {
        'QUARTZ': 'Q',
        'ALKALI FELDSPAR': 'A',
        'PLAGIOCLASE': 'P',
        'FOID': 'F'
    }
    col_upper = str(col_name).strip().upper()
    for full_name, alias_list in ALIASES.items():
        if col_upper in alias_list:
            return key_mapping.get(full_name, full_name)
    return col_upper

def load_and_validate_data(file_path):
    """Loads and validates QAPF data from Excel or CSV."""
    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith('.xlsx') or file_path.endswith('.xls'):
            df = pd.read_excel(file_path)
        else:
            return None, None, "The file could not be opened. Please make sure it is an Excel or CSV file."
    except Exception:
        return None, None, "The file could not be opened. Please check if it's corrupted or currently open in another program."

    # Normalize column names using aliases
    df.columns = [normalize_column_name(c) for c in df.columns]

    # Required columns: A, P, and at least Q or F
    required_base = ['A', 'P']
    for col in required_base:
        if col not in df.columns:
            return None, None, f"Column '{col}' is missing from your file. Please check the column names."

    if 'Q' not in df.columns and 'F' not in df.columns:
        return None, None, "Your file must contain at least a 'Q' (Quartz) or 'F' (Foid) column."

    # Fill missing optional columns with 0
    if 'Q' not in df.columns:
        df['Q'] = 0
    if 'F' not in df.columns:
        df['F'] = 0

    # Ensure numeric
    for col in ['Q', 'A', 'P', 'F']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Validation: Q and F cannot be both > 0 in any row
    for index, row in df.iterrows():
        if row['Q'] > 0 and row['F'] > 0:
            return None, None, f"Row {index + 2} contains values for both Q and F. Quartz and Foids cannot exist in the same rock. Please correct your data."

    # Determine diagram mode
    q_sum = df['Q'].sum()
    f_sum = df['F'].sum()
    
    if q_sum > 0 and f_sum == 0:
        mode = 'QAP'
    elif f_sum > 0 and q_sum == 0:
        mode = 'APF'
    else:
        mode = 'QAPF'

    # It's valid
    return df, mode, None

def normalize_qapf(df):
    """Calculates P_ratio for horizontal position and keeps absolute Q/F for vertical position."""
    normalized_data = []

    for _, row in df.iterrows():
        q, a, p, f = row.get('Q', 0), row.get('A', 0), row.get('P', 0), row.get('F', 0)
        
        # Calculate horizontal position ratio P / (A + P)
        ap_sum = a + p
        p_ratio = (p / ap_sum) if ap_sum > 0 else 0.5
        
        if q > 0:
            normalized_data.append({
                'type': 'QAP',
                'Q': q,
                'P_ratio': p_ratio
            })
        elif f > 0:
            normalized_data.append({
                'type': 'APF',
                'F': f,
                'P_ratio': p_ratio
            })
        else:
            # If both Q and F are 0, it lies on the A-P line.
            normalized_data.append({
                'type': 'QAP',
                'Q': 0,
                'P_ratio': p_ratio
            })

    return pd.DataFrame(normalized_data)
