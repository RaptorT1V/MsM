import enum


# --- Типы уведомлений при возникшей тревоге ---
class AlarmTypesEnum(str, enum.Enum):
    SIREN = 'siren'
    FLASH = 'flash'
    VIBRATION = 'vibration'
    NOTIFICATION = 'notification'


# --- Номера линий ---
class LineTypesEnum(str, enum.Enum):
    FIRST = 'Первая'
    SECOND = 'Вторая'
    THIRD = 'Третья'
    FOURTH = 'Четвёртая'