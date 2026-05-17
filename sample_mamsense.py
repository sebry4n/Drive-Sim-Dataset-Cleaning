import csv
from datetime import datetime, timedelta
import os


def modify_csv_timestamps(file_path):
    """Reads an existing mam_sense.csv, changes the first column header to 'log_time',

    and overwrites it with a strict 1 Hz (1 sample per second) sequence.
    """
    base_time_str = "2026-05-02 08:13:04"
    # Parse to a datetime object
    current_time = datetime.strptime(base_time_str, "%Y-%m-%d %H:%M:%S")

    rows = []

    with open(file_path, mode="r", newline="", encoding="utf-8") as infile:
        reader = csv.reader(infile)
        header = next(reader, None)

        if not header:
            return False  # Empty file

        # Force the first column header name to log_time
        header[0] = "log_time"
        rows.append(header)

        # Process the rows sequentially at a strict 1 Hz rate
        for row in reader:
            if not row:
                continue

            # Format the time cleanly without fractional seconds (YYYY-MM-DD HH:MM:SS)
            time_str = current_time.strftime("%Y-%m-%d %H:%M:%S")

            row[0] = time_str
            rows.append(row)

            # Increment by exactly 1 second for the next sample row
            current_time += timedelta(seconds=1)

    # Overwrite the original file in place
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

    print(
        "Scanning 'output' directory for existing mam_sense.csv files (1 Hz Update)...\n"
    )

    for folder_name in os.listdir(output_base_dir):
        folder_path = os.path.join(output_base_dir, folder_name)

        if os.path.isdir(folder_path):
            target_csv_path = os.path.join(folder_path, "mam_sense.csv")

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
    print(
        f"Successfully updated {updated_count} mam_sense.csv file(s) to 1 Hz."
    )


if __name__ == "__main__":
    update_existing_output_folders()