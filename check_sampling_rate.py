import os
import pandas as pd

def check_low_hz(output_root, threshold=1.0):
    """
    Identifies files with a sampling rate below the threshold.
    """
    target_files = [
        'mmwave_ss_heart.csv', 'mmwave_ss_breath.csv',
        'mmwave_ti_heart_rate.csv', 'mmwave_ti_breath_rate.csv'
    ]

    print(f"Checking for sessions with Hz < {threshold}...")
    print("-" * 50)
    
    found_any = False

    for root, dirs, files in os.walk(output_root):
        folder_name = os.path.basename(root)
        for filename in files:
            if filename in target_files:
                file_path = os.path.join(root, filename)
                
                try:
                    df = pd.read_csv(file_path)
                    if len(df) < 2:
                        continue
                    
                    # Calculate Hz
                    df['log_time'] = pd.to_datetime(df['log_time'])
                    time_diffs = df['log_time'].diff().dt.total_seconds().dropna()
                    time_diffs = time_diffs[time_diffs > 0]
                    
                    if not time_diffs.empty:
                        hz = 1 / time_diffs.mean()
                        
                        # Only print if it's below our 1.0Hz threshold
                        if hz < threshold:
                            print(f"LOW FREQUENCY | Folder: {folder_name} | File: {filename} -> {hz:.2f} Hz")
                            found_any = True

                except Exception:
                    # Silently skip files that can't be read
                    continue

    if not found_any:
        print("All clear! No files found below 1.0 Hz.")

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_folder = os.path.join(script_dir, "output")

    if os.path.exists(output_folder):
        check_low_hz(output_folder)
    else:
        print(f"Error: Folder '{output_folder}' not found.")