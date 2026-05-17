import os
import re
import shutil
import pandas as pd


def extract_kss_value(kantuk_string):
    """Extracts the first digit integer from the sleepiness scale string."""
    if pd.isna(kantuk_string):
        return ""
    match = re.search(r"\d+", str(kantuk_string))
    return match.group(0) if match else ""


def build_kss_mapping(csv_path):
    """Parses Form.csv to generate a robust mapping between name/session and the target KSS code."""
    df = pd.read_csv(csv_path)

    # Clean whitespaces from columns and headers
    df.columns = [col.strip() for col in df.columns]
    df["Nama Lengkap"] = df["Nama Lengkap"].str.strip().str.lower()
    df["Sesi"] = df["Sesi"].str.strip()

    # Generate codes identical to your generation rules
    def compute_participant_code(row):
        status = str(row["Status Partisipan"]).lower()
        if "umum" in status:
            return "22U"
        nrp_str = str(row["NRP"]).split(".")[0].strip()
        nrp_suffix = nrp_str[-3:] if len(nrp_str) >= 3 else "000"
        angkatan_str = str(row["Angkatan"]).split(".")[0].strip()
        angkatan_prefix = angkatan_str[-2:] if len(angkatan_str) >= 2 else "23"
        return f"{angkatan_prefix}{nrp_suffix}"

    df["p_code"] = df.apply(compute_participant_code, axis=1)
    df["s_idx"] = df["Sesi"].apply(lambda x: re.search(r"\d+", str(x)).group(0) if re.search(r"\d+", str(x)) else "1")
    df["is_pra"] = df["Sesi"].str.lower().str.contains("pra")
    df["score"] = df["Tingkat Kantuk"].apply(extract_kss_value)

    # Track pairs
    paired_sessions = {}
    for _, row in df.iterrows():
        key = (row["p_code"], row["s_idx"])
        if key not in paired_sessions:
            paired_sessions[key] = {"pra": "", "pasca": ""}
        if row["is_pra"]:
            paired_sessions[key]["pra"] = row["score"]
        else:
            paired_sessions[key]["pasca"] = row["score"]

    # Map name fragments and sessions to the finalized string
    mapping_db = []
    
    for _, row in df.iterrows():
        key = (row["p_code"], row["s_idx"])
        kss1 = paired_sessions[key]["pra"] if paired_sessions[key]["pra"] else (row["score"] if row["is_pra"] else "")
        kss2 = paired_sessions[key]["pasca"] if paired_sessions[key]["pasca"] else (row["score"] if not row["is_pra"] else "")
        
        final_kss_string = f"{row['p_code']}_{row['s_idx']}_{kss1}_{kss2}"
        
        # Break full name down into a clean set of searchable tokens/names
        name_tokens = set(re.findall(r"\w+", row["Nama Lengkap"]))
        
        mapping_db.append({
            "full_name": row["Nama Lengkap"],
            "tokens": name_tokens,
            "session": row["s_idx"],
            "target_kss": final_kss_string
        })
        
    return mapping_db


def rename_output_folders():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(base_dir, "output")
    csv_file = os.path.join(base_dir, "Form.csv")
    unsorted_dir = os.path.join(base_dir, "unsorted_folders")

    if not os.path.exists(output_dir):
        print(f"Error: 'output' directory not found at {output_dir}")
        return
    if not os.path.exists(csv_file):
        print(f"Error: Reference database '{csv_file}' missing.")
        return

    print("Parsing Form.csv database structural codes...")
    kss_map_db = build_kss_mapping(csv_file)

    print("Beginning directory renaming matching pass...\n")
    
    # Read the folder structure inside the 'output' folder
    for folder_name in os.listdir(output_dir):
        old_folder_path = os.path.join(output_dir, folder_name)

        if not os.path.isdir(old_folder_path):
            continue

        # Skip folders that are already converted to the KSS format (matches XX_X_X_X structure)
        if re.match(r"^\d{2}[0-9U]\d{2,3}_\d_\d*_\d*$", folder_name):
            continue

        # Parse folder pieces (e.g., "Faiq_sesi_1_0" -> tokens=['faiq'], session='1')
        cleaned_folder = folder_name.lower().replace("_", " ")
        session_match = re.search(r"sesi\s*(\d+)", cleaned_folder)
        
        if not session_match:
            print(f"Skipping (No session info found in name): {folder_name}")
            continue
            
        folder_session = session_match.group(1)
        
        # Remove "sesi" elements to get pure name tokens from folder
        folder_name_clean = re.sub(r"sesi\s*\d+.*", "", cleaned_folder).strip()
        folder_tokens = set(re.findall(r"\w+", folder_name_clean))

        # Look for a match in our database
        matched_kss_target = None
        
        for record in kss_map_db:
            # Check if the session matches first
            if record["session"] == folder_session:
                # Look if any of the folder name tokens overlap with database full name segments
                if folder_tokens.intersection(record["tokens"]):
                    matched_kss_target = record["target_kss"]
                    break

        if matched_kss_target:
            new_folder_path = os.path.join(output_dir, matched_kss_target)
            
            # If a folder with this KSS name already exists, merge contents instead of crashing
            if os.path.exists(new_folder_path):
                for item in os.listdir(old_folder_path):
                    shutil.move(os.path.join(old_folder_path, item), os.path.join(new_folder_path, item))
                os.rmdir(old_folder_path)
                print(f"Merged & Renamed: {folder_name} -> output/{matched_kss_target}")
            else:
                os.rename(old_folder_path, new_folder_path)
                print(f"Renamed: {folder_name} -> output/{matched_kss_target}")
        else:
            # No match found -> safely move to an unsorted folder without changing names
            os.makedirs(unsorted_dir, exist_ok=True)
            shutil.move(old_folder_path, os.path.join(unsorted_dir, folder_name))
            print(f"Warning: No match found for '{folder_name}'. Moved to unsorted_folders/")

    print("\n--- Folder Renaming Process Completed ---")


if __name__ == "__main__":
    rename_output_folders()