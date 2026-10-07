"""Интеграционные тесты сквозного сценария.

В этих тестах РЕАЛЬНЫЕ компоненты (:class:`Controller`,
:class:`RegistrationDatabase` на SQLite и :class:`RegistrationValidator`)
работают совместно, а изолируются только границы системы — пользователь
и внешний сервер — при помощи тестовых заглушек ``unittest.mock.Mock``.
"""

import unittest
from unittest.mock import Mock

from src.controller import Controller
from src.database import RegistrationDatabase
from src.validator import RegistrationValidator

VALID_DATA = ("ivan_ivanov", "Пароль123!", "Пароль123!")
INVALID_DATA = ("admin", "Пароль123!", "Пароль123!")
RECIPIENT = "master@example.com"


class TestControllerDatabaseValidatorIntegration(unittest.TestCase):
    """Связка Controller + Database + Validator на реальном SQLite."""

    def setUp(self):
        self.database = RegistrationDatabase()
        self.validator = RegistrationValidator()

    def tearDown(self):
        self.database.close()

    def _run(self, data):
        """Выполняет один сценарий с заглушками ввода и внешней отправки."""
        user_interaction = Mock()
        user_interaction.request_registration_data.return_value = data
        dependency = Mock()
        controller = Controller(self.validator, self.database,
                                user_interaction, dependency, recipient=RECIPIENT)
        result = controller.run()
        return result, dependency

    def test_valid_registration_is_computed_stored_and_sent(self):
        """Успешные данные: результат вычислен, сохранён в БД и отправлен."""
        result, dependency = self._run(VALID_DATA)
        self.assertEqual(result, (True, ""))
        self.assertEqual(self.database.get_record(*VALID_DATA), (True, ""))
        dependency.send.assert_called_once()
        summary, recipient = dependency.send.call_args[0]
        self.assertEqual(recipient, RECIPIENT)
        self.assertIn("вычислено", summary)

    def test_invalid_registration_is_stored_with_error_message(self):
        """Ошибочные данные: диагноз сохраняется в БД вместе с сообщением."""
        result, dependency = self._run(INVALID_DATA)
        self.assertFalse(result[0])
        self.assertIn("чёрном списке", result[1])
        self.assertEqual(self.database.get_record(*INVALID_DATA), result)
        dependency.send.assert_called_once()

    def test_repeated_run_reads_result_from_database_not_validator(self):
        """Повторные данные берутся из БД, а не пересчитываются.

        В БД заранее кладётся результат, который валидатор для этих данных
        выдать не может. Если сценарий возвращает именно его — значит,
        результат действительно взят из базы, а валидатор не вызывался.
        """
        self.database.add_record(*VALID_DATA, False, "предзаполненная запись БД")
        result, dependency = self._run(VALID_DATA)
        self.assertEqual(result, (False, "предзаполненная запись БД"))
        dependency.send.assert_called_once()
        summary, _ = dependency.send.call_args[0]
        self.assertIn("из БД", summary)

    def test_deleted_record_is_recomputed_on_next_run(self):
        """После удаления записи сценарий снова считает результат валидатором."""
        self.database.add_record(*VALID_DATA, False, "предзаполненная запись БД")
        self.database.delete_record(*VALID_DATA)
        result, dependency = self._run(VALID_DATA)
        self.assertEqual(result, (True, ""))
        self.assertEqual(self.database.get_record(*VALID_DATA), (True, ""))
        dependency.send.assert_called_once()


class TestControllerDependencyIntegration(unittest.TestCase):
    """Связка Controller + реальный EmailServerSimulator.

    Проверяет, что контроллер доходит до сторонней зависимости и передаёт
    ей осмысленную строку-результат.
    """

    def setUp(self):
        self.database = RegistrationDatabase()
        self.validator = RegistrationValidator()
        from src.notifier import EmailServerSimulator
        self.dependency = EmailServerSimulator()

    def tearDown(self):
        self.database.close()

    def test_controller_delivers_summary_to_email_simulator(self):
        user_interaction = Mock()
        user_interaction.request_registration_data.return_value = VALID_DATA
        controller = Controller(self.validator, self.database,
                                user_interaction, self.dependency,
                                recipient=RECIPIENT)
        controller.run()
        self.assertEqual(len(self.dependency.history), 1)
        recipient, summary = self.dependency.history[0]
        self.assertEqual(recipient, RECIPIENT)
        self.assertIn("ivan_ivanov", summary)
        self.assertIn("успех", summary)


if __name__ == "__main__":
    unittest.main()
