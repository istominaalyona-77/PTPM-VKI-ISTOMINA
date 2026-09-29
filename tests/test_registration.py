import unittest

from registration import mask, check_login, check_password, validate, BLACKLIST


class TestMaskPassword(unittest.TestCase):
    """Проверка маскирования паролей."""

    def test_mask_hides_middle_characters(self):
        self.assertEqual(mask("Пароль123!"), "П********!")

    def test_mask_of_two_characters_does_not_reveal_password(self):
        self.assertEqual(mask("ab"), "**")

    def test_mask_of_single_character_is_hidden(self):
        self.assertEqual(mask("a"), "*")

    def test_mask_of_three_characters_keeps_borders_only(self):
        self.assertEqual(mask("abc"), "a*c")

    def test_mask_of_empty_string_stays_empty(self):
        self.assertEqual(mask(""), "")

    def test_mask_never_equals_original_password(self):
        for password in ("a", "ab", "abc", "Пароль", "Пароль123!"):
            self.assertNotEqual(mask(password), password)

    def test_mask_is_deterministic_for_equal_passwords(self):
        self.assertEqual(mask("Пароль123!"), mask("Пароль123!"))

    def test_mask_differs_for_different_passwords(self):
        self.assertNotEqual(mask("Пароль123!"), mask("Пароль1234!"))


class TestCheckLoginEmpty(unittest.TestCase):
    """Проверка обработки пустого логина."""

    def test_empty_login_is_rejected(self):
        ok, msg = check_login("")
        self.assertFalse(ok)
        self.assertEqual(msg, "Логин не может быть пустым")

    def test_whitespace_only_login_is_rejected(self):
        ok, msg = check_login("     ")
        self.assertFalse(ok)
        self.assertEqual(msg, "Логин не может быть пустым")

    def test_login_with_surrounding_spaces_is_trimmed(self):
        ok, _ = check_login("  ivan_ivanov  ")
        self.assertTrue(ok)


class TestCheckLoginPhone(unittest.TestCase):
    """Проверка валидации логина в формате телефона."""

    def test_valid_phone_is_accepted(self):
        ok, msg = check_login("+7-999-123-4567")
        self.assertTrue(ok)
        self.assertEqual(msg, "")

    def test_phone_without_separators_is_rejected(self):
        ok, _ = check_login("+79991234567")
        self.assertFalse(ok)

    def test_phone_with_too_few_digits_is_rejected(self):
        ok, _ = check_login("+7-999-123-456")
        self.assertFalse(ok)

    def test_phone_with_letters_is_rejected(self):
        ok, _ = check_login("+7-abc-123-4567")
        self.assertFalse(ok)


class TestCheckLoginEmail(unittest.TestCase):
    """Проверка валидации логина в формате email."""

    def test_valid_email_is_accepted(self):
        ok, msg = check_login("ivan@mail.ru")
        self.assertTrue(ok)
        self.assertEqual(msg, "")

    def test_email_with_subdomain_is_accepted(self):
        ok, _ = check_login("ivan.petrov@shop.mail.ru")
        self.assertTrue(ok)

    def test_email_with_domain_without_dot_is_rejected(self):
        ok, _ = check_login("ivan@mail")
        self.assertFalse(ok)

    def test_email_with_empty_host_part_is_rejected(self):
        ok, _ = check_login("ivan@.ru")
        self.assertFalse(ok)

    def test_email_with_double_dot_in_local_part_is_rejected(self):
        ok, _ = check_login("ivan..petrov@mail.ru")
        self.assertFalse(ok)

    def test_email_with_trailing_dot_is_rejected(self):
        ok, _ = check_login("ivan@mail.ru.")
        self.assertFalse(ok)

    def test_email_without_at_sign_is_rejected(self):
        ok, _ = check_login("ivan.mail.ru")
        self.assertFalse(ok)


class TestCheckLoginString(unittest.TestCase):
    """Проверка валидации логина-строки."""

    def test_valid_string_login_is_accepted(self):
        ok, msg = check_login("ivan_ivanov")
        self.assertTrue(ok)
        self.assertEqual(msg, "")

    def test_login_of_exactly_five_characters_is_accepted(self):
        ok, _ = check_login("abcde")
        self.assertTrue(ok)

    def test_login_of_four_characters_is_rejected(self):
        ok, msg = check_login("abcd")
        self.assertFalse(ok)
        self.assertIn("5 символов", msg)

    def test_login_with_cyrillic_is_rejected(self):
        ok, msg = check_login("ivan тест")
        self.assertFalse(ok)
        self.assertIn("латиницу", msg)

    def test_login_with_hyphen_is_rejected(self):
        ok, msg = check_login("ivan-ivanov")
        self.assertFalse(ok)
        self.assertIn("латиницу", msg)

    def test_numeric_login_not_in_blacklist_is_accepted(self):
        ok, _ = check_login("123456")
        self.assertTrue(ok)

    def test_blacklisted_login_is_rejected(self):
        ok, msg = check_login("admin")
        self.assertFalse(ok)
        self.assertIn("чёрном списке", msg)

    def test_blacklisted_login_is_rejected_case_insensitively(self):
        for login in ("ADMIN", "Admin", "aDmIn"):
            ok, msg = check_login(login)
            self.assertFalse(ok, f"Логин {login} должен отклоняться")
            self.assertIn("чёрном списке", msg)

    def test_every_blacklist_entry_is_actually_blocked(self):
        for login in BLACKLIST:
            ok, _ = check_login(login)
            self.assertFalse(ok, f"Логин {login} из чёрного списка не заблокирован")


class TestCheckPasswordLength(unittest.TestCase):
    """Проверка требований к длине пароля."""

    def test_password_shorter_than_seven_is_rejected(self):
        ok, msg = check_password("Коро1!")
        self.assertFalse(ok)
        self.assertIn("7 символов", msg)

    def test_empty_password_is_rejected(self):
        ok, _ = check_password("")
        self.assertFalse(ok)

    def test_password_of_exactly_seven_characters_is_accepted(self):
        ok, msg = check_password("Пароль1!")
        self.assertTrue(ok)
        self.assertEqual(msg, "")


class TestCheckPasswordComposition(unittest.TestCase):
    """Проверка состава символов пароля."""

    def test_valid_password_is_accepted(self):
        ok, msg = check_password("Пароль123!")
        self.assertTrue(ok)
        self.assertEqual(msg, "")

    def test_password_without_cyrillic_is_rejected(self):
        ok, msg = check_password("password123!")
        self.assertFalse(ok)
        self.assertIn("кириллическую", msg)

    def test_password_without_uppercase_letter_is_rejected(self):
        ok, msg = check_password("пароль123!")
        self.assertFalse(ok)
        self.assertIn("заглавную", msg)

    def test_password_without_lowercase_letter_is_rejected(self):
        ok, msg = check_password("ПАРОЛЬ123!")
        self.assertFalse(ok)
        self.assertIn("строчную", msg)

    def test_password_without_digit_is_rejected(self):
        ok, msg = check_password("Парольбезцифр!")
        self.assertFalse(ok)
        self.assertIn("цифру", msg)

    def test_password_without_special_character_is_rejected(self):
        ok, msg = check_password("Пароль12345")
        self.assertFalse(ok)
        self.assertIn("спецсимвол", msg)

    def test_password_with_latin_letters_is_rejected(self):
        ok, msg = check_password("Пароль123a!")
        self.assertFalse(ok)
        self.assertIn("латинские буквы", msg)

    def test_password_with_space_is_rejected(self):
        ok, _ = check_password("Пароль 123!")
        self.assertFalse(ok)


class TestValidateRegistration(unittest.TestCase):
    """Проверка сценариев регистрации целиком."""

    def test_successful_registration_returns_true_and_empty_message(self):
        result, message = validate("ivan_ivanov", "Пароль123!", "Пароль123!")
        self.assertTrue(result)
        self.assertEqual(message, "")

    def test_registration_via_phone_succeeds(self):
        result, _ = validate("+7-999-123-4567", "Пароль123!", "Пароль123!")
        self.assertTrue(result)

    def test_registration_via_email_succeeds(self):
        result, _ = validate("ivan@mail.ru", "Пароль123!", "Пароль123!")
        self.assertTrue(result)

    def test_mismatched_confirmation_is_rejected(self):
        result, msg = validate("ivan_ivanov", "Пароль123!", "Пароль1234!")
        self.assertFalse(result)
        self.assertIn("не совпадают", msg)

    def test_empty_confirmation_is_rejected(self):
        result, msg = validate("ivan_ivanov", "Пароль123!", "")
        self.assertFalse(result)
        self.assertIn("не совпадают", msg)

    def test_login_error_is_reported_before_password_check(self):
        result, msg = validate("admin", "short", "short")
        self.assertFalse(result)
        self.assertIn("чёрном списке", msg)

    def test_password_error_is_reported_when_login_is_valid(self):
        result, msg = validate("ivan_ivanov", "short", "short")
        self.assertFalse(result)
        self.assertIn("7 символов", msg)

    def test_failure_message_is_never_empty(self):
        for login, password in [("", "Пароль123!"), ("ab", "Пароль123!"),
                                ("admin", "Пароль123!"), ("ivan_ivanov", "short")]:
            with self.subTest(login=login, password=password):
                result, message = validate(login, password, password)
                self.assertFalse(result)
                self.assertTrue(message, "При ошибке сообщение не должно быть пустым")


if __name__ == "__main__":
    unittest.main()
