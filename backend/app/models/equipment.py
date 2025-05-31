from typing import List, TYPE_CHECKING

from sqlalchemy import ForeignKey, Enum as SQLEnum, Identity, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from .enums import LineTypesEnum

if TYPE_CHECKING:
    from .parameter import Parameter, ParameterType  # noqa F401
    from .user import User  # noqa F401


'''
===================
    Справочники     
===================
'''


# --- Цехи предприятия ---
class Shop(Base):
    __tablename__ = "shops"

    shop_id: Mapped[int] = mapped_column(Integer, Identity(always=True), primary_key=True)
    shop_name: Mapped[str] = mapped_column(String(35), nullable=False, unique=True)

    lines: Mapped[List["Line"]] = relationship(back_populates="shop")  # 1:N → Один цех содержит несколько линий

    def __repr__(self):
        """ Возвращает строковое представление объекта Shop """
        return f"<Shop(id={self.shop_id}, name='{self.shop_name}')>"


# --- Агрегаты предприятия ---
class AggregateType(Base):
    __tablename__ = "aggregate_types"

    aggregate_type_id: Mapped[int] = mapped_column(Integer, Identity(always=True), primary_key=True)
    aggregate_type_name: Mapped[str] = mapped_column(String(55), nullable=False, unique=True)

    aggregates: Mapped[List["Aggregate"]] = relationship(back_populates="aggregate_type")  # 1:N → Один тип агрегата содержит несколько конкретных агрегатов этого типа (например, тип агрегата = "агломашина", а этих агломашин будет 4 в аглоцехе, по 1 на каждую линию)

    def __repr__(self):
        """ Возвращает строковое представление объекта AggregateType """
        return f"<AggregateType(id={self.aggregate_type_id}, name='{self.aggregate_type_name}')>"


# --- Исполнительные механизмы (актуаторы) предприятия ---
class ActuatorType(Base):
    __tablename__ = "actuator_types"

    actuator_type_id: Mapped[int] = mapped_column(Integer, Identity(always=True), primary_key=True)
    actuator_type_name: Mapped[str] = mapped_column(String(60), nullable=False, unique=True)

    actuators: Mapped[List["Actuator"]] = relationship(back_populates="actuator_type")  # 1:N → Один тип актуатора может иметь несколько экземпляров (например, тип актуатора = "электродвигатель постоянного тока", а этих двигателей будет множество по всему предприятию)

    def __repr__(self):
        """ Возвращает строковое представление объекта ActuatorType """
        return f"<ActuatorType(id={self.actuator_type_id}, name='{self.actuator_type_name}')>"


'''
========================
    Таблицы иерархии     
========================
'''


# --- Производственные линии, находящиеся внутри цехов ---
class Line(Base):
    __tablename__ = "lines"

    line_id: Mapped[int] = mapped_column(Integer, Identity(always=True), primary_key=True)
    shop_id: Mapped[int] = mapped_column(Integer, ForeignKey("shops.shop_id", ondelete="CASCADE"), nullable=False)
    line_type: Mapped[LineTypesEnum] = mapped_column(SQLEnum(LineTypesEnum, name='line_types',
                                                             create_type=False, native_enum=False,
                                                             values_callable=lambda x: [e.value for e in x]),
                                                     nullable=False)
    shop: Mapped["Shop"] = relationship(back_populates="lines")  # N:1 → Несколько линий находятся в одном цехе (но одна линия не может быть в двух цехах одновременно)
    aggregates: Mapped[List["Aggregate"]] = relationship(back_populates="line")  # 1:N → На одной линии установлены несколько агрегатов

    __table_args__ = (
        UniqueConstraint('shop_id', 'line_type'),  # Каждый номер линии уникален. В одном цехе не может быть две первых или три вторых линии.
    )

    def __repr__(self):
        """ Возвращает строковое представление объекта Line """
        return f"<Line(id={self.line_id}, type='{self.line_type.value}', shop_id={self.shop_id})>"


# --- Агрегаты, находящиеся на производственных линиях ---
class Aggregate(Base):
    __tablename__ = "aggregates"

    aggregate_id: Mapped[int] = mapped_column(Integer, Identity(always=True), primary_key=True)
    line_id: Mapped[int] = mapped_column(Integer, ForeignKey("lines.line_id", ondelete="CASCADE"), nullable=False)
    aggregate_type_id: Mapped[int] = mapped_column(Integer, ForeignKey("aggregate_types.aggregate_type_id", ondelete="RESTRICT"), nullable=False)

    line: Mapped["Line"] = relationship(back_populates="aggregates")  # N:1 → Несколько агрегатов установлены на одной линии (но один и тот же агрегат не может быть установлен одновременно на двух или более линиях)
    aggregate_type: Mapped["AggregateType"] = relationship(back_populates="aggregates")  # N:1 → Несколько агрегатов могут быть одного типа (но один и тот же агрегат не может быть двух типов одновременно)
    actuators: Mapped[List["Actuator"]] = relationship(back_populates="aggregate")  # 1:N → Один агрегат состоит из нескольких исполнительных механизмов (актуаторов)

    __table_args__ = (
        UniqueConstraint('line_id', 'aggregate_type_id'),  # На одной линии не может быть два одинаковых агрегата, например 2 агломашины.
    )

    def __repr__(self):
        """ Возвращает строковое представление объекта Aggregate """
        return f"<Aggregate(id={self.aggregate_id}, type_id={self.aggregate_type_id}, line_id={self.line_id})>"


# --- Исполнительные механизмы (актуаторы), находящиеся внутри агрегатов ---
class Actuator(Base):
    __tablename__ = "actuators"

    actuator_id: Mapped[int] = mapped_column(Integer, Identity(always=True), primary_key=True)
    aggregate_id: Mapped[int] = mapped_column(Integer, ForeignKey("aggregates.aggregate_id", ondelete="CASCADE"), nullable=False, index=True)
    actuator_type_id: Mapped[int] = mapped_column(Integer, ForeignKey("actuator_types.actuator_type_id", ondelete="RESTRICT"), nullable=False, index=True)

    # --> Здесь нету UniqueConstraint, т.к. в очень редких случаях один агрегат может содержать в себе два актуатора одинакового типа (например, два электродвигателя) <--

    aggregate: Mapped["Aggregate"] = relationship(back_populates="actuators")  # N:1 → Несколько актуаторов входят в состав одного агрегата (но один и тот же актуатор не может входить в состав двух агрегатов одновременно)
    actuator_type: Mapped["ActuatorType"] = relationship(back_populates="actuators")  # N:1 → Несколько актуаторов могут быть одного типа (но один и тот же актуатор не может быть двух типов одновременно)
    parameters: Mapped[List["Parameter"]] = relationship(back_populates="actuator")  # 1:N → Один актуатор имеет несколько измерительных параметров

    def __repr__(self):
        """ Возвращает строковое представление объекта Actuator """
        return f"<Actuator(id={self.actuator_id}, type_id={self.actuator_type_id}, aggregate_id={self.aggregate_id})>"