import json
from pathlib import Path

from backend.services.major_taxonomy_service import major_taxonomy_service


def test_all_major_directions_are_registered() -> None:
    major_data_path = Path('public/data/major_data_processed.json')
    assert major_data_path.exists(), "major data file should exist for taxonomy validation"

    with major_data_path.open(encoding='utf-8') as f:
        data = json.load(f)

    unique_directions = {
        item.get('major_direction')
        for item in data
        if item.get('major_direction')
    }

    missing = sorted(
        direction
        for direction in unique_directions
        if major_taxonomy_service.normalise_direction(direction) is None
    )

    assert not missing, f"Unmapped major directions found: {missing}"
