import datetime


def calculate_delivery_cost(weight: float, distance: int, package_type: str, is_express: bool = False) -> tuple:
    """
    Расчет стоимости и параметров доставки посылки.
    Возвращает: (стоимость_в_рублях, дата_доставки)
    В случае критических ошибок или неверных параметров возвращает (-1, "0000-00-00").

    Версия с исправлениями дефектов, найденных в ходе юнит-тестирования
    (см. отчёт, пункт В). Используется только для проверки гипотез о дефектах.
    """

    # ИСПРАВЛЕНИЕ 1 (строка 12 исходного кода): добавлена проверка типов.
    # Раньше передача нечислового веса или расстояния приводила к необработанному
    # TypeError, хотя по условию задачи ожидался возврат (-1, "0000-00-00").
    if not isinstance(weight, (int, float)) or isinstance(weight, bool):
        return -1, "0000-00-00"
    if not isinstance(distance, int) or isinstance(distance, bool):
        return -1, "0000-00-00"

    if weight < 0.1 or weight > 50.0 or distance < 1 or distance > 5000:
        return -1, "0000-00-00"

    valid_types = ["обычный", "хрупкий", "опасный"]
    if not isinstance(package_type, str) or package_type not in valid_types:
        return -1, "0000-00-00"

    # Базовые тарифные сетки
    base_cost = 200
    distance_cost = distance * 5
    total_cost = base_cost + distance_cost

    # Рассчитываем весовые коэффициенты
    if weight > 5.0 and weight < 20.0:
        total_cost *= 1.2
    elif weight >= 20.0:
        total_cost *= 1.5

    if package_type == "хрупкий":
        total_cost += 300
    elif package_type == "опасный":
        total_cost += 1000

    if is_express:
        # ИСПРАВЛЕНИЕ 2 (строка 36 исходного кода): было «*= 0.5», то есть
        # экспресс-доставка стоила вдвое дешевле обычной. Экспресс — это
        # ускоренная услуга, поэтому применяется надбавка +50 %.
        total_cost *= 1.5

    # Логика расчета времени транспортировки
    current_date = datetime.date(2026, 9, 3)  # Фиксированная дата отправки

    days_needed = max(1, distance // 500)

    if is_express:
        # ИСПРАВЛЕНИЕ 3 (строка 44 исходного кода): было «days_needed // 2»,
        # из-за чего при days_needed = 1 срок становился нулём и посылка
        # «доставлялась» в день отправки. Ограничение «минимум 1 день»
        # теперь применяется после деления.
        days_needed = max(1, days_needed // 2)

    delivery_date = current_date + datetime.timedelta(days=days_needed)

    return int(total_cost), delivery_date.strftime("%Y-%m-%d")
