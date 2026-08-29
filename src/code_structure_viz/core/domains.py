from __future__ import annotations

from typing import Final, Literal

DomainName = Literal["python", "sqlalchemy"]

SNAPSHOT_DOMAINS: Final[tuple[DomainName, ...]] = ("python", "sqlalchemy")
DIFF_DOMAINS: Final[tuple[DomainName, ...]] = ("python",)
