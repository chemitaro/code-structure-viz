from pathlib import Path

import pytest

from tests.helpers.sqlalchemy_snapshot import (
    SQLALCHEMY_GOLDEN_CASES,
    render_sqlalchemy_golden_case,
)

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("case", SQLALCHEMY_GOLDEN_CASES)
def test_sqlalchemy_snapshot_lifecycle_matches_reviewed_goldens(case: str) -> None:
    expected_root = ROOT / "tests" / "golden" / "sqlalchemy_snapshot" / case

    actual = render_sqlalchemy_golden_case(case)

    assert {path.name for path in expected_root.iterdir()} == set(actual)
    for name, content in actual.items():
        assert content == (expected_root / name).read_bytes()
