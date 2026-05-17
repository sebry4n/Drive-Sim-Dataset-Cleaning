import os
import re
import pandas as pd


def extract_kss_value(kantuk_string):
    """Extracts the first digit integer from the sleepiness scale string."""
    if pd.isna(kantuk_string):
        return ""
    match = re.search(r"\d+", str(kantuk_string))
    return match.group(0) if match else ""


def generate_kss_excel(input_csv, output_excel):
    if not os.path.exists(input_csv):
        print(f"Error: Source file '{input_csv}' not found in this directory.")
        return

    # Read the raw CSV questionnaire file
    df = pd.read_csv(input_csv)

    # Clean whitespace from string columns and headers
    df.columns = [col.strip() for col in df.columns]
    df["Nama Lengkap"] = df["Nama Lengkap"].str.strip()
    df["Sesi"] = df["Sesi"].str.strip()

    # 1. Standardize Participant Code (KODE PARTISIPAN)
    # Rules: (ITS) Angkatan + 3 last digits of NRP. (Umum) 22U
    def compute_participant_code(row):
        status = str(row["Status Partisipan"]).lower()
        if "umum" in status:
            return "22U"

        # Safe fallback logic if NRP is missing/short
        nrp_str = str(row["NRP"]).split(".")[0].strip()  # Removes trailing float decimals if any
        nrp_suffix = nrp_str[-3:] if len(nrp_str) >= 3 else "000"

        angkatan_str = str(row["Angkatan"]).split(".")[0].strip()
        angkatan_prefix = angkatan_str[-2:] if len(angkatan_str) >= 2 else "23"

        return f"{angkatan_prefix}{nrp_suffix}"

    df["participant_code"] = df.apply(compute_participant_code, axis=1)

    # 2. Extract Session Number (1, 2, or 3)
    def extract_session_num(row):
        session_str = str(row["Sesi"])
        match = re.search(r"\d+", session_str)
        return match.group(0) if match else "1"

    df["session_idx"] = df.apply(extract_session_num, axis=1)

    # 3. Determine row category (Pra vs Pasca)
    df["is_pra"] = df["Sesi"].str.lower().str.contains("pra")

    # Extract single rating digit
    df["kss_score"] = df["Tingkat Kantuk"].apply(extract_kss_value)

    # Dictionary to link paired scores: (participant_code, session_idx) -> { 'pra': X, 'pasca': Y }
    paired_sessions = {}

    for _, row in df.iterrows():
        p_code = row["participant_code"]
        s_idx = row["session_idx"]
        key = (p_code, s_idx)

        if key not in paired_sessions:
            paired_sessions[key] = {"pra": "", "pasca": ""}

        if row["is_pra"]:
            paired_sessions[key]["pra"] = row["kss_score"]
        else:
            paired_sessions[key]["pasca"] = row["kss_score"]

    # 4. Compile the final formatted target strings back onto the dataset rows
    compiled_codes = []
    for _, row in df.iterrows():
        p_code = row["participant_code"]
        s_idx = row["session_idx"]
        key = (p_code, s_idx)

        kss1 = paired_sessions[key]["pra"]
        kss2 = paired_sessions[key]["pasca"]

        # If a participant filled out only one of the forms, fall back to their current row rating
        if not kss1:
            kss1 = row["kss_score"] if row["is_pra"] else ""
        if not kss2:
            kss2 = row["kss_score"] if not row["is_pra"] else ""

        # Construct final string: KODE_SESI_KSS1_KSS2
        formatted_code = f"{p_code}_{s_idx}_{kss1}_{kss2}"
        compiled_codes.append(formatted_code)

    # Overwrite target column with computed codes
    df["PENAMAAAN KSS"] = compiled_codes

    # Drop temporary calculation columns before saving out
    df = df.drop(columns=["participant_code", "session_idx", "is_pra", "kss_score"])

    # Save output to an Excel workbook (.xlsx) cleanly
    df.to_excel(output_excel, index=False, engine="openpyxl")
    print(f"Success! Form parsed and Excel compiled saved to: {output_excel}")


if __name__ == "__main__":
    input_filename = "Form.csv"
    output_filename = "Form_Formatted.xlsx"

    generate_kss_excel(input_filename, output_filename)