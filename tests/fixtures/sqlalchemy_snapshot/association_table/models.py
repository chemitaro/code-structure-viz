from sqlalchemy import Column, Integer, Table
from sqlalchemy.orm import DeclarativeBase, Mapped, relationship

membership = Table("membership", object(), Column("id", Integer))


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    groups: Mapped[list["Group"]] = relationship("Group", secondary=membership)


class Group(Base):
    __tablename__ = "groups"
