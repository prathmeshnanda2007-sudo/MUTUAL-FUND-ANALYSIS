import pandas as pd
from sqlalchemy import create_engine, text
from pathlib import Path
import os
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
from scripts.config import DB_URI_NON_POOLED_SA

OUTPUT_DIR = BASE_DIR / "powerbi_connector"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def export_table_to_csv(conn, table_name: str):
    print(f"Exporting {table_name}...")
    df = pd.read_sql_query(text(f"SELECT * FROM {table_name}"), conn)  # nosec
    output_file = OUTPUT_DIR / f"{table_name}.csv"
    df.to_csv(output_file, index=False)
    print(f"  -> Saved {len(df)} rows to {output_file.name}")

if __name__ == "__main__":
    engine = create_engine(DB_URI_NON_POOLED_SA)
    
    with engine.connect() as conn:
        # Get list of all tables in the public schema
        result = conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname='public';"))
        tables = [row[0] for row in result]

        print(f"Found {len(tables)} tables. Beginning export...")
        for table in tables:
            export_table_to_csv(conn, table)
            
    # Fix encoding issue for Windows
    sys.stdout.reconfigure(encoding='utf-8')
    print("\n✅ Success! All data exported to the `powerbi_connector` directory.")
    print("You can now connect Power BI Desktop to these CSVs and build your Star Schema.")
