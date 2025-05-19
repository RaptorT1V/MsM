from typing import List, TYPE_CHECKING
from sqlalchemy import Boolean, Enum as SQLEnum, CheckConstraint, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base
from .enums import AlarmTypesEnum

if TYPE_CHECKING:
    from .user import User


# --- Таблица настроек пользователя ---
class UserSetting(Base):
    __tablename__ = "user_settings"

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    theme: Mapped[str] = mapped_column(String(10), nullable=False, server_default='light')
    language: Mapped[str] = mapped_column(String(5), nullable=False, server_default='ru')
    alarm_types: Mapped[List[AlarmTypesEnum]] = mapped_column(ARRAY(SQLEnum(AlarmTypesEnum, name='alarm_types',
                                                                            create_type=False)),
                                                              nullable=False, server_default=AlarmTypesEnum.NOTIFICATION)
    is_rules_public: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default='false')

    __table_args__ = (
        CheckConstraint("theme IN ('light', 'dark')", name='theme_option'),
        CheckConstraint("language IN ('ru', 'en')", name='language_option'),
    )

    user: Mapped["User"] = relationship(back_populates="settings")  # 1:1 → Одни настройки соответствуют только одному пользователю

    def __repr__(self):
        return f"<UserSetting(user_id={self.user_id}, theme='{self.theme}')>"