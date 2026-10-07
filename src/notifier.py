"""Класс сторонней зависимости (пункт «d» требований ЛР3).

Абстрактный базовый класс :class:`ExternalDependency` (модуль ``abc``)
выступает в роли интерфейса передачи данных стороннему процессу.
:class:`EmailServerSimulator` реализует исключительно имитацию отправки
на внешний email-сервер и реальных сетевых вызовов не выполняет.
"""

from abc import ABC, abstractmethod


class ExternalDependency(ABC):
    """Интерфейс взаимодействия со сторонней зависимостью."""

    @abstractmethod
    def send(self, message, recipient):
        """Передаёт строку ``message`` получателю ``recipient``."""
        raise NotImplementedError


class EmailServerSimulator(ExternalDependency):
    """Имитация отправки сообщения на внешний email-сервер."""

    def __init__(self, host="smtp.example.com"):
        self.host = host
        self.history = []

    def send(self, message, recipient):
        self.history.append((recipient, message))
        return True
