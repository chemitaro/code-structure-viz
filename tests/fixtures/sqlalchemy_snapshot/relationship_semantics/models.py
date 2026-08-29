from sqlalchemy import Column, Integer, Table
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

raise RuntimeError("this fixture must never execute")

membership = Table("membership", object(), Column("id", Integer))


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    groups: Mapped[list["Group"]] = relationship(
        "Group",
        secondary=membership,
        back_populates="users",
        primaryjoin=id == object(),
        foreign_keys=[id],
    )


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    users: Mapped[list[User]] = relationship("User", back_populates="groups")


class Admin(User):
    __tablename__ = "admins"
