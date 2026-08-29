from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Zed(Base):
    __tablename__ = "zed"


class Alpha(Base):
    __tablename__ = "alpha"
