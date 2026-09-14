import unittest
from registration import validate, mask


class TestMask(unittest.TestCase):
    def test_normal(self):
        self.assertEqual(mask("Пароль123!"), "П********!")

    def test_short(self):
        self.assertEqual(mask("ab"), "ab")

    def test_one_char(self):
        self.assertEqual(mask("a"), "*")


class TestLogin(unittest.TestCase):
    def test_empty(self):
        result, msg = validate("", "Пароль123!", "Пароль123!")
        self.assertFalse(result)
        self.assertEqual(msg, "Логин не может быть пустым")

    def test_phone(self):
        result, _ = validate("+7-999-123-4567", "Пароль123!", "Пароль123!")
        self.assertTrue(result)

    def test_email(self):
        result, _ = validate("user@mail.ru", "Пароль123!", "Пароль123!")
        self.assertTrue(result)

    def test_string_valid(self):
        result, _ = validate("ivan_ivanov", "Пароль123!", "Пароль123!")
        self.assertTrue(result)

    def test_too_short(self):
        result, msg = validate("ab", "Пароль123!", "Пароль123!")
        self.assertFalse(result)
        self.assertIn("5 символов", msg)

    def test_cyrillic_in_login(self):
        result, msg = validate("ivan тест", "Пароль123!", "Пароль123!")
        self.assertFalse(result)
        self.assertIn("латиницу", msg)

    def test_blacklist(self):
        result, msg = validate("admin", "Пароль123!", "Пароль123!")
        self.assertFalse(result)
        self.assertIn("чёрном списке", msg)


class TestPassword(unittest.TestCase):
    def test_too_short(self):
        result, msg = validate("test123", "short", "short")
        self.assertFalse(result)
        self.assertIn("7 символов", msg)

    def test_no_cyrillic(self):
        result, msg = validate("test123", "password123!", "password123!")
        self.assertFalse(result)
        self.assertIn("кириллическую", msg)

    def test_no_uppercase(self):
        result, msg = validate("test123", "пароль123!", "пароль123!")
        self.assertFalse(result)
        self.assertIn("заглавную", msg)

    def test_no_lowercase(self):
        result, msg = validate("test123", "ПАРОЛЬ123!", "ПАРОЛЬ123!")
        self.assertFalse(result)
        self.assertIn("строчную", msg)

    def test_no_digit(self):
        result, msg = validate("test123", "Парольбезцифр!", "Парольбезцифр!")
        self.assertFalse(result)
        self.assertIn("цифру", msg)

    def test_no_special(self):
        result, msg = validate("test123", "Пароль12345", "Пароль12345")
        self.assertFalse(result)
        self.assertIn("спецсимвол", msg)

    def test_latin_in_password(self):
        result, msg = validate("test123", "Пароль123!", "Пароль123!")
        self.assertTrue(result)


class TestConfirm(unittest.TestCase):
    def test_mismatch(self):
        result, msg = validate("test123", "Пароль123!", "Пароль1234!")
        self.assertFalse(result)
        self.assertIn("не совпадают", msg)

    def test_match(self):
        result, _ = validate("test123", "Пароль123!", "Пароль123!")
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()