import os
import pandas as pd
import json
from mcap.writer import Writer

def csv_to_mcap(output_root):
    # Standardizing topic names to strict ROS-style syntax
    target_files = {
        'mmwave_ss_heart.csv': '/mmwave/ss/heart',
        'mmwave_ss_breath.csv': '/mmwave/ss/breath',
        'mmwave_ti_heart_rate.csv': '/mmwave/ti/heart',
        'mmwave_ti_breath_rate.csv': '/mmwave/ti/breath'
    }

    # Define a simple JSON schema for the vitals
    # This tells Foxglove that the data is a number called "value"
    schema_json = {
        "type": "object",
        "properties": {
            "value": {"type": "number"}
        }
    }

    for root, dirs, files in os.walk(output_root):
        if not any(f in files for f in target_files):
            continue

        folder_name = os.path.basename(root)
        mcap_file_path = os.path.join(root, f"{folder_name}_vitals.mcap")
        
        print(f"Processing: {folder_name}")

        with open(mcap_file_path, "wb") as f:
            writer = Writer(f)
            writer.start()

            # Register the Schema
            schema_id = writer.register_schema(
                name="vitals_msg",
                encoding="jsonschema",
                data=json.dumps(schema_json).encode("utf-8"),
            )

            # Register Channels
            topic_to_channel = {}
            for topic in target_files.values():
                topic_to_channel[topic] = writer.register_channel(
                    schema_id=schema_id,
                    topic=topic,
                    message_encoding="json",
                )

            # Write Data
            for filename, topic in target_files.items():
                if filename in files:
                    csv_path = os.path.join(root, filename)
                    df = pd.read_csv(csv_path)
                    
                    # Convert log_time to datetime objects
                    df['log_time'] = pd.to_datetime(df['log_time'])
                    
                    # Identify value column
                    val_col = [c for c in df.columns if c != 'log_time'][0]
                    df[val_col] = pd.to_numeric(df[val_col], errors='coerce')

                    for _, row in df.iterrows():
                        if pd.isna(row[val_col]):
                            continue
                            
                        # Standard ROS-style timestamp (nanoseconds)
                        timestamp_ns = int(row['log_time'].timestamp() * 1e9)
                        
                        # Create valid JSON message
                        msg_dict = {"value": float(row[val_col])}
                        message_data = json.dumps(msg_dict).encode("utf-8")
                        
                        writer.add_message(
                            channel_id=topic_to_channel[topic],
                            log_time=timestamp_ns,
                            data=message_data,
                            publish_time=timestamp_ns
                        )

            writer.finish()

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_folder = os.path.join(script_dir, "output")

    if os.path.exists(output_folder):
        csv_to_mcap(output_folder)
        print("\nAll MCAP files generated successfully!")
    else:
        print(f"Error: {output_folder} not found.")