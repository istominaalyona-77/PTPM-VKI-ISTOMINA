"""Тесты класса взаимодействия с пользователем :class:`ConsoleUserInteraction`.

Пользовательский ввод изолируется тестовой заглушкой: функция ``input``
подменяется через :func:`unittest.mock.patch`.
"""

import unittest
from unittest.mock import patch

from src.user_io import ConsoleUserInteraction, UserInteraction


class TestUserInteractionInterface(unittest.TestCase):
    """Абстрактный интерфейс нельзя инстанцировать напрямую."""

    def test_abstract_base_class_cannot_be_instantiated(self):
        with self.assertRaises(TypeError):
            UserInteraction()

    def test_console_implementation_is_a_user_interaction(self):
        self.assertIsInstance(ConsoleUserInteraction(), UserInteraction)

    def test_abstract_method_body_is_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            UserInteraction.request_registration_data(ConsoleUserInteraction())


class TestConsoleUserInteraction(unittest.TestCase):
    """Проверка получения данных из консоли с заменой input()."""

    @patch("builtins.input", side_effect=["ivan_ivanov", "Пароль123!", "Пароль123!"])
    def test_returns_login_password_and_confirmation(self, mock_input):
        interaction = ConsoleUserInteraction()
        self.assertEqual(
            interaction.request_registration_data(),
            ("ivan_ivanov", "Пароль123!", "Пароль123!"),
        )
        self.assertEqual(mock_input.call_count, 3)

    @patch("builtins.input", side_effect=["", "", ""])
    def test_empty_input_is_returned_unchanged(self, mock_input):
        interaction = ConsoleUserInteraction()
        self.assertEqual(interaction.request_registration_data(), ("", "", ""))

    @patch("builtins.input", side_effect=["  spaces  ", "Пароль123!", "Пароль123!"])
    def test_console_layer_does_not_modify_input(self, mock_input):
        interaction = ConsoleUserInteraction()
        login, _, _ = interaction.request_registration_data()
        self.assertEqual(login, "  spaces  ")


if __name__ == "__main__":
    unittest.main()
