import csv
from datetime import datetime, timedelta
import os


def modify_csv_timestamps(file_path):
    """Reads an existing mam_sense.csv, changes 'Time_Seconds' to 'log_time',

    and aligns the decimal offsets to the 2026-05-02 08:13:04 base time.
    """
    base_time_str = "2026-05-02 08:13:04"
    base_datetime = datetime.strptime(base_time_str, "%Y-%m-%d %H:%M:%S")

    rows = []

    with open(file_path, mode="r", newline="", encoding="utf-8") as infile:
        reader = csv.reader(infile)
        header = next(reader, None)

        if not header:
            return False  # Empty file

        # Change header name from Time_Seconds to log_time
        header[0] = "log_time"
        rows.append(header)

        first_row = True
        first_time_val = 0.0

        for row in reader:
            if not row or not row[0].strip():
                continue

            try:
                current_float_time = float(row[0])

                if first_row:
                    first_time_val = current_float_time
                    target_datetime = base_datetime
                    first_row = False
                else:
                    elapsed_seconds = current_float_time - first_time_val
                    target_datetime = base_datetime + timedelta(
                        seconds=elapsed_seconds
                    )

                # Format timestamp with milliseconds precision
                time_str = target_datetime.strftime("%Y-%m-%d %H:%M:%S.%f")[
                    :-3
                ]
                row[0] = time_str
                rows.append(row)

            except ValueError:
                # Skips any faulty rows that can't be parsed as a float
                continue

    # Overwrite the file with the modifications
    with open(file_path, mode="w", newline="", encoding="utf-8") as outfile:
        writer = csv.writer(outfile)
        writer.writerows(rows)

    return True


def update_existing_output_folders():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_base_dir = os.path.join(base_dir, "output")

    if not os.path.exists(output_base_dir):
        print(f"Error: 'output' directory not found at {output_base_dir}")
        return

    updated_count = 0

    print("Scanning 'output' directory for existing mam_sense.csv files...\n")

    # Iterate through every subfolder inside the output folder
    for folder_name in os.listdir(output_base_dir):
        folder_path = os.path.join(output_base_dir, folder_name)

        # Check if it's actually a directory (e.g., Akhul_sesi_1_0)
        if os.path.isdir(folder_path):
            target_csv_path = os.path.join(folder_path, "mam_sense.csv")

            # Check if mam_sense.csv exists inside this dataset folder
            if os.path.exists(target_csv_path):
                try:
                    success = modify_csv_timestamps(target_csv_path)
                    if success:
                        print(f"Updated: output/{folder_name}/mam_sense.csv")
                        updated_count += 1
                except Exception as e:
                    print(
                        f"Failed to update output/{folder_name}/mam_sense.csv. Error: {e}"
                    )

    print("\n--- Update Process Completed ---")
    print(f"Successfully updated {updated_count} mam_sense.csv file(s).")


if __name__ == "__main__":
    update_existing_output_folders()