from app.db.base_class import Base
from sqlalchemy import TIMESTAMP, Float, BigInteger, Integer, String, ForeignKey, UniqueConstraint, func, Identity
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional, TYPE_CHECKING
import datetime

if TYPE_CHECKING:
    from .equipment import Actuator
    from .rule import MonitoringRule


# --- Справочник типов параметров ---
class ParameterType(Base):
    __tablename__ = "parameter_types"

    parameter_type_id: Mapped[int] = mapped_column(Integer, Identity(always=True), primary_key=True)
    parameter_type_name: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    parameter_unit: Mapped[Optional[str]] = mapped_column(String(20))

    parameters: Mapped[List["Parameter"]] = relationship(back_populates="parameter_type")  # 1:N → Один тип параметра может иметь несколько экземпляров (например, тип параметра = "электрический ток", а его используют множество разных актуаторов)

    def __repr__(self):
        return f"<ParameterType(id={self.parameter_type_id}, name='{self.parameter_type_name}')>"


# --- Таблица связи "Актуатор <-> Тип Параметра" ---
class Parameter(Base):
    __tablename__ = "parameters"

    parameter_id: Mapped[int] = mapped_column(Integer, Identity(always=True), primary_key=True)
    actuator_id: Mapped[int] = mapped_column(Integer, ForeignKey("actuators.actuator_id", ondelete="CASCADE"), nullable=False)
    parameter_type_id: Mapped[int] = mapped_column(Integer, ForeignKey("parameter_types.parameter_type_id", ondelete="RESTRICT"), nullable=False)

    actuator: Mapped["Actuator"] = relationship(back_populates="parameters")  # N:1 → Несколько параметров могут принадлежать одному актуатору [но один и тот же параметр (именно айдишник параметра, а не его тип) не может принадлежать двум актуаторам одновременно]
    parameter_type: Mapped["ParameterType"] = relationship(back_populates="parameters")  # N:1 → Несколько параметров могут быть одного типа (но один и тот же параметр не может быть двух типов одновременно)
    monitoring_rules: Mapped[List["MonitoringRule"]] = relationship(back_populates="parameter")  # 1:N → Один параметр может быть включён в несколько различных пользовательских правил мониторинга
    parameter_data: Mapped[List["ParameterData"]] = relationship(back_populates="parameter", cascade="all, delete", passive_deletes=True)  # 1:N → Данные для одного параметра в определённый момент времени могут быть записаны множество раз

    __table_args__ = (
        UniqueConstraint('actuator_id', 'parameter_type_id'),  # У одного актуатора не может быть 2 одинаковых параметра (например, 2 электрических тока)
    )

    def __repr__(self):
        return f"<Parameter(id={self.parameter_id}, actuator_id={self.actuator_id}, type_id={self.parameter_type_id})>"


# --- Таблица данных временных рядов (гипертаблица TimeScaleDB) ---
class ParameterData(Base):
    __tablename__ = "parameter_data"

    parameter_data_id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=False)
    parameter_id: Mapped[int] = mapped_column(Integer, ForeignKey("parameters.parameter_id", ondelete="CASCADE"), nullable=False, primary_key=True)
    parameter_value: Mapped[float] = mapped_column(Float(precision=8), nullable=False)
    data_timestamp: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), primary_key=True)

    parameter: Mapped["Parameter"] = relationship(back_populates="parameter_data")  # N:1 → Много записей данных для одного параметра

    def __repr__(self):
        return f"<ParameterData(param_id={self.parameter_id}, ts='{self.data_timestamp}', val={self.parameter_value})>"