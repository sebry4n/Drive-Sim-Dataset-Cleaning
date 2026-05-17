import csv
import os


def extract_target_timestamps(folder_path):
    """Scans the mmwave files in the participant folder to extract the precise

    ordered list of log_time strings to use as the timing anchor.
    """
    # Check TI file first, fallback to SS file
    ti_path = os.path.join(folder_path, "mmwave_ti_heart_rate.csv")
    ss_path = os.path.join(folder_path, "mmwave_ss_heart.csv")

    target_path = None
    if os.path.exists(ti_path):
        target_path = ti_path
    elif os.path.exists(ss_path):
        target_path = ss_path
    else:
        return None

    timestamps = []
    with open(target_path, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)

        if not header:
            return None

        # Find log_time index
        try:
            time_idx = header.index("log_time")
        except ValueError:
            time_idx = 0  # Fallback to first column

        for row in reader:
            if row and len(row) > time_idx:
                timestamps.append(row[time_idx].strip())

    return timestamps


def sync_mam_sense_timestamps(mam_path, target_timestamps):
    """Overwrites the first column of mam_sense.csv with the exact timestamps

    extracted from the mmwave files.
    """
    rows = []

    with open(mam_path, mode="r", newline="", encoding="utf-8") as infile:
        reader = csv.reader(infile)
        header = next(reader, None)

        if not header:
            return False

        # Set standard header
        header[0] = "log_time"
        rows.append(header)

        # Match row by row to the reference timestamps
        for i, row in enumerate(reader):
            if not row:
                continue

            # If mam_sense has more rows than mmwave data, stop or pad
            if i < len(target_timestamps):
                row[0] = target_timestamps[i]
            else:
                # If it exceeds the reference frame bounds, skip it to keep data shapes paired
                continue
            rows.append(row)

    # Overwrite the file back down safely
    with open(mam_path, mode="w", newline="", encoding="utf-8") as outfile:
        writer = csv.writer(outfile)
        writer.writerows(rows)

    return True


def run_time_synchronization():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_base_dir = os.path.join(base_dir, "output")

    if not os.path.exists(output_base_dir):
        print(f"Error: 'output' directory not found at {output_base_dir}")
        return

    success_count = 0

    print("Synchronizing mam_sense timelines to match mmWave logs...\n")

    for folder_name in sorted(os.listdir(output_base_dir)):
        folder_path = os.path.join(output_base_dir, folder_name)

        if not os.path.isdir(folder_path):
            continue

        mam_file_path = os.path.join(folder_path, "mam_sense.csv")

        if os.path.exists(mam_file_path):
            # 1. Grab the precise timeline from the reference mmWave tracking array
            ref_timestamps = extract_target_timestamps(folder_path)

            if not ref_timestamps:
                print(
                    f"Skipped: {folder_name} (No valid mmWave reference logs found to clone timestamps from)"
                )
                continue

            # 2. Re-anchor the mam_sense logs to that timing grid
            try:
                if sync_mam_sense_timestamps(mam_file_path, ref_timestamps):
                    print(
                        f"Synchronized: output/{folder_name}/mam_sense.csv -> Linked to mmWave timeline"
                    )
                    success_count += 1
            except Exception as e:
                print(f"Error syncing timelines for {folder_name}: {e}")

    print("\n--- Sync completed ---")
    print(f"Successfully re-aligned {success_count} participant files.")


if __name__ == "__main__":
    run_time_synchronization()