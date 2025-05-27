from app.db.base_class import Base  # noqa

# --- ВСЕ модели SQLAlchemy ---
from app.models.equipment import Shop, AggregateType, ActuatorType, Line, Aggregate, Actuator  # noqa
from app.models.parameter import Parameter, ParameterType, ParameterData  # noqa
from app.models.rule import MonitoringRule, Alert  # noqa
from app.models.setting import UserSetting  # noqa
from app.models.user import User, JobTitle  # noqa