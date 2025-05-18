import enum


# --- Типы уведомлений при возникшей тревоге ---
class AlarmTypesEnum(str, enum.Enum):
    SIREN = 'SIREN'
    FLASH = 'FLASH'
    VIBRATION = 'VIBRATION'
    NOTIFICATION = 'NOTIFICATION'


# --- Номера линий ---
class LineTypesEnum(str, enum.Enum):
    FIRST = 'Первая'
    SECOND = 'Вторая'
    THIRD = 'Третья'
    FOURTH = 'Четвёртая'