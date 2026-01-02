"""
Data Transformation Script
Converts XES event logs to canonical CSV format
"""

import pandas as pd
import pm4py
from datetime import datetime
import os 
from pathlib import Path

from repoRoot import REPO_ROOT

# Target Schema Structure
CANONICAL_SCHEMA = {
    'case_id': 'string',
    'activity': 'string',
    'timestamp': 'datetime',
    'resource': 'string',
    'cost': 'float',
    'location': 'string',
    'product_type': 'string'
}


def standardise_xes_to_canonical(xes_path, output_csv_path, dataset_name):
    """
    Convert XES event log to canonical CSV format with dataset-specific mappings.
    Handles trace attributes for cost, product_type, and location with proper cleaning.
    """
    print(f"\n{'='*70}")
    print(f"🔄 Processing: {dataset_name}")
    print('='*70)
    print(f"   Source: {xes_path}")
    
    # Load XES file
    try:
        print(f"   📂 Loading XES file...")
        log = pm4py.read_xes(xes_path)
        print(f"   ✅ Loaded successfully")
    except FileNotFoundError:
        print(f"   ❌ Error: XES file not found. Skipping.")
        return None
        
    # Convert to DataFrame
    print(f"   🔄 Converting to DataFrame...")
    df = pm4py.convert_to_dataframe(log)
    print(f"   ✅ Converted {len(df):,} events")
    
    # Core column mappings
    column_mapping = {
        'case:concept:name': 'case_id',
        'concept:name': 'activity',
        'time:timestamp': 'timestamp',
        'org:resource': 'resource',
    }
    
    df_clean = df.rename(columns=column_mapping, errors='ignore')

    # Setup trace attribute source columns
    cost_source_col = None
    product_type_source_col = None
    location_source_col = 'lifecycle:transition'

    if '2017' in dataset_name:
        cost_source_col = 'case:RequestedAmount' 
        product_type_source_col = 'case:LoanGoal'
        print(f"   📊 Dataset: BPI 2017 (Loan Applications)")
        
    elif '2012' in dataset_name:
        cost_source_col = 'case:AMOUNT_REQ'
        print(f"   📊 Dataset: BPI 2012 (Loan Applications)")
        
    # Initialise canonical columns with defaults
    df_clean['cost'] = 0.0
    df_clean['location'] = ''
    df_clean['product_type'] = ''

    # Assign cost with robust conversion
    print(f"   🔧 Mapping attributes...")
    if cost_source_col and cost_source_col in df_clean.columns:
        cost_series = df_clean[cost_source_col].astype(str)
        
        df_clean['cost'] = pd.to_numeric(
            cost_series, 
            errors='coerce'
        ).fillna(0.0)
        
        df_clean = df_clean.drop(columns=[cost_source_col], errors='ignore')
        print(f"      ✓ Cost mapped")

    # Assign product type
    if product_type_source_col and product_type_source_col in df_clean.columns:
        df_clean['product_type'] = df_clean[product_type_source_col].astype(str).fillna('')
        df_clean = df_clean.drop(columns=[product_type_source_col], errors='ignore')
        print(f"      ✓ Product type mapped")
        
    # Assign location
    if location_source_col and location_source_col in df_clean.columns:
        df_clean['location'] = df_clean[location_source_col].astype(str).fillna('')
        df_clean = df_clean.drop(columns=[location_source_col], errors='ignore')
        print(f"      ✓ Location mapped")
        
    # Ensure required columns exist
    required_cols = ['case_id', 'activity', 'timestamp']
    for col in required_cols:
        if col not in df_clean.columns:
             raise ValueError(f"Missing required column for {dataset_name}: {col}")
    
    # Standardise timestamp format
    print(f"   🕐 Standardising timestamps...")
    df_clean['timestamp'] = pd.to_datetime(df_clean['timestamp'], utc=True)
    df_clean['timestamp'] = df_clean['timestamp'].dt.strftime('%Y-%m-%dT%H:%M:%S.%f')
    print(f"   ✅ Timestamps standardised")
    
    # Resource default
    if 'resource' not in df_clean.columns:
        df_clean['resource'] = 'Unknown'
    
    # Final column selection and ordering
    canonical_cols = list(CANONICAL_SCHEMA.keys())
    df_clean = df_clean.reindex(columns=canonical_cols)
    
    # Calculate statistics
    unique_cases = df_clean['case_id'].nunique()
    unique_activities = df_clean['activity'].nunique()
    date_range = (
        pd.to_datetime(df_clean['timestamp']).min().date(),
        pd.to_datetime(df_clean['timestamp']).max().date()
    )

    # Save cleaned dataset
    os.makedirs(os.path.dirname(output_csv_path), exist_ok=True) 
    df_clean.to_csv(output_csv_path, index=False)
    
    print(f"\n   📈 Dataset Statistics:")
    print(f"      • Total Events: {len(df_clean):,}")
    print(f"      • Unique Cases: {unique_cases:,}")
    print(f"      • Unique Activities: {unique_activities}")
    print(f"      • Date Range: {date_range[0]} to {date_range[1]}")
    print(f"\n   💾 Saved to: {output_csv_path}")
    print(f"   ✅ Transformation Complete\n")
    
    return df_clean


def main():
    """Main transformation workflow"""
    print("\n" + "="*70)
    print("🚀 DATA TRANSFORMATION - XES to Canonical CSV")
    print("="*70)
    
    RAW_DIR = REPO_ROOT / 'data' / 'raw'
    CLEAN_DIR = REPO_ROOT / 'data' / 'clean'

    datasets = [
        ('BPI_Challenge_2012.xes.gz', 'BPI_2012_clean.csv', 'BPI_Challenge_2012'),
        ('BPI_Challenge_2017.xes.gz', 'BPI_2017_clean.csv', 'BPI_Challenge_2017'),
    ]

    successful = 0
    failed = 0

    for xes_file, csv_file, dataset_name in datasets:
        xes_path_obj = RAW_DIR / xes_file
        csv_path_obj = CLEAN_DIR / csv_file
        
        xes_path = str(xes_path_obj)
        csv_path = str(csv_path_obj)
        
        try:
            result = standardise_xes_to_canonical(xes_path, csv_path, dataset_name)
            if result is not None:
                successful += 1
            else:
                failed += 1
        except Exception as e:
            print(f"   ❌ Error processing {dataset_name}: {str(e)}\n")
            failed += 1
    
    print("="*70)
    print("📊 TRANSFORMATION SUMMARY")
    print("="*70)
    print(f"   ✅ Successful: {successful}/{len(datasets)}")
    print(f"   ❌ Failed: {failed}/{len(datasets)}")
    print("="*70)
    
    if successful == len(datasets):
        print("🎉 All datasets transformed successfully!")
    elif successful > 0:
        print("⚠️  Some datasets failed to transform")
    else:
        print("❌ All transformations failed")
    
    print("\nNext steps:")
    print("1. Review cleaned files in data/clean/")
    print("2. Run validation: python -m scripts.dataset_validation")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()