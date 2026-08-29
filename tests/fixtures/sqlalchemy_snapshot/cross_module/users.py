from .base import Base
from .groups import Group
from .tables import membership
from sqlalchemy.orm import Mapped, relationship


class User(Base):
    __tablename__ = "users"
    groups: Mapped[list[Group]] = relationship(Group, secondary=membership)
