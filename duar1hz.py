import os
import pandas as pd

def resample_dataset_to_1hz(output_root):
    """
    Standardizes heart and breath rate CSVs to 1Hz.
    Fixes the 'str' dtype error by forcing numeric conversion.
    """
    target_files = [
        'mmwave_ss_heart.csv', 'mmwave_ss_breath.csv',
        'mmwave_ti_heart_rate.csv', 'mmwave_ti_breath_rate.csv'
    ]

    processed_count = 0

    for root, dirs, files in os.walk(output_root):
        folder_name = os.path.basename(root)
        for filename in files:
            if filename in target_files:
                file_path = os.path.join(root, filename)
                
                try:
                    df = pd.read_csv(file_path)
                    if df.empty or 'log_time' not in df.columns:
                        continue
                    
                    # 1. Convert time and set as index
                    df['log_time'] = pd.to_datetime(df['log_time'])
                    df.set_index('log_time', inplace=True)
                    
                    # 2. Identify the value column
                    val_cols = [c for c in df.columns if 'rate' in c.lower()]
                    if not val_cols:
                        val_cols = [df.columns[0]] if len(df.columns) > 0 else []
                    
                    if not val_cols:
                        continue
                        
                    target_col = val_cols[0]
                    
                    # --- NEW STEP: Force Numeric ---
                    # errors='coerce' turns non-numeric text into NaN
                    df[target_col] = pd.to_numeric(df[target_col], errors='coerce')
                    
                    # 3. Resample to 1 second
                    # Using lowercase 's' for compatibility
                    resampled_df = df[[target_col]].resample('1s').mean()
                    
                    # 4. Fill very small gaps (1-2 seconds)
                    resampled_df[target_col] = resampled_df[target_col].interpolate(method='linear', limit=2)
                    
                    # 5. Save back
                    resampled_df.reset_index(inplace=True)
                    resampled_df.to_csv(file_path, index=False)
                    
                    processed_count += 1
                    if processed_count % 50 == 0:
                        print(f"Progress: {processed_count} files standardized...")

                except Exception as e:
                    print(f"Error processing {folder_name}/{filename}: {e}")

    print(f"\nFinished! {processed_count} files are now standardized to 1 Hz.")

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_folder = os.path.join(script_dir, "output")

    if os.path.exists(output_folder):
        print("Starting 1 Hz Resampling with Numeric Correction...")
        resample_dataset_to_1hz(output_folder)
    else:
        print(f"Error: Folder '{output_folder}' not found.")