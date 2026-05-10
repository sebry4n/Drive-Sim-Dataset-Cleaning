import os
import pandas as pd

def remove_publish_time(output_root):
    """
    Removes the 'publish_time' column from all mmwave_ti_*.csv files.
    """
    processed_count = 0

    for root, dirs, files in os.walk(output_root):
        # Target only files starting with mmwave_ti_
        target_files = [f for f in files if f.startswith('mmwave_ti_') and f.endswith('.csv')]
        
        for filename in target_files:
            file_path = os.path.join(root, filename)
            
            try:
                # Load the file
                df = pd.read_csv(file_path)
                
                if 'publish_time' in df.columns:
                    # Drop the column
                    df.drop(columns=['publish_time'], inplace=True)
                    
                    # Save back (Overwriting)
                    df.to_csv(file_path, index=False)
                    processed_count += 1
                
            except Exception as e:
                print(f"Error processing {filename} in {os.path.basename(root)}: {e}")

    print(f"\nClean-up complete! Removed 'publish_time' from {processed_count} files.")

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Assuming your data is in the 'output' folder
    output_folder = os.path.join(script_dir, "output")

    if os.path.exists(output_folder):
        print("Cleaning TI files: Removing 'publish_time'...")
        remove_publish_time(output_folder)
    else:
        print(f"Error: Folder '{output_folder}' not found.")