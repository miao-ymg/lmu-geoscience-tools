import pandas as pd

def load_and_validate_data(file_path):
    """
    Reads a text file containing Raman spectra data.
    Looks for lines that contain exactly two float numbers (Raman Shift and Intensity).
    Returns (DataFrame, error_msg)
    """
    try:
        x_vals = []
        y_vals = []
        
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                # Strip whitespace and split by tabs or spaces
                parts = line.strip().split()
                if len(parts) == 2:
                    try:
                        # Replace comma with dot to handle European number format
                        x = float(parts[0].replace(',', '.'))
                        y = float(parts[1].replace(',', '.'))
                        x_vals.append(x)
                        y_vals.append(y)
                    except ValueError:
                        # Not a valid data line (e.g. headers), skip
                        pass
                        
        if not x_vals:
            from utils.i18n import tr
            return None, tr("err_raman_no_data")
            
        df = pd.DataFrame({
            'Raman Shift': x_vals,
            'Intensity': y_vals
        })
        return df, None
    except Exception as e:
        from utils.i18n import tr
        return None, tr("err_raman_read_failed", error=str(e))
