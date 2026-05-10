import os
import shutil

def copy_other_csv_files(input_root, output_root):
    """
    Copies all CSV files from input_root to output_root, 
    preserving folder structure, except for 'mmwave_ss.csv'.
    """
    for root, dirs, files in os.walk(input_root):
        # Filter for CSV files but exclude the one you've already processed
        csv_files = [f for f in files if f.lower().endswith('.csv') and f != "mmwave_ss.csv" and f != "mam_sense.csv" and f!= "mmwave_ti_phase_data.csv" and f!= "mmwave_ti_points.csv"]
        
        if csv_files:
            # Create the matching subfolder in the output directory
            rel_path = os.path.relpath(root, input_root)
            current_output_dir = os.path.join(output_root, rel_path)
            os.makedirs(current_output_dir, exist_ok=True)
            
            for file in csv_files:
                source_path = os.path.join(root, file)
                destination_path = os.path.join(current_output_dir, file)
                
                # Copy the file (shutil.copy2 preserves metadata)
                shutil.copy2(source_path, destination_path)
                print(f"Copied: {file} to {rel_path}")

if __name__ == "__main__":
    # Define your paths
    input_dir = r"D:\output"
    # This identifies the directory where this python script is saved
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "output")

    print("Starting file copy process...")
    copy_other_csv_files(input_dir, output_dir)
    print("\nCopy process complete.")