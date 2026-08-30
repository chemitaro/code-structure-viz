from sqlalchemy import CheckConstraint, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

raise RuntimeError("this fixture must never execute")


class Base(DeclarativeBase):
    pass


class Item(Base):
    __tablename__ = "items"
    __table_args__ = (
        CheckConstraint("private-check-a"),
        CheckConstraint("private-check-b"),
        Index(None, object()),
        Index(None, object()),
    )

    id: Mapped[int] = mapped_column()
