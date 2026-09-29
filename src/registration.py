import os
import re
import logging
import sys

# Исправление бага №1: папка logs создавалась только вручную, без неё
# FileHandler выбрасывал FileNotFoundError и программа падала при запуске.
os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | [%(levelname)-7s] | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/file_txt.log", encoding="utf-8"),
    ],
)

BLACKLIST = ["admin", "user", "test", "password", "qwerty", "login", "12345", "moderator"]

# Исправление бага №3: прежнее выражение пропускало невалидные адреса
# («ivan@.ru», «ivan..petrov@mail.ru», «ivan@mail.ru.»), то есть не соответствовало
# стандартному формату email. Новое выражение запрещает ведущие/завершающие
# и двойные точки в локальной части и требует домен второго уровня из букв.
EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9](?:[A-Za-z0-9._%+-]*[A-Za-z0-9])?"
    r"@(?:[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?\.)+[A-Za-z]{2,}$"
)

SPECIAL_CHARS = "!@#$%^&*()-+=[]{}|;:',.<>?/~`"


def is_valid_email(login):
    """Проверка e-mail: формат адреса и отсутствие «двойных точек» в локальной части."""
    if not EMAIL_PATTERN.match(login):
        return False
    local_part = login.split("@", 1)[0]
    return ".." not in local_part


def mask(password):
    # Исправление бага №2: при длине 2 функция возвращала пароль целиком
    # («ab» -> «ab»), полностью раскрывая секрет в логах.
    # Теперь при длине меньше 3 символов выводятся только звёздочки.
    if len(password) < 3:
        return "*" * len(password)
    return password[0] + "*" * (len(password) - 2) + password[-1]


def check_login(login):
    login = login.strip()
    if not login:
        return False, "Логин не может быть пустым"
    if re.match(r"^\+\d-\d{3}-\d{3}-\d{4}$", login):
        return True, ""
    if is_valid_email(login):
        return True, ""
    if len(login) < 5:
        return False, "Логин должен содержать минимум 5 символов"
    if not re.match(r"^[a-zA-Z0-9_]+$", login):
        return False, "Логин может содержать только латиницу, цифры и _"
    if login.lower() in BLACKLIST:
        return False, f"Логин '{login}' в чёрном списке"
    return True, ""


def check_password(password):
    if len(password) < 7:
        return False, "Пароль должен содержать минимум 7 символов"

    if not any('\u0400' <= c <= '\u04FF' for c in password):
        return False, "Пароль должен содержать хотя бы одну кириллическую букву"
    if not any(c.isupper() and '\u0400' <= c <= '\u04FF' for c in password):
        return False, "Пароль должен содержать хотя бы одну заглавную букву"
    if not any(c.islower() and '\u0400' <= c <= '\u04FF' for c in password):
        return False, "Пароль должен содержать хотя бы одну строчную букву"
    if not any(c.isdigit() for c in password):
        return False, "Пароль должен содержать хотя бы одну цифру"
    if not any(c in SPECIAL_CHARS for c in password):
        return False, "Пароль должен содержать хотя бы один спецсимвол"

    # Исправление бага №4: раньше каждый символ проверялся только на отсутствие
    # кириллицы, и «не буква, не цифра, не спецсимвол» (пробел, табуляция) молча
    # проходило валидацию. Теперь разрешённый состав символов проверяется явно.
    for c in password:
        if '\u0400' <= c <= '\u04FF' or c.isdigit() or c in SPECIAL_CHARS:
            continue
        if c.isalpha():
            return False, "Пароль не должен содержать латинские буквы"
        return False, f"Пароль содержит недопустимый символ: '{c}'"

    return True, ""


def validate(login, password, confirm):
    logging.info("Начало валидации")
    logging.debug(f"Логин={login}, Пароль={mask(password)}, Подтверждение={mask(confirm)}")

    ok, msg = check_login(login)
    if not ok:
        logging.warning(msg)
        return False, msg

    ok, msg = check_password(password)
    if not ok:
        logging.warning(msg)
        return False, msg

    if password != confirm:
        logging.warning("Пароли не совпадают")
        return False, "Пароль и подтверждение не совпадают"

    logging.info("Регистрация успешна")
    return True, ""


if __name__ == "__main__":
    print("Регистрация")
    login = input("Логин: ")
    password = input("Пароль: ")
    confirm = input("Подтверждение: ")

    try:
        result, message = validate(login, password, confirm)
        print(f"\nРезультат: {result}")
        if message:
            print(f"Сообщение: {message}")
        logging.info(f"Результат: {result}, сообщение: {message or '(пусто)'}")
    except Exception:
        logging.exception("Непредвиденная ошибка:")
        print("\nРезультат: False\nСообщение: Внутренняя ошибка")
