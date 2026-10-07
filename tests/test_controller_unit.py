"""Модульные тесты класса :class:`Controller`.

Все соисполнители (валидатор, БД, ввод, сторонняя зависимость) заменены
тестовыми заглушками :class:`unittest.mock.MagicMock`, поэтому здесь
проверяется исключительно логика ветвления контроллера в изоляции.
"""

import unittest
from unittest.mock import MagicMock

from src.controller import Controller

DATA = ("ivan_ivanov", "Пароль123!", "Пароль123!")
RECIPIENT = "boss@example.com"


class TestControllerUnit(unittest.TestCase):
    """Изолированная проверка ветвления контроллера."""

    def _make_controller(self, cached, validation_result=(True, "")):
        validator = MagicMock()
        validator.validate.return_value = validation_result
        database = MagicMock()
        database.get_record.return_value = cached
        user_interaction = MagicMock()
        user_interaction.request_registration_data.return_value = DATA
        dependency = MagicMock()
        controller = Controller(validator, database, user_interaction,
                                dependency, recipient=RECIPIENT)
        return controller, validator, database, user_interaction, dependency

    def test_asks_user_for_registration_data(self):
        controller, _, _, user_interaction, _ = self._make_controller(None)
        controller.run()
        user_interaction.request_registration_data.assert_called_once_with()

    def test_missing_record_triggers_validation_and_insert(self):
        controller, validator, database, _, _ = self._make_controller(None)
        result = controller.run()
        validator.validate.assert_called_once_with(*DATA)
        database.add_record.assert_called_once_with(*DATA, True, "")
        self.assertEqual(result, (True, ""))

    def test_existing_record_skips_validation_and_insert(self):
        controller, validator, database, _, _ = self._make_controller(
            (False, "сообщение из БД")
        )
        result = controller.run()
        validator.validate.assert_not_called()
        database.add_record.assert_not_called()
        self.assertEqual(result, (False, "сообщение из БД"))

    def test_sends_summary_to_external_dependency(self):
        controller, _, _, _, dependency = self._make_controller(None)
        controller.run()
        dependency.send.assert_called_once()
        summary, recipient = dependency.send.call_args[0]
        self.assertEqual(recipient, RECIPIENT)
        self.assertIn("ivan_ivanov", summary)
        self.assertIn("вычислено", summary)

    def test_summary_marks_result_taken_from_cache(self):
        controller, _, _, _, dependency = self._make_controller((True, ""))
        controller.run()
        summary, _ = dependency.send.call_args[0]
        self.assertIn("из БД", summary)
        self.assertIn("успех", summary)

    def test_summary_marks_error_status_and_empty_message(self):
        controller, _, _, _, dependency = self._make_controller((False, ""))
        controller.run()
        summary, _ = dependency.send.call_args[0]
        self.assertIn("ошибка", summary)
        self.assertIn("сообщение=нет", summary)


if __name__ == "__main__":
    unittest.main()
