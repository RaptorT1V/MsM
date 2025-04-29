import enum


class AlarmTypesEnum(str, enum.Enum):
    SIREN = 'siren'
    FLASH = 'flash'
    VIBRATION = 'vibration'
    NOTIFICATION = 'notification'


class LineTypesEnum(str, enum.Enum):
    FIRST = 'Первая'
    SECOND = 'Вторая'
    THIRD = 'Третья'
    FOURTH = 'Четвёртая'