import pandas as pd

def load_and_validate_data(file_path):
    """Loads and validates QAPF data from Excel or CSV."""
    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith('.xlsx') or file_path.endswith('.xls'):
            df = pd.read_excel(file_path)
        else:
            return None, "The file could not be opened. Please make sure it is an Excel or CSV file."
    except Exception:
        return None, "The file could not be opened. Please check if it's corrupted or currently open in another program."

    # Make columns uppercase for easier checking
    df.columns = [str(c).strip().upper() for c in df.columns]

    # Required columns: A, P, and at least Q or F
    required_base = ['A', 'P']
    for col in required_base:
        if col not in df.columns:
            return None, f"Column '{col}' is missing from your file. Please check the column names."

    if 'Q' not in df.columns and 'F' not in df.columns:
        return None, "Your file must contain at least a 'Q' (Quartz) or 'F' (Foid) column."

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
            return None, f"Row {index + 2} contains values for both Q and F. Quartz and Foids cannot exist in the same rock. Please correct your data."

    # It's valid
    return df, None

def normalize_qapf(df):
    """Normalizes QAP and APF to 100%."""
    normalized_data = []

    for _, row in df.iterrows():
        q, a, p, f = row['Q'], row['A'], row['P'], row['F']
        
        if q > 0:
            total = q + a + p
            if total > 0:
                normalized_data.append({
                    'type': 'QAP',
                    'Q': (q / total) * 100,
                    'A': (a / total) * 100,
                    'P': (p / total) * 100
                })
        elif f > 0:
            total = f + a + p
            if total > 0:
                normalized_data.append({
                    'type': 'APF',
                    'F': (f / total) * 100,
                    'A': (a / total) * 100,
                    'P': (p / total) * 100
                })
        else:
            # If both Q and F are 0, it lies on the A-P line.
            total = a + p
            if total > 0:
                 normalized_data.append({
                    'type': 'QAP',
                    'Q': 0,
                    'A': (a / total) * 100,
                    'P': (p / total) * 100
                })

    return pd.DataFrame(normalized_data)
