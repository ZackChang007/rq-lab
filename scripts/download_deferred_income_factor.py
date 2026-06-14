"""Download deferred_income factor using rqdatac.get_factor() API."""
import rqdatac
import pandas as pd
from utils.common import setup_license
import os
from pathlib import Path

def download_deferred_income_factor():
    """Download and save deferred_income factor to parquet."""
    try:
        # Initialize license
        setup_license()
        rqdatac.init()

        # Get A-share stock list
        stocks = rqdatac.all_instruments(type='CS')['order_book_id'].tolist()
        print(f'Found {len(stocks)} stocks')

        # Download factor data
        print('Downloading deferred_income factor...')
        df = rqdatac.get_factor(stocks, 'deferred_income', '2010-01-01', '2026-06-13', expect_df=True)

        if df is None or df.empty:
            print('No data returned')
            return {
                'success': True,
                'factor_name': 'deferred_income',
                'rows': 0,
                'file_size_mb': 0,
                'error': None
            }
        else:
            print(f'Data shape: {df.shape}')
            rows = len(df)

            # Save to parquet
            output_dir = Path('data/factor')
            output_dir.mkdir(parents=True, exist_ok=True)
            file_path = output_dir / 'deferred_income.parquet'

            df.to_parquet(str(file_path), engine='pyarrow', compression='snappy')

            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            print(f'Saved to {file_path} ({file_size_mb:.2f} MB)')

            return {
                'success': True,
                'factor_name': 'deferred_income',
                'rows': rows,
                'file_size_mb': round(file_size_mb, 2),
                'error': None
            }

    except Exception as e:
        print(f'Error: {str(e)}')
        return {
            'success': False,
            'factor_name': 'deferred_income',
            'rows': 0,
            'file_size_mb': 0,
            'error': str(e)
        }

if __name__ == '__main__':
    result = download_deferred_income_factor()
    print(f'Result: {result}')