import os
import csv
import re

def process_mmwave_data(input_root, output_root):
    # Regex to find numbers after x= and y=
    # This handles integers and floats (e.g., 73.0 or 28)
    heart_rate_pattern = re.compile(r"x=([\d\.]+)")
    breath_rate_pattern = re.compile(r"y=([\d\.]+)")

    for root, dirs, files in os.walk(input_root):
        if "mmwave_ss.csv" in files:
            # 1. Setup paths
            input_file_path = os.path.join(root, "mmwave_ss.csv")
            
            # Create the relative path to maintain folder structure
            rel_path = os.path.relpath(root, input_root)
            current_output_dir = os.path.join(output_root, rel_path)
            
            os.makedirs(current_output_dir, exist_ok=True)
            
            heart_output_path = os.path.join(current_output_dir, "mmwave_ss_heart.csv")
            breath_output_path = os.path.join(current_output_dir, "mmwave_ss_breath.csv")

            heart_data = []
            breath_data = []

            # 2. Read and Parse
            with open(input_file_path, mode='r', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    point_str = row['point']
                    log_time = row['log_time']
                    
                    hr_match = heart_rate_pattern.search(point_str)
                    br_match = breath_rate_pattern.search(point_str)

                    if hr_match:
                        heart_data.append([log_time, hr_match.group(1)])
                    if br_match:
                        breath_data.append([log_time, br_match.group(1)])

            # 3. Write Heart Rate CSV
            with open(heart_output_path, mode='w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['log_time', 'heart_rate'])
                writer.writerows(heart_data)

            # 4. Write Breath Rate CSV
            with open(breath_output_path, mode='w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['log_time', 'breath_rate'])
                writer.writerows(breath_data)

            print(f"Processed: {input_file_path}")

if __name__ == "__main__":
    # Settings
    input_dir = r"D:\output"
    # This puts the 'output' folder in the same directory as this script
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")

    process_mmwave_data(input_dir, output_dir)
    print("\nExtraction complete.")