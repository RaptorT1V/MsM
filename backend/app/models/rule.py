import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import BigInteger, Boolean, CheckConstraint, Float, ForeignKey, func, Identity, Integer, String, TIMESTAMP, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base

if TYPE_CHECKING:
    from .parameter import Parameter
    from .user import User


# --- Таблица правил мониторинга ---
class MonitoringRule(Base):
    __tablename__ = "monitoring_rules"

    rule_id: Mapped[int] = mapped_column(Integer, Identity(always=True), primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    parameter_id: Mapped[int] = mapped_column(Integer, ForeignKey("parameters.parameter_id", ondelete="CASCADE"), nullable=False, index=True)
    rule_name: Mapped[Optional[str]] = mapped_column(String(110))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default='true')
    comparison_operator: Mapped[str] = mapped_column(String(1), nullable=False)
    threshold: Mapped[float] = mapped_column(Float(precision=8), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint("comparison_operator IN ('>', '<')", name='comparison_operator'),
        UniqueConstraint('user_id', 'parameter_id', 'comparison_operator', 'threshold',
                         name='uq_monitoring_rules_user_parameter_operator_threshold'),
    )

    user: Mapped["User"] = relationship(back_populates="rules")  # N:1 → Несколько правил могут принадлежать одному пользователю (но у одного правила может быть только один владелец)
    parameter: Mapped["Parameter"] = relationship(back_populates="monitoring_rules")  # N:1 → Несколько правил могут содержать один и тот же параметр (но у одного правила может быть только один параметр)
    alerts: Mapped[List["Alert"]] = relationship(back_populates="rule", cascade="all, delete")  # 1:N → Одно правило может вызвать множество тревог

    def __repr__(self):
        return f"<MonitoringRule(id={self.rule_id}, user={self.user_id}, param={self.parameter_id})>"


# --- Таблица журнала тревог ---
class Alert(Base):
    __tablename__ = "alerts"

    alert_id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    rule_id: Mapped[int] = mapped_column(Integer, ForeignKey("monitoring_rules.rule_id", ondelete="CASCADE"), nullable=False, index=True)
    parameter_data_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    alert_message: Mapped[Optional[str]] = mapped_column(String(250))
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default='false')
    alert_timestamp: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, index=True, server_default=func.now())

    rule: Mapped["MonitoringRule"] = relationship(back_populates="alerts")  # N:1 → Несколько тревог может быть вызвано одним правилом [но одна тревога (в плане alert_id) не может быть вызвана несколькими правилами сразу]

    def __repr__(self):
        return f"<Alert(id={self.alert_id}, rule_id={self.rule_id}, ts='{self.alert_timestamp}')>"