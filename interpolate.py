import os
import pandas as pd
import numpy as np

def interpolate_nan_segments(output_root, gap_limit=10):
    """
    Finds NaN values and fills them using linear interpolation.
    gap_limit: Maximum number of consecutive NaNs to fill.
    """
    target_files = [
        'mmwave_ss_heart.csv', 'mmwave_ss_breath.csv',
        'mmwave_ti_heart_rate.csv', 'mmwave_ti_breath_rate.csv'
    ]

    for root, dirs, files in os.walk(output_root):
        for filename in files:
            if filename in target_files:
                file_path = os.path.join(root, filename)
                
                try:
                    df = pd.read_csv(file_path)
                    
                    if df.empty:
                        continue

                    # Find the column that contains the data (heart_rate or breath_rate)
                    # We skip 'log_time'
                    data_cols = [c for c in df.columns if 'rate' in c.lower()]
                    
                    if not data_cols:
                        continue
                    
                    target_col = data_cols[0]

                    # Perform Linear Interpolation
                    # limit_direction='both' ensures it can fill towards the start/end
                    df[target_col] = df[target_col].interpolate(
                        method='linear', 
                        limit=gap_limit, 
                        limit_direction='both'
                    )

                    # Save the file back (Overwriting)
                    df.to_csv(file_path, index=False)
                    print(f"Interpolated: {file_path}")

                except Exception as e:
                    print(f"Error processing {file_path}: {e}")

if __name__ == "__main__":
    # Point this to your 'output' folder
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_folder = os.path.join(script_dir, "output")

    if os.path.exists(output_folder):
        print(f"Starting interpolation (Limit: {10} consecutive rows)...")
        interpolate_nan_segments(output_folder, gap_limit=10)
        print("\nInterpolation complete.")
    else:
        print(f"Error: Folder '{output_folder}' not found.")