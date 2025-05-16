import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import CHAR, TIMESTAMP, CheckConstraint, ForeignKey, Identity, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base

if TYPE_CHECKING:
    from .rule import MonitoringRule
    from .setting import UserSetting


# --- Справочник типов должностей ---
class JobTitle(Base):
    __tablename__ = "job_titles"

    job_title_id: Mapped[int] = mapped_column(Integer, Identity(always=True), primary_key=True)
    job_title_name: Mapped[str] = mapped_column(String(65), nullable=False, unique=True)

    users: Mapped[List["User"]] = relationship(back_populates="job_title")  # 1:N → Одну должность могут иметь несколько рабочих

    def __repr__(self):
        return f"<JobTitle(id={self.job_title_id}, name='{self.job_title_name}')>"


# --- Таблица, содержащая информацию о пользователях ---
class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(Integer, Identity(always=True), primary_key=True)
    job_title_id: Mapped[int] = mapped_column(Integer, ForeignKey("job_titles.job_title_id", ondelete="RESTRICT"), nullable=False, index=True)
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

    job_title: Mapped["JobTitle"] = relationship(back_populates="users")  # N:1 → Несколько рабочих могут иметь одну и ту же должность (но один рабочий может иметь только одну должность)
    rules: Mapped[List["MonitoringRule"]] = relationship(back_populates="user", cascade="all, delete")  # 1:N → Один пользователь может иметь несколько правил
    settings: Mapped["UserSetting"] = relationship(back_populates="user", cascade="all, delete-orphan")  # 1:1 → Одному пользователю соответствуют только одни настройки

    def __repr__(self):
        return f"<User(id={self.user_id}, email='{self.email}')>"