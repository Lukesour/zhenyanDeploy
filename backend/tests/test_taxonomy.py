import json
from pathlib import Path

from backend.services.major_taxonomy_service import major_taxonomy_service


def _load_all_major_data() -> list[dict]:
    manifest_path = Path('public/data/major-data-manifest.json')
    assert manifest_path.exists(), "major data manifest should exist for taxonomy validation"

    with manifest_path.open(encoding='utf-8') as f:
        manifest = json.load(f)

    all_data: list[dict] = []

    for chunk in manifest.get('chunks', []):
        chunk_path = Path('public') / chunk['file']
        assert chunk_path.exists(), f"major data chunk missing: {chunk_path}"

        with chunk_path.open(encoding='utf-8') as chunk_file:
            all_data.extend(json.load(chunk_file))

    return all_data


def test_all_major_directions_are_registered() -> None:
    data = _load_all_major_data()

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
