"""Download reserve ratio data from RQData."""
import rqdatac
import pandas as pd
from utils.common import setup_license
import os

# Initialize license
setup_license()
rqdatac.init()

# Download reserve ratio data
try:
    df = rqdatac.econ.get_reserve_ratio(start_date="2010-01-01", end_date="2026-06-13")

    if df is None or df.empty:
        print("RESULT: success=true, rows=0, empty data returned")
    else:
        # Save to parquet
        output_path = "data/macro/reserve_ratio.parquet"
        df.to_parquet(output_path, index=True)

        # Get file size
        file_size = os.path.getsize(output_path)
        file_size_mb = file_size / (1024 * 1024)

        print(f"RESULT: success=true, rows={len(df)}, file_size_mb={file_size_mb:.6f}")
        print(f"Columns: {list(df.columns)}")
        print(f"Date range: {df.index.min()} to {df.index.max()}")
        print("Sample data:")
        print(df.head())
except Exception as e:
    print(f"RESULT: success=false, error={str(e)}")
