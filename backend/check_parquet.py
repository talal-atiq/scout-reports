import pandas as pd
from pathlib import Path
import sys

def check_parquet_schema():
    backend_dir = Path("d:/scout-reports/backend")
    df = pd.read_parquet(backend_dir / "data" / "1911273.parquet")
    
    print("--- PARQUET COLUMNS ---")
    # Print columns in chunks of 5 for readability
    cols = list(df.columns)
    for i in range(0, len(cols), 5):
        print(cols[i:i+5])
        
    print("\n--- EVENT TYPES ---")
    print(df["type"].value_counts().head(25))
    
    # Check for xG column
    xg_cols = [c for c in cols if 'xg' in c.lower() or 'expected' in c.lower()]
    print("\n--- xG RELATED COLUMNS ---")
    print(xg_cols)
    
    # Check for possession metrics
    poss_cols = [c for c in cols if 'poss' in c.lower()]
    print("\n--- POSSESSION RELATED COLUMNS ---")
    print(poss_cols)

if __name__ == "__main__":
    check_parquet_schema()
