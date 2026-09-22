import pandas as pd
from utils.i18n import tr

MAJOR_OXIDES = {
    'sio2', 'tio2', 'al2o3', 'fe2o3', 'feo', 'fe2o3t', 'feot', 
    'mno', 'mgo', 'cao', 'na2o', 'k2o', 'p2o5', 'cr2o3', 'nio', 'so3'
}

def load_and_validate_data(file_path):
    """Loads and validates TAS data from Excel or CSV."""
    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path, header=None)
        elif file_path.endswith('.xlsx') or file_path.endswith('.xls'):
            df = pd.read_excel(file_path, header=None)
        else:
            return None, tr("err_unsupported_file")
    except Exception:
        return None, tr("err_file_corrupt")
    
    # Find the header row by searching for 'SiO2' (case-insensitive)
    header_idx = -1
    for idx, row in df.iterrows():
        if any('sio2' in str(val).strip().lower() for val in row):
            header_idx = idx
            break
            
    if header_idx == -1:
        return None, tr("err_missing_sio2")
        
    # Assign columns
    raw_cols = [str(c).strip().lower() for c in df.iloc[header_idx]]
    cleaned_cols = []
    for c in raw_cols:
        # Extract base oxide name if formatted like 'sio2 (wt%)'
        base = c.split()[0].split('(')[0].split('[')[0].strip()
        cleaned_cols.append(base if base in MAJOR_OXIDES or base in ['loi', 'total', 'sum', 'sample'] else c)
    df.columns = cleaned_cols
    
    # Drop the header row and any rows before it
    df = df.iloc[header_idx + 1:].reset_index(drop=True)
    
    # Check if the next row is a unit row (e.g., 'g/100g', 'wt%')
    if len(df) > 0:
        try:
            float(df['sio2'].iloc[0])
        except (ValueError, TypeError):
            # First row is likely units, drop it
            df = df.iloc[1:].reset_index(drop=True)
            
    # Check for required columns
    required = ['sio2', 'na2o', 'k2o']
    for req in required:
        if req not in df.columns:
            return None, tr("err_tas_required_missing", req=req)
            
    return df, None

def normalize_tas(df):
    """
    For each row, normalizes major element oxides to 100% (excluding LOI, total sums, and trace elements),
    and returns a DataFrame with SiO2 and Total_Alkali (Na2O + K2O).
    """
    normalized_data = []
    
    for _, row in df.iterrows():
        row_vals = {}
        for col, val in row.items():
            col_clean = str(col).strip().lower().split()[0].split('(')[0].split('[')[0]
            # Only consider known major oxide columns for major element normalization
            if col_clean not in MAJOR_OXIDES:
                continue
            try:
                num_val = float(val)
                if pd.isna(num_val):
                    num_val = 0.0
                row_vals[col_clean] = num_val
            except (ValueError, TypeError):
                pass
                
        # Sum of all valid major numeric oxide values
        total = sum(row_vals.values())
        
        if total == 0:
            continue
            
        sio2 = row_vals.get('sio2', 0) / total * 100
        na2o = row_vals.get('na2o', 0) / total * 100
        k2o = row_vals.get('k2o', 0) / total * 100
        
        if sio2 == 0 and (na2o + k2o) == 0:
            continue
            
        normalized_data.append({
            'SiO2': sio2,
            'Total_Alkali': na2o + k2o
        })
        
    return pd.DataFrame(normalized_data)
