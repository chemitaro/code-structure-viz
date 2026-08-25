from pathlib import Path

import pytest

from tests.helpers.golden import GOLDEN_CASES, render_case

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("case", GOLDEN_CASES)
def test_python_snapshot_lifecycle_matches_reviewed_goldens(case: str) -> None:
    expected_root = ROOT / "tests" / "golden" / "python_snapshot" / case

    actual = render_case(case)

    assert {path.name for path in expected_root.iterdir()} == set(actual)
    for name, content in actual.items():
        assert content == (expected_root / name).read_bytes()
