from sqlalchemy.orm import Session
from app.models.parameter import ParameterData  # noqa F401
from app.models.rule import MonitoringRule  # noqa F401
from app.repositories.parameter_repository import parameter_data_repository
from app.repositories.rule_repository import rule_repository, alert_repository
from app.schemas.rule import AlertCreateInternal


# --- Сервис уведомлений (заглушка) ---
# TODO: Убрать заглушку. Возможно, эта функция будет асинхронной.
def _send_notification(user_id: int, message: str):
    """ Отправляет уведомление пользователю (заглушка) """
    print(f"--- УВЕДОМЛЕНИЕ ДЛЯ User {user_id} ---")
    print(message)
    print(f"--------------------------------------")


# --- Основная логика обработки новых данных ---
def process_new_parameter_data(*, db: Session, parameter_data_id: int) -> None:
    """ Обрабатывает новую запись данных параметра: проверяет правила и создает тревоги.
    Эта функция вызывается фоновым воркером (alert_worker.py). """
    print(f"[AlertService] Обработка ParameterData ID: {parameter_data_id}")

    # 1. Получает запись ParameterData с предзагруженными деталями
    data_entry = parameter_data_repository.get_by_data_id_with_details(
        db=db, parameter_data_id=parameter_data_id
    )

    if not data_entry:
        print(f"[AlertService] Ошибка: Запись ParameterData с id={parameter_data_id} не найдена.")
        return
    if not data_entry.parameter:
        print(f"[AlertService] Ошибка: Связанный Parameter для ParameterData id={parameter_data_id} не найден.")
        return

    # 2. Получает активные правила для этого параметра
    active_rules = rule_repository.get_active_by_parameter(
        db=db, parameter_id=data_entry.parameter_id
    )

    if not active_rules:
        print(f"[AlertService] Нет активных правил для parameter_id: {data_entry.parameter_id}")
        return

    value_to_check = data_entry.parameter_value
    alerts_created_this_run = []

    # 3. Проверяет каждое активное правило
    for rule in active_rules:
        threshold = rule.threshold
        operator = rule.comparison_operator
        rule_violated = False

        if operator == '>' and value_to_check > threshold:
            rule_violated = True
        elif operator == '<' and value_to_check < threshold:
            rule_violated = True
        elif operator == '=' and value_to_check == threshold:
            rule_violated = True
        elif operator == '>=' and value_to_check >= threshold:
            rule_violated = True
        elif operator == '<=' and value_to_check <= threshold:
            rule_violated = True

        if rule_violated:
            print(f"[AlertService] Правило ID {rule.rule_id} НАРУШЕНО для ParameterData ID {parameter_data_id}")
            # --- Формирование сообщения тревоги ---
            try:
                # Использует предзагруженные данные для формирования сообщения
                param = data_entry.parameter
                param_type = param.parameter_type
                actuator = param.actuator
                actuator_type = actuator.actuator_type
                aggregate = actuator.aggregate
                aggregate_type = aggregate.aggregate_type
                line = aggregate.line
                shop = line.shop

                param_name_str = param_type.parameter_type_name if param_type else "N/A"
                unit_str = param_type.parameter_unit or "" if param_type else ""
                act_type_str = actuator_type.actuator_type_name if actuator_type else "N/A"
                agg_type_str = aggregate_type.aggregate_type_name if aggregate_type else "N/A"
                line_type_str = line.line_type.value if line else "N/A"
                shop_name_str = shop.shop_name if shop else "N/A"
                rule_name_str = f"'{rule.rule_name}'" if rule.rule_name else f"(ID: {rule.rule_id})"

                alert_message = (   f"Тревога [{shop_name_str} / {line_type_str} / {agg_type_str} / {act_type_str}]: "
                                    f"Параметр '{param_name_str}' = {value_to_check:.2f} {unit_str} "
                                    f"нарушил правило {rule_name_str} ({operator} {threshold} {unit_str})"
                )[:150]
            except AttributeError as e:
                print(f"[AlertService] Ошибка при формировании сообщения: {e}")
                alert_message = f"Тревога по правилу ID {rule.rule_id}: значение {value_to_check:.2f} {operator} {threshold}"

            # --- Подготовка данных для создания Alert ---
            alert_create_data = AlertCreateInternal(
                rule_id=rule.rule_id,
                parameter_data_id=data_entry.parameter_data_id,
                alert_message=alert_message
            )

            # --- Создание записи Alert ---
            # Использует унаследованный create из AlertRepository
            try:
                created_alert = alert_repository.create(db=db, obj_in=alert_create_data)
                alerts_created_this_run.append({"alert_obj": created_alert, "user_id": rule.user_id})
                print(f"[AlertService] Создана тревога ID {created_alert.alert_id} для пользователя {rule.user_id}")
            except Exception as e_create:
                print(f"[AlertService] Ошибка создания записи Alert для rule_id {rule.rule_id}: {e_create}")
                db.rollback()

    # 4. Отправка уведомлений (ПОСЛЕ всех проверок и создания алертов)
    # Пока отправляет по одному.
    for alert_info in alerts_created_this_run:
        _send_notification(user_id=alert_info["user_id"], message=alert_info["alert_obj"].alert_message)

    print(f"[AlertService] Обработка ParameterData ID: {parameter_data_id} завершена.")