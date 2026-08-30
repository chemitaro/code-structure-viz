from sqlalchemy import CheckConstraint, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Secret(Base):
    __tablename__ = "secret"
    __table_args__ = (CheckConstraint("private-check"),)
    value: Mapped[str] = mapped_column(
        String(255),
        default="private-default",
        server_default="private-server-default",
    )
    related: Mapped["Other"] = relationship(
        "Other",
        primaryjoin="private-join",
    )
