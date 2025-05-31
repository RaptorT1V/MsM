from app.db.base_class import Base  # noqa F401

# --- ВСЕ модели SQLAlchemy ---
from app.models.equipment import Shop, AggregateType, ActuatorType, Line, Aggregate, Actuator  # noqa F401
from app.models.parameter import Parameter, ParameterType, ParameterData  # noqa F401
from app.models.rule import MonitoringRule, Alert  # noqa F401
from app.models.setting import UserSetting  # noqa F401
from app.models.user import User, JobTitle  # noqa F401