"""Тесты класса валидации :class:`RegistrationValidator`.

Здесь проверяется контракт класса-обёртки над логикой ЛР1: тип и состав
возвращаемых значений, приоритет проверок и классификация ошибок.
Развёрнутый перебор конкретных значений логина и пароля уже выполнен
в автотестах Лабораторной работы №2 и намеренно не повторяется.
"""

import unittest

from src.validator import RegistrationValidator


class TestRegistrationValidatorContract(unittest.TestCase):
    """Контракт единственного публичного метода validate()."""

    def setUp(self):
        self.validator = RegistrationValidator()

    def test_valid_data_returns_true_and_empty_message(self):
        result = self.validator.validate("ivan_ivanov", "Пароль123!", "Пароль123!")
        self.assertEqual(result, (True, ""))

    def test_invalid_data_returns_false_and_non_empty_message(self):
        result = self.validator.validate("", "Пароль123!", "Пароль123!")
        self.assertFalse(result[0])
        self.assertTrue(result[1])

    def test_method_returns_tuple_of_two_elements(self):
        result = self.validator.validate("ivan_ivanov", "Пароль123!", "Пароль123!")
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], bool)
        self.assertIsInstance(result[1], str)

    def test_login_error_has_priority_over_password_error(self):
        result = self.validator.validate("admin", "плохой", "плохой")
        self.assertIn("чёрном списке", result[1])


class TestRegistrationValidatorErrorClasses(unittest.TestCase):
    """Каждый класс ошибок приводит к отказу с содержательным сообщением."""

    def setUp(self):
        self.validator = RegistrationValidator()

    def test_invalid_login_variants_are_rejected(self):
        for login in ("", "   ", "abcd", "ivan тест", "ivan-ivanov", "admin"):
            with self.subTest(login=login):
                result = self.validator.validate(login, "Пароль123!", "Пароль123!")
                self.assertFalse(result[0])
                self.assertTrue(result[1])

    def test_login_formats_are_accepted(self):
        for login in ("ivan_ivanov", "ivan@mail.ru", "+7-999-123-4567"):
            with self.subTest(login=login):
                result = self.validator.validate(login, "Пароль123!", "Пароль123!")
                self.assertEqual(result, (True, ""))

    def test_invalid_password_variants_are_rejected(self):
        for password in ("Коро1!", "password123!", "пароль123!", "ПАРОЛЬ123!",
                         "Парольбезцифр!", "Пароль12345", "Пароль123a!", "Пароль 123!"):
            with self.subTest(password=password):
                result = self.validator.validate("ivan_ivanov", password, password)
                self.assertFalse(result[0])
                self.assertTrue(result[1])

    def test_mismatched_confirmation_is_rejected(self):
        result = self.validator.validate("ivan_ivanov", "Пароль123!", "Пароль1234!")
        self.assertFalse(result[0])
        self.assertIn("не совпадают", result[1])


if __name__ == "__main__":
    unittest.main()
