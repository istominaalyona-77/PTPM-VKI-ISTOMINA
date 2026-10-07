"""Точка входа приложения «Регистрация» (Лабораторная работа №3).

Собирает компоненты и запускает сквозной сценарий контроллера.
"""

from src.controller import Controller
from src.database import RegistrationDatabase
from src.notifier import EmailServerSimulator
from src.user_io import ConsoleUserInteraction
from src.validator import RegistrationValidator


def main():
    controller = Controller(
        validator=RegistrationValidator(),
        database=RegistrationDatabase("registrations.db"),
        user_interaction=ConsoleUserInteraction(),
        external_dependency=EmailServerSimulator(),
        recipient="admin@example.com",
    )
    result, message = controller.run()
    print(f"\nРезультат: {result}")
    print(f"Сообщение: {message or '(нет)'}")


if __name__ == "__main__":
    main()
