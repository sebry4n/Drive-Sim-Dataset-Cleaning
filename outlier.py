import os
import pandas as pd
import numpy as np

def remove_outliers_and_flatlines(df, column_name, min_val, max_val, window=10, sigma=3, max_flatline=5):
    """
    1. Removes hard outliers.
    2. Removes statistical spikes.
    3. Removes flatlines (stuck values).
    """
    # Safety check: if column doesn't exist, return
    if column_name not in df.columns:
        return df

    # --- 1. Hard Thresholding ---
    # We clip slightly below 140 if your 'stuck' value is exactly 140
    df.loc[(df[column_name] < min_val) | (df[column_name] >= max_val), column_name] = np.nan
    
    # --- 2. Flatline Detection ---
    # Detects if the sensor is "stuck" on the same value for 'max_flatline' consecutive samples
    # This is common in the TI AWR1642 when it loses tracking
    df['diff'] = df[column_name].diff().fillna(0)
    # Boolean mask: is the difference zero?
    df['is_flat'] = (df['diff'] == 0) & (df[column_name].notna())
    
    # Identify groups of identical values
    df['flat_group'] = (df['is_flat'] != df['is_flat'].shift()).cumsum()
    flat_counts = df.groupby('flat_group')['is_flat'].transform('sum')
    
    # If the value is the same for more than 5 samples, mark as NaN
    df.loc[flat_counts >= max_flatline, column_name] = np.nan
    
    # Drop helper columns
    df = df.drop(columns=['diff', 'is_flat', 'flat_group'])

    # --- 3. Rolling Z-Score (Statistical spikes) ---
    rolling_mean = df[column_name].rolling(window=window, center=True).mean()
    rolling_std = df[column_name].rolling(window=window, center=True).std()
    
    outlier_condition = (df[column_name] < (rolling_mean - sigma * rolling_std)) | \
                        (df[column_name] > (rolling_mean + sigma * rolling_std))
    
    df.loc[outlier_condition, column_name] = np.nan
    return df

def process_cleaning(output_root):
    # Thresholds: Note we set Heart Rate max to 139 to auto-kill the "140" stuck values
    limits = {
        'heart': {'min': 40, 'max': 139, 'col': 'heart_rate'}, 
        'breath': {'min': 8, 'max': 35, 'col': 'breath_rate'}
    }

    target_files = {
        'mmwave_ss_heart.csv': limits['heart'],
        'mmwave_ss_breath.csv': limits['breath'],
        'mmwave_ti_heart_rate.csv': limits['heart'],
        'mmwave_ti_breath_rate.csv': limits['breath']
    }

    for root, dirs, files in os.walk(output_root):
        for filename, config in target_files.items():
            if filename in files:
                file_path = os.path.join(root, filename)
                try:
                    df = pd.read_csv(file_path)
                    
                    # Handle TI naming variations if necessary
                    actual_col = config['col']
                    if actual_col not in df.columns:
                        # Try finding a column that contains 'heart' or 'breath'
                        potential_cols = [c for c in df.columns if config['col'].split('_')[0] in c.lower()]
                        if potential_cols:
                            actual_col = potential_cols[0]

                    df = remove_outliers_and_flatlines(df, actual_col, config['min'], config['max'])
                    
                    df.to_csv(file_path, index=False)
                    print(f"Cleaned (Stuck values removed): {file_path}")
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_folder = os.path.join(script_dir, "output")

    if os.path.exists(output_folder):
        process_cleaning(output_folder)
        print("\nCleaned data. Note: Long gaps (Data Loss) are now represented as NaNs.")