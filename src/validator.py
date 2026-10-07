"""Класс вычислений / валидации (пункт «a» требований ЛР3).

Класс :class:`RegistrationValidator` инкапсулирует единственный публичный
метод ``validate``, логика которого была реализована в Лабораторной работе
№1 (проверка данных пользователя при регистрации).
"""

import re

BLACKLIST = [
    "admin",
    "user",
    "test",
    "password",
    "qwerty",
    "login",
    "12345",
    "moderator",
]

EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9](?:[A-Za-z0-9._%+-]*[A-Za-z0-9])?"
    r"@(?:[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?\.)+[A-Za-z]{2,}$"
)

PHONE_PATTERN = re.compile(r"^\+\d-\d{3}-\d{3}-\d{4}$")

SPECIAL_CHARS = "!@#$%^&*()-+=[]{}|;:',.<>?/~`"


def _is_valid_email(login):
    """Формат e-mail и отсутствие «двойных точек» в локальной части."""
    if not EMAIL_PATTERN.match(login):
        return False
    local_part = login.split("@", 1)[0]
    return ".." not in local_part


def _check_login(login):
    login = login.strip()
    if not login:
        return False, "Логин не может быть пустым"
    if PHONE_PATTERN.match(login):
        return True, ""
    if _is_valid_email(login):
        return True, ""
    if len(login) < 5:
        return False, "Логин должен содержать минимум 5 символов"
    if not re.match(r"^[a-zA-Z0-9_]+$", login):
        return False, "Логин может содержать только латиницу, цифры и _"
    if login.lower() in BLACKLIST:
        return False, f"Логин '{login}' в чёрном списке"
    return True, ""


def _check_password(password):
    if len(password) < 7:
        return False, "Пароль должен содержать минимум 7 символов"
    if not any("\u0400" <= c <= "\u04ff" for c in password):
        return False, "Пароль должен содержать хотя бы одну кириллическую букву"
    if not any(c.isupper() and "\u0400" <= c <= "\u04ff" for c in password):
        return False, "Пароль должен содержать хотя бы одну заглавную букву"
    if not any(c.islower() and "\u0400" <= c <= "\u04ff" for c in password):
        return False, "Пароль должен содержать хотя бы одну строчную букву"
    if not any(c.isdigit() for c in password):
        return False, "Пароль должен содержать хотя бы одну цифру"
    if not any(c in SPECIAL_CHARS for c in password):
        return False, "Пароль должен содержать хотя бы один спецсимвол"
    for char in password:
        if "\u0400" <= char <= "\u04ff" or char.isdigit() or char in SPECIAL_CHARS:
            continue
        if char.isalpha():
            return False, "Пароль не должен содержать латинские буквы"
        return False, f"Пароль содержит недопустимый символ: '{char}'"
    return True, ""


class RegistrationValidator:
    """Класс вычислений / валидации с единственным публичным методом."""

    def validate(self, login, password, confirm):
        """Проверяет данные регистрации.

        Возвращает кортеж ``(результат: bool, сообщение_об_ошибке: str)``.
        При успешной проверке сообщение пустое.
        """
        ok, message = _check_login(login)
        if not ok:
            return False, message

        ok, message = _check_password(password)
        if not ok:
            return False, message

        if password != confirm:
            return False, "Пароль и подтверждение не совпадают"

        return True, ""
