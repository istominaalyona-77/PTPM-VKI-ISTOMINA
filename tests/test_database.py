"""Тесты репозитория :class:`DatabaseRepository`.

Для каждого из пяти методов (``add``, ``get_by_id``, ``get_by_name``,
``update``, ``delete``) проверяются как успешные сценарии, так и ошибочные.
"""

import os
import tempfile
import unittest

from src.database import (
    MAX_MESSAGE_LENGTH,
    MAX_NAME_LENGTH,
    CommentNotFoundError,
    DatabaseRepository,
    DuplicateCommentError,
    ValidationError,
)

LONG_NAME = "a" * MAX_NAME_LENGTH
TOO_LONG_NAME = "a" * (MAX_NAME_LENGTH + 1)
LONG_MESSAGE = "b" * MAX_MESSAGE_LENGTH
TOO_LONG_MESSAGE = "b" * (MAX_MESSAGE_LENGTH + 1)


class RepositoryTestCase(unittest.TestCase):
    """Перед каждым тестом создаётся чистая база в памяти."""

    def setUp(self):
        self.repository = DatabaseRepository(":memory:")

    def tearDown(self):
        self.repository.close()


class TestAdd(RepositoryTestCase):
    def test_add_new_comment_returns_true_and_stores_record(self):
        self.assertTrue(self.repository.add(1, "alice", "<p>Привет</p>"))
        self.assertEqual(
            self.repository.get_by_id(1),
            {"id": 1, "name": "alice", "message": "<p>Привет</p>"},
        )

    def test_add_duplicate_id_raises_exception(self):
        self.repository.add(1, "alice", "первое сообщение")
        with self.assertRaises(DuplicateCommentError):
            self.repository.add(1, "bob", "второе сообщение")
        self.assertEqual(self.repository.get_by_id(1)["name"], "alice")

    def test_add_accepts_values_of_maximum_length(self):
        self.assertTrue(self.repository.add(2, LONG_NAME, LONG_MESSAGE))
        record = self.repository.get_by_id(2)
        self.assertEqual(len(record["name"]), MAX_NAME_LENGTH)
        self.assertEqual(len(record["message"]), MAX_MESSAGE_LENGTH)

    def test_add_rejects_too_long_name(self):
        with self.assertRaises(ValidationError):
            self.repository.add(3, TOO_LONG_NAME, "текст")
        self.assertIsNone(self.repository.get_by_id(3))

    def test_add_rejects_too_long_message(self):
        with self.assertRaises(ValidationError):
            self.repository.add(4, "alice", TOO_LONG_MESSAGE)
        self.assertIsNone(self.repository.get_by_id(4))

    def test_add_rejects_wrong_types(self):
        with self.assertRaises(ValidationError):
            self.repository.add("5", "alice", "текст")
        with self.assertRaises(ValidationError):
            self.repository.add(5, 123, "текст")
        with self.assertRaises(ValidationError):
            self.repository.add(5, "alice", None)
        with self.assertRaises(ValidationError):
            self.repository.add(True, "alice", "текст")

    def test_add_rejects_empty_name_and_message(self):
        with self.assertRaises(ValidationError):
            self.repository.add(6, "   ", "текст")
        with self.assertRaises(ValidationError):
            self.repository.add(6, "alice", "   ")

    def test_add_rejects_non_positive_id(self):
        for comment_id in (0, -1):
            with self.subTest(comment_id=comment_id):
                with self.assertRaises(ValidationError):
                    self.repository.add(comment_id, "alice", "текст")


class TestGetById(RepositoryTestCase):
    def test_get_by_id_returns_existing_record(self):
        self.repository.add(10, "carol", "<span>текст</span>")
        self.assertEqual(
            self.repository.get_by_id(10),
            {"id": 10, "name": "carol", "message": "<span>текст</span>"},
        )

    def test_get_by_id_returns_none_for_missing_record(self):
        self.assertIsNone(self.repository.get_by_id(999))

    def test_get_by_id_rejects_wrong_type(self):
        with self.assertRaises(ValidationError):
            self.repository.get_by_id("10")


class TestGetByName(RepositoryTestCase):
    def test_get_by_name_returns_all_user_comments(self):
        self.repository.add(1, "alice", "первое")
        self.repository.add(2, "bob", "чужое")
        self.repository.add(3, "alice", "второе")

        comments = self.repository.get_by_name("alice")

        self.assertEqual([comment["id"] for comment in comments], [1, 3])
        self.assertEqual({comment["name"] for comment in comments}, {"alice"})

    def test_get_by_name_returns_empty_list_for_unknown_user(self):
        self.repository.add(1, "alice", "текст")
        self.assertEqual(self.repository.get_by_name("nobody"), [])

    def test_get_by_name_rejects_wrong_type(self):
        with self.assertRaises(ValidationError):
            self.repository.get_by_name(42)


class TestUpdate(RepositoryTestCase):
    def test_update_existing_comment_changes_message(self):
        self.repository.add(1, "alice", "старый текст")
        self.assertTrue(self.repository.update(1, "новый текст"))
        self.assertEqual(self.repository.get_by_id(1)["message"], "новый текст")

    def test_update_missing_id_raises_exception(self):
        with self.assertRaises(CommentNotFoundError):
            self.repository.update(999, "новый текст")

    def test_update_rejects_too_long_message_and_keeps_old_value(self):
        self.repository.add(1, "alice", "старый текст")
        with self.assertRaises(ValidationError):
            self.repository.update(1, TOO_LONG_MESSAGE)
        self.assertEqual(self.repository.get_by_id(1)["message"], "старый текст")

    def test_update_rejects_wrong_types(self):
        self.repository.add(1, "alice", "текст")
        with self.assertRaises(ValidationError):
            self.repository.update("1", "новый текст")
        with self.assertRaises(ValidationError):
            self.repository.update(1, 12345)


class TestDelete(RepositoryTestCase):
    def test_delete_existing_comment_returns_true_and_removes_it(self):
        self.repository.add(1, "alice", "текст")
        self.assertTrue(self.repository.delete(1))
        self.assertIsNone(self.repository.get_by_id(1))

    def test_delete_missing_comment_returns_false(self):
        self.assertFalse(self.repository.delete(999))

    def test_delete_is_not_repeatable(self):
        self.repository.add(1, "alice", "текст")
        self.assertTrue(self.repository.delete(1))
        self.assertFalse(self.repository.delete(1))

    def test_delete_rejects_wrong_type(self):
        with self.assertRaises(ValidationError):
            self.repository.delete(None)


class TestRepositorySetup(unittest.TestCase):
    def test_default_database_is_in_memory(self):
        repository = DatabaseRepository()
        try:
            self.assertEqual(repository.db_path, ":memory:")
        finally:
            repository.close()

    def test_invalid_db_path_is_rejected(self):
        with self.assertRaises(ValidationError):
            DatabaseRepository(123)
        with self.assertRaises(ValidationError):
            DatabaseRepository("   ")

    def test_comments_survive_reopening_file_database(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "forum.db")

            repository = DatabaseRepository(db_path)
            repository.add(1, "alice", "текст")
            repository.close()

            repository = DatabaseRepository(db_path)
            try:
                self.assertEqual(
                    repository.get_by_id(1),
                    {"id": 1, "name": "alice", "message": "текст"},
                )
            finally:
                repository.close()


if __name__ == "__main__":
    unittest.main()
