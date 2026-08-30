from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Safe(Base):
    __tablename__ = "safe"


unknown = dynamic_factory()
