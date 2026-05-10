import os
import pandas as pd
import numpy as np

def check_dataset_health(output_root):
    target_files = [
        'mmwave_ss_heart.csv', 'mmwave_ss_breath.csv',
        'mmwave_ti_heart_rate.csv', 'mmwave_ti_breath_rate.csv'
    ]

    all_hz_values = []
    file_type_stats = {f: [] for f in target_files}

    print(f"{'File Type':<25} | {'Average Hz'}")
    print("-" * 40)

    for root, dirs, files in os.walk(output_root):
        for filename in files:
            if filename in target_files:
                file_path = os.path.join(root, filename)
                
                try:
                    df = pd.read_csv(file_path)
                    if len(df) < 2:
                        continue
                    
                    # Calculate Hz for this specific file
                    df['log_time'] = pd.to_datetime(df['log_time'])
                    # Use the total duration divided by number of samples for a stable average
                    total_seconds = (df['log_time'].max() - df['log_time'].min()).total_seconds()
                    
                    if total_seconds > 0:
                        hz = (len(df) - 1) / total_seconds
                        all_hz_values.append(hz)
                        file_type_stats[filename].append(hz)
                except Exception:
                    continue

    # Print summary per file type
    for filename, stats in file_type_stats.items():
        if stats:
            avg_type_hz = np.mean(stats)
            print(f"{filename:<25} | {avg_type_hz:.2f} Hz")

    print("-" * 40)
    if all_hz_values:
        grand_avg = np.mean(all_hz_values)
        print(f"{'GRAND DATASET AVERAGE':<25} | {grand_avg:.2f} Hz")
        print(f"{'TOTAL FILES ANALYZED':<25} | {len(all_hz_values)}")
    else:
        print("No valid files found to calculate average Hz.")

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_folder = os.path.join(script_dir, "output")

    if os.path.exists(output_folder):
        check_dataset_health(output_folder)
    else:
        print(f"Error: Folder '{output_folder}' not found.")