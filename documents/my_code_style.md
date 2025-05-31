<h2 align="center" style="color: #02ed45; font-family: cursive;">Мой стиль оформления кода</h2>

<h2 style="color: #ffe500; font-family: Roboto, Geneva, Helvetica, sans-serif;">Оглавление</h2>

1. [Импорты](#1-импорты)
2. [Классы](#2-классы)
3. [Функции](#3-функции)
4. [Комментарии](#4-комментарии)
5. [Переносы](#5-переносы)
6. [Логирование](#6-логирование)
7. [Коммиты](#7-коммиты)



<a id="1-импорты"></a>
## Импорты

Импорты подразделяются на три вида:
 1. В начале — стандартные библиотеки Python;
 2. В середине — библиотеки сторонних разработчиков;
 3. В конце — собственные модули;
 4. [Опционально] В самом конце — импорты `IF TYPE_CHECKING:`.

Если из одного модуля импортируется несколько функций/классов, следует расположить их в алфавитном порядке и записать на 1 строке. 
<br> Переносить `import` также не стоит. Нужно записать всё на одной строке, через запятую.

Исключением являются импорты моих модулей equipment и parameter: их классы следует располагать в том порядке, в каком они записаны в этих модулях (по старшинству иерархии + сначала идут справочники). 
<br> Несмотря на то, что shop является одновременно и справочником, и таблицей иерархии, его следует писать после справочников и перед таблицами иерархии. 

Между видами импортов пропускается одна строка.
<br> После всех импортов пропускаются две строки.

Итоговый результат будет точно такой же, если нажать на клавиатуре комбинацию клавиш `ctrl + alt + O` в PyCharm — _(imports optimized)_.

> Пример оформления импортов в моём стиле:
```python
import datetime
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import CHAR, TIMESTAMP, CheckConstraint, ForeignKey, Identity, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.repositories.equipment_repository import aggregate_type_repository, actuator_type_repository, shop_repository, line_repository, aggregate_repository, actuator_repository

if TYPE_CHECKING:
    from .rule import MonitoringRule
    from .setting import UserSetting


# ... остальной код, начинается с этой строчки ...
```

<a id="2-классы"></a>
## Классы

Возможно, это не совсем правильно и не подчиняется PEP8, но для классов здесь не используется docstring.
<br> Вместо этого используется конструкция `# --- Описание/Наименование --- #`.

Внутри класса код следует писать сразу, не пропуская ни одной строчки.

Между атрибутами класса можно пропускать 1 строчку (если найдётся логическое обоснование), а можно не пропускать.
<br> Между методами класса нужно оставлять 1 строчку.

Перед каждым классом нужно иметь 2 пустых строчки.
<br> Конструкция `# --- Описание/Наименование --- #` не считается за пустую строчку.

> Пример оформления классов в моём стиле:
```python
# ... предыдущий код заканчивается на этой строчке ...


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
    created_at: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint(r"email ~* '^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$'", name='email_format'),
        CheckConstraint(r"phone ~ '^\+7\d{10}$'", name='phone_format'),
    )

    job_title: Mapped["JobTitle"] = relationship(back_populates="users")  # N:1 → Несколько рабочих могут иметь одну и ту же должность (но один рабочий может иметь только одну должность)
    rules: Mapped[List["MonitoringRule"]] = relationship(back_populates="user", cascade="all, delete")  # 1:N → Один пользователь может иметь несколько правил
    settings: Mapped["UserSetting"] = relationship(back_populates="user", cascade="all, delete-orphan")  # 1:1 → Одному пользователю соответствуют только одни настройки

    @property
    def job_title_name(self) -> Optional[str]:
        """ Какой-то docstring """
        if self.job_title:
            return self.job_title.job_title_name
        return None

    def __repr__(self):
        """ Какой-то docstring """
        return f"<User(id={self.user_id}, email='{self.email}')>"


# ... остальной код начинается с этой строчки ...
```

<a id="3-функции"></a>
## Функции

Для функций следует использовать docstring.
<br> О стиле docstring и других комментариев будет рассказано [ниже](#4-комментарии).

Внутри каждой функции при написании кода следует пропускать 1 строчку до и после конструкций: 
- `if ... else`; 
- `try ... except ... finally`; 
- а также циклов `for` и `while`.

Между переменными можно пропускать 1 строчку, если это логически обосновано.

Можно использовать нумерацию этапов. Об этом тоже будет рассказано [ниже](#4-комментарии). 
<br> Главное здесь придерживаться тех же правил русского языка, что и при docstring. То есть особое внимание на форму глагола (что делает?).

Перед return можно не пропускать 1 строчку.

Перед каждой функцией нужно иметь 2 пустые строчки.

> Пример оформления функций в моём стиле:
```python
# ... предыдущий код заканчивается на этой строчке ...


def get_all_parameter_types(*, db: Session, skip: int = 0, limit: int = 100) -> List[ParameterType]:
    """ Получает список всех типов параметров """
    return parameter_type_repository.get_multi(db=db, skip=skip, limit=limit)


def get_parameters_for_actuator(*, db: Session, current_user: User, actuator_id: int, skip: int = 0, limit: int = 100) -> List[Parameter]:
    """ Получает список доступных пользователю параметров для актуатора """
    scope = get_user_access_scope(db=db, user=current_user)

    # 1. Проверяет доступ к актуатору
    if not can_user_access_actuator(db=db, scope=scope, target_actuator_id=actuator_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к параметрам этого актуатора")

    # 2. Получает параметры
    return parameter_repository.get_by_actuator(db=db, actuator_id=actuator_id, skip=skip, limit=limit)


# ... остальной код начинается с этой строчки ...
```

<a id="4-комментарии"></a>
## Различные виды комментариев (docstring, "# ...", "'''...'''")

### docstring

1. **Однострочный** записывается в таком формате: 
<br> `""" Делает то-то, то-то """` 
- Точка в конце не ставится;
- Перед первой буквой первого слова и после последней буквы последнего слова ставятся пробелы;
- Глаголы используются в форме 3 лица, единственного числа, несовершенного вида.

2. **Двухстрочный** записывается в таком формате:
```python
""" Делает то-то, то-то. 
    Требует то-то, то-то. """
```
- Точка в конце каждого предложения ставится; 
- Пробелы по краям текста так же остаются;
- Глаголы используются в той же форме.

docstring записывается сразу после объявления функции, не пропуская ни строчки.
После docstring следует записывать код сразу, не пропуская ни строчки.

> Пример оформления docstring в моём стиле:
```python
def authenticate_user(*, db: Session, username: str, password: str) -> Optional[User]:
    """ Аутентифицирует пользователя по имени пользователя (email или телефон) и паролю.
    Возвращает объект User в случае успеха, иначе None. """
    user = user_repository.get_by_email(db, email=username)
```

### Однострочные комментарии вида "# ..."

Однострочные комментарии вида "# ..." нужны, чтобы пояснить за какую-то одну строку.
<br> Не стоит использовать однострочные комментарии в качестве многострочных. Для этого есть "'''...'''".

Перед самим комментарием следует нажать "пробел" 2 раза.

> Пример оформления однострочных комментариев в моём стиле
```python
    job_title: Mapped["JobTitle"] = relationship(back_populates="users")  # N:1 → Несколько рабочих могут иметь одну и ту же должность (но один рабочий может иметь только одну должность)
```

### Многострочные комментарии вида "'''...'''"

Многострочные комментарии вида "'''...'''" нужны, чтобы визуально отделить один участок кода от другого.

Зачастую мною они используются со знаками "=" в качестве обрамления заголовка.

Сначала идёт открывающее `'''`, затем знаки "=", после этого заголовок, затем опять знаки "=" и закрывающее `'''`.
<br> Перед заголовком нужно пропустить 4 пробела или нажать на TAB.
<br> Перед открывающим `'''` и после закрывающего `'''` нужно иметь 2 пустых строки.

Количество знаков "=" определяется по следующему алгоритму:
- После заголовка отсчитываем 4 пробела;
- Количество знаков "=" должно быть таким, что последний знак "=" не выходит за четвёртый пробел. 
Обычно пробелов выходит 4 штуки после последней буквы.

> Пример оформления многострочных комментариев в моём стиле
```python
# ... предыдущий код заканчивается на этой строчке ...


'''
===================
    Справочники     
===================
'''


# ... остальной код начинается с этой строчки ...
```

<a id="5-переносы"></a>
## Переносы строк

Если это длинный print или import с большим количеством модулей, я не переношу.
<br> Если это какая-то переменная с большим количеством параметров или функция с большим количеством аргументов, я переношу.

<a id="6-логирование"></a>
## Логирование

Всё, что можно написать по-русски, следует записать по-русски.
<br> Всё, что нецелесообразно перевести на русский, следует записать по-английски.

Наименование исполнителя записывается в квадратных скобках.
<br> Если оно состоит из одного слова, то записывается большими буквами.
<br> Если оно состоит из нескольких слов, то записывается через "_".

После наименования нужно нажать пробел 2 раза. Двоеточие перед пробелами не ставится.
<br> Слово "ошибка" записывается большими буквами, а перед ним ставятся три восклицательных знака.

> Пример логирования в моём стиле
```python
print(f"[WORKER]  !!! ОШИБКА при объявлении fanout exchange: '{type(e_declare_exch).__name__}' - '{e_declare_exch}'")
print(f"[SIMULATOR]  Опубликовано в RabbitMQ exchange '{simulator_live_data_exchange.name}': {payload_dict}")
print(f"[FastAPI]  Получил live data через RabbitMQ: {data}")
print(f"[Alert_Service]  Создана тревога с ID = {created_alert.alert_id} для пользователя с ID = {rule.user_id}")
```

<a id="7-коммиты"></a>
## GitHub Commits

Коммиты следует подразделять на виды: 
 - init:; 
 - feat:; 
 - fix:;
 - refactor:; 
 - docs:.

Примеры имён коммитов можно посмотреть [здесь](https://web.archive.org/web/20240111062431/https://docs.rs.school/#/git-convention?id=%d0%9f%d1%80%d0%b8%d0%bc%d0%b5%d1%80%d1%8b-%d0%b8%d0%bc%d0%b5%d0%bd-%d0%ba%d0%be%d0%bc%d0%bc%d0%b8%d1%82%d0%be%d0%b2).

Текст коммитов следует записывать только на английском языке.