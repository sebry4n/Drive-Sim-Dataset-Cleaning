import os
import re
import shutil


def sort_csv_files():
    # Define paths relative to the script's location
    base_dir = os.path.dirname(os.path.abspath(__file__))
    source_dir = os.path.join(base_dir, "processed_results")
    output_base_dir = os.path.join(base_dir, "output")
    unsorted_dir = os.path.join(base_dir, "unsorted")

    # Check if the source directory exists
    if not os.path.exists(source_dir):
        print(f"Error: Source directory '{source_dir}' does not exist.")
        return

    # Regular expression to match: mam_sense_[Name]_Sesi_[Number]_HR.csv
    # Case-insensitive flag (re.IGNORECASE) is used to handle 'Sesi' or 'sesi'
    pattern = re.compile(r"^mam_sense_(.+?)_sesi_(\d+)_hr\.csv$", re.IGNORECASE)

    # Track processing statistics
    moved_count = 0
    unsorted_count = 0

    print("Starting file sorting process...\n")

    # Iterate through all files in the processed_results folder
    for filename in os.listdir(source_dir):
        source_file_path = os.path.join(source_dir, filename)

        # Skip directories, process files only
        if not os.path.isfile(source_file_path):
            continue

        match = pattern.match(filename)

        if match:
            # Extract name (XXX) and session (X) from the regex groups
            name = match.group(1)
            session = match.group(2)

            # Define the target folder name format: XXX_sesi_X_0
            # Matches the exact case of the extracted name
            target_folder_name = f"{name}_sesi_{session}_0"
            target_folder_path = os.path.join(output_base_dir, target_folder_name)

            # Ensure the specific target folder exists
            os.makedirs(target_folder_path, exist_ok=True)

            # Define the destination path with the new name 'mam_sense.csv'
            destination_file_path = os.path.join(target_folder_path, "mam_sense.csv")

            # Move and rename the file
            shutil.move(source_file_path, destination_file_path)
            print(f"Moved & Renamed: {filename} -> output/{target_folder_name}/mam_sense.csv")
            moved_count += 1
        else:
            # File doesn't match the format -> move to unsorted without renaming
            os.makedirs(unsorted_dir, exist_ok=True)
            destination_file_path = os.path.join(unsorted_dir, filename)

            shutil.move(source_file_path, destination_file_path)
            print(f"Unsorted file found: {filename} -> moved to unsorted/")
            unsorted_count += 1

    print("\n--- Process Completed ---")
    print(f"Successfully processed: {moved_count} file(s)")
    print(f"Sent to unsorted: {unsorted_count} file(s)")


if __name__ == "__main__":
    sort_csv_files()