from pathlib import Path

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

Path("TARGET_CODE_EXECUTED").write_text("DO_NOT_PUBLISH_THIS_SECRET")


class Base(DeclarativeBase):
    pass


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    users: Mapped[list["User"]] = relationship("User", back_populates="account")


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
        CheckConstraint("DO_NOT_PUBLISH_THIS_SECRET", name="ck_users_email"),
        Index("ix_users_email", "email"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, default="DO_NOT_PUBLISH_THIS_SECRET"
    )
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))
    account: Mapped[Account] = relationship("Account", back_populates="users")


class Admin(User):
    __tablename__ = "admins"
