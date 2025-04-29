import datetime
from typing import Optional, List

from app.db.base_class import Base
from sqlalchemy import (Integer, String, func, ForeignKey, CHAR, TIMESTAMP, CheckConstraint)
from sqlalchemy.orm import Mapped, mapped_column, relationship


class JobTitle(Base):
    __tablename__ = "job_titles"

    job_title_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_title_name: Mapped[str] = mapped_column(String(65), nullable=False, unique=True)

    users: Mapped[List["User"]] = relationship(back_populates="job_title")

    def __repr__(self):
        return f"<JobTitle(id={self.job_title_id}, name='{self.job_title_name}')>"


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_titles_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("job_titles.job_title_id", ondelete="SET NULL"), index=True)
    first_name: Mapped[str] = mapped_column(String(26), nullable=False)
    last_name: Mapped[str] = mapped_column(String(36), nullable=False)
    middle_name: Mapped[Optional[str]] = mapped_column(String(24))
    email: Mapped[str] = mapped_column(String(60), nullable=False, unique=True)
    phone: Mapped[str] = mapped_column(CHAR(12), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(228), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("email ~* '^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$'", name='email_format'),
        CheckConstraint("phone ~ '^\+7\d{10}$'", name='phone_format'),
    )

    job_title: Mapped[Optional["JobTitle"]] = relationship(back_populates="users")

    def __repr__(self):
        return f"<User(id={self.user_id}, email='{self.email}')>"