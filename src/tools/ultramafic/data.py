import pandas as pd
import yaml
import os
import numpy as np

import sys

def _get_resource_path(filename):
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, 'tools', 'ultramafic', filename)
    else:
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)

def load_column_mappings():
    yml_path = _get_resource_path('column_aliases.yml')
    with open(yml_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def extract_and_normalize(df):
    """
    Extracts Ol, Opx, Cpx columns and normalizes them so they sum to 100.
    Returns a dataframe with 'Ol', 'Opx', 'Cpx' columns.
    """
    mappings = load_column_mappings()
    
    # Identify which columns to use
    ol_col = None
    opx_col = None
    cpx_col = None
    
    for col in df.columns:
        col_lower = col.lower().strip()
        if not ol_col and col_lower in [name.lower() for name in mappings.get('Ol', [])]:
            ol_col = col
        if not opx_col and col_lower in [name.lower() for name in mappings.get('Opx', [])]:
            opx_col = col
        if not cpx_col and col_lower in [name.lower() for name in mappings.get('Cpx', [])]:
            cpx_col = col

    if not (ol_col and opx_col and cpx_col):
        raise ValueError(f"Could not find all required columns (Ol, Opx, Cpx). Found: Ol={ol_col}, Opx={opx_col}, Cpx={cpx_col}")
        
    extracted_df = df[[ol_col, opx_col, cpx_col]].copy()
    extracted_df.columns = ['Ol', 'Opx', 'Cpx']
    
    # Convert to numeric
    for col in ['Ol', 'Opx', 'Cpx']:
        extracted_df[col] = pd.to_numeric(extracted_df[col], errors='coerce').fillna(0)
    
    extracted_df['Total'] = extracted_df[['Ol', 'Opx', 'Cpx']].sum(axis=1)
    
    # Identify non-zero rows
    non_zero = extracted_df['Total'] > 0
    
    # Drop rows where sum is 0
    normalized_df = extracted_df[non_zero].copy()
    
    normalized_df['Ol'] = (normalized_df['Ol'] / normalized_df['Total']) * 100
    normalized_df['Opx'] = (normalized_df['Opx'] / normalized_df['Total']) * 100
    normalized_df['Cpx'] = (normalized_df['Cpx'] / normalized_df['Total']) * 100
    
    return normalized_df[['Ol', 'Opx', 'Cpx']]
