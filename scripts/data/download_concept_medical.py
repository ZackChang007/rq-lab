"""Download medical concept sector data from RQData."""

import json
import rqdatac
from utils.common import setup_license
from pathlib import Path


def main():
    # Initialize license
    setup_license()

    # Initialize RQData
    rqdatac.init()

    # Concept name
    concept_name = '医疗器械'

    # Output path
    output_dir = Path('C:/gh/rq-lab/data/stock')
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f'concept_{concept_name}.json'

    try:
        # Fetch concept data
        data = rqdatac.concept(concept_name)

        # Check if data is empty (concept() returns a list)
        if data is None or len(data) == 0:
            result = {
                'success': True,
                'concept_name': concept_name,
                'rows': 0,
                'error': None
            }
        else:
            # Save to JSON file (data is already a list)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            result = {
                'success': True,
                'concept_name': concept_name,
                'rows': len(data),
                'error': None
            }

    except Exception as e:
        result = {
            'success': False,
            'concept_name': concept_name,
            'rows': 0,
            'error': str(e)
        }

    return result


if __name__ == '__main__':
    result = main()
    print(json.dumps(result, ensure_ascii=False, indent=2))
