import csv
import math
import os


def load_heart_rate_data(file_path):
    """Reads a CSV file and returns a dictionary of {log_time: heart_rate_value}."""
    hr_dict = {}
    if not os.path.exists(file_path):
        return None

    with open(file_path, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)

        if not header:
            return hr_dict

        try:
            time_idx = header.index("log_time")
            hr_idx = -1
            for i, h in enumerate(header):
                cleaned = h.lower().replace("_", " ")
                if "heart" in cleaned or "hr" in cleaned or "rate" in cleaned:
                    hr_idx = i
                    break

            if hr_idx == -1:
                hr_idx = 1
        except ValueError:
            time_idx, hr_idx = 0, 1

        for row in reader:
            if not row or len(row) <= max(time_idx, hr_idx):
                continue
            time_str = row[time_idx].strip()
            hr_str = row[hr_idx].strip()

            try:
                hr_dict[time_str] = float(hr_str)
            except ValueError:
                continue

    return hr_dict


def calculate_metrics(ground_truth, predictions):
    """Calculates MAE, RMSE, and Percentage Accuracy based on MAPE."""
    absolute_errors = []
    squared_errors = []
    percentage_errors = []

    for time_key, gt_val in ground_truth.items():
        if time_key in predictions:
            pred_val = predictions[time_key]

            # Avoid division by zero if heart rate is unexpectedly 0
            if gt_val == 0:
                continue

            error = pred_val - gt_val
            absolute_errors.append(abs(error))
            squared_errors.append(error**2)

            # Absolute percentage error relative to ground truth
            percentage_errors.append(abs(error) / gt_val)

    n_samples = len(absolute_errors)
    if n_samples == 0:
        return None, None, None, 0

    mae = sum(absolute_errors) / n_samples
    rmse = math.sqrt(sum(squared_errors) / n_samples)

    # Calculate percentage accuracy: max handles clipping outliers below 0%
    mape = sum(percentage_errors) / n_samples
    accuracy_pct = max(0.0, (1.0 - mape) * 100.0)

    return mae, rmse, accuracy_pct, n_samples


def run_analytical_evaluation():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_base_dir = os.path.join(base_dir, "output")

    if not os.path.exists(output_base_dir):
        print(f"Error: 'output' directory not found at {output_base_dir}")
        return

    # Global aggregation containers
    global_ti_errors = []
    global_ti_squared = []
    global_ti_pct_errs = []

    global_ss_errors = []
    global_ss_squared = []
    global_ss_pct_errs = []

    print("=" * 85)
    print(" PARTICIPANT ACCURACY ANALYSIS (Ground Truth: mamsense)")
    print("=" * 85)

    for folder_name in sorted(os.listdir(output_base_dir)):
        folder_path = os.path.join(output_base_dir, folder_name)

        if not os.path.isdir(folder_path):
            continue

        mam_file = os.path.join(folder_path, "mam_sense.csv")
        ti_file = os.path.join(folder_path, "mmwave_ti_heart_rate.csv")
        ss_file = os.path.join(folder_path, "mmwave_ss_heart.csv")

        mam_data = load_heart_rate_data(mam_file)

        if not mam_data:
            continue

        print(f"\n[ Participant: {folder_name} ]")

        # 1. Evaluate mmWave TI
        ti_data = load_heart_rate_data(ti_file)
        if ti_data is not None:
            mae_ti, rmse_ti, acc_ti, samples_ti = calculate_metrics(
                mam_data, ti_data
            )
            if samples_ti > 0:
                print(
                    f"  -> mmWave TI:   Accuracy = {acc_ti:6.2f}% | MAE = {mae_ti:5.2f} BPM | RMSE = {rmse_ti:5.2f} BPM ({samples_ti} samples)"
                )
                for tk, gt in mam_data.items():
                    if tk in ti_data and gt != 0:
                        err = ti_data[tk] - gt
                        global_ti_errors.append(abs(err))
                        global_ti_squared.append(err**2)
                        global_ti_pct_errs.append(abs(err) / gt)
            else:
                print("  -> mmWave TI:   No overlapping timestamp frames found.")
        else:
            print("  -> mmWave TI:   File missing.")

        # 2. Evaluate mmWave SS
        ss_data = load_heart_rate_data(ss_file)
        if ss_data is not None:
            mae_ss, rmse_ss, acc_ss, samples_ss = calculate_metrics(
                mam_data, ss_data
            )
            if samples_ss > 0:
                print(
                    f"  -> mmWave SS:   Accuracy = {acc_ss:6.2f}% | MAE = {mae_ss:5.2f} BPM | RMSE = {rmse_ss:5.2f} BPM ({samples_ss} samples)"
                )
                for tk, gt in mam_data.items():
                    if tk in ss_data and gt != 0:
                        err = ss_data[tk] - gt
                        global_ss_errors.append(abs(err))
                        global_ss_squared.append(err**2)
                        global_ss_pct_errs.append(abs(err) / gt)
            else:
                print("  -> mmWave SS:   No overlapping timestamp frames found.")
        else:
            print("  -> mmWave SS:   File missing.")

    # --- OVERALL AGGREGATED REPORT ---
    print("\n" + "=" * 85)
    print(" OVERALL SYSTEM METRICS SUMMARY")
    print("=" * 85)

    # Global TI Metrics
    if global_ti_errors:
        g_mae_ti = sum(global_ti_errors) / len(global_ti_errors)
        g_rmse_ti = math.sqrt(sum(global_ti_squared) / len(global_ti_squared))
        g_acc_ti = max(0.0, (1.0 - (sum(global_ti_pct_errs) / len(global_ti_pct_errs))) * 100.0)

        print(f"Overall mmWave TI Performance:")
        print(f"  Total Data Points paired: {len(global_ti_errors)}")
        print(f"  Mean Absolute Percentage Accuracy: {g_acc_ti:.2f}%")
        print(f"  Mean Absolute Error (MAE):          {g_mae_ti:.3f} BPM")
        print(f"  Root Mean Sq. Error (RMSE):         {g_rmse_ti:.3f} BPM")
    else:
        print("Overall mmWave TI Performance: No valid paired data collected.")

    print("-" * 85)

    # Global SS Metrics
    if global_ss_errors:
        g_mae_ss = sum(global_ss_errors) / len(global_ss_errors)
        g_rmse_ss = math.sqrt(sum(global_ss_squared) / len(global_ss_squared))
        g_acc_ss = max(0.0, (1.0 - (sum(global_ss_pct_errs) / len(global_ss_pct_errs))) * 100.0)

        print(f"Overall mmWave SS Performance:")
        print(f"  Total Data Points paired: {len(global_ss_errors)}")
        print(f"  Mean Absolute Percentage Accuracy: {g_acc_ss:.2f}%")
        print(f"  Mean Absolute Error (MAE):          {g_mae_ss:.3f} BPM")
        print(f"  Root Mean Sq. Error (RMSE):         {g_rmse_ss:.3f} BPM")
    else:
        print("Overall mmWave SS Performance: No valid paired data collected.")
    print("=" * 85 + "\n")


if __name__ == "__main__":
    run_analytical_evaluation()