"""Тесты класса сторонней зависимости :class:`EmailServerSimulator`."""

import unittest

from src.notifier import EmailServerSimulator, ExternalDependency


class TestExternalDependencyInterface(unittest.TestCase):
    """Абстрактный интерфейс нельзя инстанцировать напрямую."""

    def test_abstract_base_class_cannot_be_instantiated(self):
        with self.assertRaises(TypeError):
            ExternalDependency()

    def test_simulator_implements_external_dependency(self):
        self.assertIsInstance(EmailServerSimulator(), ExternalDependency)

    def test_abstract_method_body_is_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            ExternalDependency.send(EmailServerSimulator(), "текст", "a@example.com")


class TestEmailServerSimulator(unittest.TestCase):
    """Проверка имитации отправки сообщения."""

    def test_send_returns_true(self):
        self.assertTrue(EmailServerSimulator().send("текст", "admin@example.com"))

    def test_send_records_recipient_and_message(self):
        server = EmailServerSimulator()
        server.send("первое", "a@example.com")
        server.send("второе", "b@example.com")
        self.assertEqual(
            server.history,
            [("a@example.com", "первое"), ("b@example.com", "второе")],
        )

    def test_default_host_is_set(self):
        self.assertEqual(EmailServerSimulator().host, "smtp.example.com")

    def test_custom_host_is_kept(self):
        self.assertEqual(EmailServerSimulator("mail.local").host, "mail.local")


if __name__ == "__main__":
    unittest.main()
