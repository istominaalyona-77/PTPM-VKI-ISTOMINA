"""Класс взаимодействия с пользователем (пункт «c» требований ЛР3).

Абстрактный базовый класс :class:`UserInteraction` (модуль ``abc``)
выступает в роли интерфейса получения данных у пользователя.
:class:`ConsoleUserInteraction` читает данные из консоли через ``input()``.
"""

from abc import ABC, abstractmethod


class UserInteraction(ABC):
    """Интерфейс взаимодействия с пользователем."""

    @abstractmethod
    def request_registration_data(self):
        """Возвращает кортеж ``(логин, пароль, подтверждение пароля)``."""
        raise NotImplementedError


class ConsoleUserInteraction(UserInteraction):
    """Получение данных через консоль с помощью ``input()``."""

    def request_registration_data(self):
        login = input("Логин: ")
        password = input("Пароль: ")
        confirm = input("Подтверждение пароля: ")
        return login, password, confirm
