"""Тесты класса работы с базой данных :class:`RegistrationDatabase`."""

import unittest

from src.database import RegistrationDatabase

DATA = ("ivan_ivanov", "Пароль123!", "Пароль123!")


class TestRegistrationDatabase(unittest.TestCase):
    """Проверка добавления, получения и удаления записей."""

    def setUp(self):
        self.database = RegistrationDatabase()

    def tearDown(self):
        self.database.close()

    def test_added_record_can_be_read_back(self):
        self.database.add_record(*DATA, True, "")
        self.assertEqual(self.database.get_record(*DATA), (True, ""))

    def test_record_with_error_message_is_stored(self):
        self.database.add_record("admin", "Пароль123!", "Пароль123!", False,
                                 "Логин 'admin' в чёрном списке")
        result, message = self.database.get_record("admin", "Пароль123!", "Пароль123!")
        self.assertFalse(result)
        self.assertEqual(message, "Логин 'admin' в чёрном списке")

    def test_get_missing_record_returns_none(self):
        self.assertIsNone(self.database.get_record(*DATA))

    def test_record_is_identified_by_all_three_fields(self):
        self.database.add_record(*DATA, True, "")
        self.assertIsNone(self.database.get_record("ivan_ivanov", "Пароль123!", "другой"))
        self.assertIsNone(self.database.get_record("ivan_ivanov", "Другой123!", "Пароль123!"))
        self.assertIsNone(self.database.get_record("другой_логин", "Пароль123!", "Пароль123!"))

    def test_add_record_with_same_key_overwrites_previous(self):
        self.database.add_record(*DATA, False, "старая ошибка")
        self.database.add_record(*DATA, True, "")
        self.assertEqual(self.database.get_record(*DATA), (True, ""))

    def test_delete_existing_record_returns_true_and_removes_it(self):
        self.database.add_record(*DATA, True, "")
        self.assertTrue(self.database.delete_record(*DATA))
        self.assertIsNone(self.database.get_record(*DATA))

    def test_delete_missing_record_returns_false(self):
        self.assertFalse(self.database.delete_record(*DATA))


if __name__ == "__main__":
    unittest.main()
