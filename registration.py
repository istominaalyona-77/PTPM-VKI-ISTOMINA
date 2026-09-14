import re
import logging
import sys

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | [%(levelname)-7s] | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/file_txt.log", encoding="utf-8"),
    ],
)

logging.info("Логгер успешно сконфигурирован")
logging.info("Приложение запущено")


BLACKLIST = ["admin", "user", "test", "password", "qwerty", "login", "12345", "moderator"]


def mask(password):
    return password[0] + "*" * (len(password) - 2) + password[-1] if len(password) >= 2 else "*"


def check_login(login):
    login = login.strip()
    if not login:
        return False, "Логин не может быть пустым"
    if re.match(r"^\+\d-\d{3}-\d{3}-\d{4}$", login):
        return True, ""
    if re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", login):
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
    if not any(c in "!@#$%^&*()-+=[]{}|;:',.<>?/~`" for c in password):
        return False, "Пароль должен содержать хотя бы один спецсимвол"
    if any(c.isalpha() and not ('\u0400' <= c <= '\u04FF') for c in password):
        return False, "Пароль не должен содержать латинские буквы"
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
        result, message =  validate(login, password, confirm)
        print(f"\nРезультат: {result}")
        if message:
            print(f"Сообщение: {message}")
        logging.info(f"Результат: {result}, сообщение: {message or '(пусто)'}")
    except Exception:
        logging.exception("Непредвиденная ошибка:")
        print("\nРезультат: False\nСообщение: Внутренняя ошибка")