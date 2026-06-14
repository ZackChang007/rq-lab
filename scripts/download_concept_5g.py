"""Download 5G concept sector data using rqdatac.concept() API."""
import rqdatac
import json
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import setup_license

# Initialize license
setup_license()
rqdatac.init()

# Get 5G concept data
try:
    # rqdatac.concept() returns a list of stock codes for the concept
    # Use '5G概念' as the concept name (Chinese)
    data = rqdatac.concept('5G概念')

    if data is None or len(data) == 0:
        result = {'success': True, 'concept_name': '5G', 'rows': 0, 'error': None}
    else:
        # Save to JSON
        output_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                    'data', 'stock', 'concept_5G.json')

        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Convert to list if needed and count rows
        stock_list = list(data) if not isinstance(data, list) else data
        rows = len(stock_list)

        # Save as JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(stock_list, f, ensure_ascii=False, indent=2)

        result = {'success': True, 'concept_name': '5G', 'rows': rows, 'error': None}

    print(json.dumps(result, ensure_ascii=False))

except Exception as e:
    result = {'success': False, 'concept_name': '5G', 'rows': 0, 'error': str(e)}
    print(json.dumps(result, ensure_ascii=False))
