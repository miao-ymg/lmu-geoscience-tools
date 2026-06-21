import pandas as pd

def load_and_validate_data(file_path):
    """Loads and validates TAS data from Excel or CSV."""
    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path, header=None)
        elif file_path.endswith('.xlsx') or file_path.endswith('.xls'):
            df = pd.read_excel(file_path, header=None)
        else:
            return None, "The file could not be opened. Please make sure it is an Excel or CSV file."
    except Exception:
        return None, "The file could not be opened. Please check if it's corrupted or currently open in another program."
    
    # Find the header row by searching for 'SiO2' (case-insensitive)
    header_idx = -1
    for idx, row in df.iterrows():
        if any('sio2' == str(val).strip().lower() for val in row):
            header_idx = idx
            break
            
    if header_idx == -1:
        return None, "Could not find a 'SiO2' column in the file. Is it missing?"
        
    # Assign columns
    df.columns = [str(c).strip().lower() for c in df.iloc[header_idx]]
    
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
            return None, f"Required column '{req}' is missing. Please ensure your file has SiO2, Na2O, and K2O."
            
    return df, None

def normalize_tas(df):
    """
    For each row, drops LOI, normalizes all remaining values to 100%, 
    and returns a DataFrame with SiO2 and Total_Alkali.
    """
    normalized_data = []
    
    for _, row in df.iterrows():
        row_vals = {}
        for col, val in row.items():
            if col == 'loi' or 'unnamed' in col: 
                continue
            try:
                num_val = float(val)
                # Ensure we only keep positive valid numbers
                if pd.isna(num_val):
                    num_val = 0.0
                row_vals[col] = num_val
            except (ValueError, TypeError):
                # Non-numeric columns (like Sample ID) are ignored
                pass
                
        # Sum of all valid numeric values except LOI
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
