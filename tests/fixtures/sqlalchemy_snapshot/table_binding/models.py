from sqlalchemy import Column, Integer, Table
from sqlalchemy.orm import DeclarativeBase

users = Table("users", object(), Column("id", Integer, primary_key=True), schema="auth")


class Base(DeclarativeBase):
    pass


class User(Base):
    __table__ = users
