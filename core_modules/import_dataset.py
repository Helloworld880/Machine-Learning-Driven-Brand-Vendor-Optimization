import pandas as pd
import sqlite3
import os

DB_PATH = "Data layer/vendors.db"
DATA_PATH = "Data layer/vendor_data.csv"  # change filename to your dataset

def import_dataset():
    if not os.path.exists(DATA_PATH):
        print(f"❌ Dataset not found: {DATA_PATH}")
        return

    # Load the CSV
    df = pd.read_csv(DATA_PATH)
    print(f"✅ Loaded {len(df)} rows from {DATA_PATH}")

    # Connect to SQLite
    conn = sqlite3.connect(DB_PATH)

    # Import into vendors table
    df.to_sql("vendors", conn, if_exists="replace", index=False)
    conn.commit()
    conn.close()

    print("✅ Vendor dataset successfully imported into SQLite database.")

if __name__ == "__main__":
    import_dataset()
