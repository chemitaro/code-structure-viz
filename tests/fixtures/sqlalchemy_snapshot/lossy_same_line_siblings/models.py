# ruff: noqa: E501

from sqlalchemy import CheckConstraint, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

raise RuntimeError("this fixture must never execute")


class Base(DeclarativeBase):
    pass


class Item(Base):
    __tablename__ = "items"
    __table_args__ = (CheckConstraint("a"), CheckConstraint("b"), Index(None, object()), Index(None, object()))  # fmt: skip
    id: Mapped[int] = mapped_column()
