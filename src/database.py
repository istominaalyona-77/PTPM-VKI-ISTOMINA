"""Модуль 1. Репозиторий для работы с базой данных комментариев.

Данные хранятся во встроенной базе SQLite в таблице ``comments``:

* ``id``      — ``INTEGER PRIMARY KEY``, идентификатор сообщения с форума;
* ``name``    — ``TEXT NOT NULL``, логин автора (не длиннее 256 символов);
* ``message`` — ``TEXT NOT NULL``, текст сообщения с HTML-разметкой
  (не длиннее 8096 символов).

Публичный интерфейс — класс :class:`DatabaseRepository` с пятью методами:
``add``, ``get_by_id``, ``get_by_name``, ``update`` и ``delete``.
"""

import sqlite3

MAX_NAME_LENGTH = 256
MAX_MESSAGE_LENGTH = 8096

CREATE_TABLE_SQL = f"""
    CREATE TABLE IF NOT EXISTS comments (
        id      INTEGER PRIMARY KEY,
        name    TEXT NOT NULL CHECK (length(name) <= {MAX_NAME_LENGTH}),
        message TEXT NOT NULL CHECK (length(message) <= {MAX_MESSAGE_LENGTH})
    )
"""


class RepositoryError(Exception):
    """Базовое исключение репозитория."""


class ValidationError(RepositoryError, ValueError):
    """Переданы данные недопустимого типа или длины."""


class DuplicateCommentError(RepositoryError):
    """Комментарий с таким ``id`` уже существует в базе."""


class CommentNotFoundError(RepositoryError):
    """Комментарий с указанным ``id`` отсутствует в базе."""


def _validate_comment_id(comment_id):
    """Идентификатор должен быть положительным целым числом (не ``bool``)."""
    if isinstance(comment_id, bool) or not isinstance(comment_id, int):
        raise ValidationError(
            f"id должен быть целым числом, получено: {type(comment_id).__name__}"
        )
    if comment_id <= 0:
        raise ValidationError("id должен быть положительным целым числом")
    return comment_id


def _validate_name(username):
    """Логин должен быть непустой строкой не длиннее 256 символов."""
    if not isinstance(username, str):
        raise ValidationError(
            f"name должен быть строкой, получено: {type(username).__name__}"
        )
    name = username.strip()
    if not name:
        raise ValidationError("name не может быть пустым")
    if len(name) > MAX_NAME_LENGTH:
        raise ValidationError(
            f"name не должен превышать {MAX_NAME_LENGTH} символов "
            f"(получено {len(name)})"
        )
    return name


def _validate_message(message):
    """Сообщение должно быть непустой строкой не длиннее 8096 символов."""
    if not isinstance(message, str):
        raise ValidationError(
            f"message должен быть строкой, получено: {type(message).__name__}"
        )
    if not message.strip():
        raise ValidationError("message не может быть пустым")
    if len(message) > MAX_MESSAGE_LENGTH:
        raise ValidationError(
            f"message не должен превышать {MAX_MESSAGE_LENGTH} символов "
            f"(получено {len(message)})"
        )
    return message


class DatabaseRepository:
    """Репозиторий комментариев форума поверх SQLite."""

    def __init__(self, db_path=":memory:"):
        if not isinstance(db_path, str) or not db_path.strip():
            raise ValidationError("Путь к базе данных должен быть непустой строкой")
        self._db_path = db_path
        self._connection = sqlite3.connect(db_path)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute(CREATE_TABLE_SQL)
        self._connection.commit()

    @property
    def db_path(self):
        """Путь к файлу базы данных (или ``:memory:``)."""
        return self._db_path

    def add(self, comment_id, username, message):
        """Добавляет новую запись и возвращает ``True`` при успехе.

        Перед вставкой проверяются типы данных и длины строк.
        При дублировании ``id`` выбрасывается :class:`DuplicateCommentError`.
        """
        comment_id = _validate_comment_id(comment_id)
        name = _validate_name(username)
        text = _validate_message(message)
        try:
            with self._connection:
                self._connection.execute(
                    "INSERT INTO comments (id, name, message) VALUES (?, ?, ?)",
                    (comment_id, name, text),
                )
        except sqlite3.IntegrityError as error:
            raise DuplicateCommentError(
                f"Комментарий с id={comment_id} уже существует"
            ) from error
        return True

    def get_by_id(self, comment_id):
        """Возвращает запись в виде словаря или ``None``, если её нет."""
        comment_id = _validate_comment_id(comment_id)
        row = self._connection.execute(
            "SELECT id, name, message FROM comments WHERE id = ?",
            (comment_id,),
        ).fetchone()
        return dict(row) if row is not None else None

    def get_by_name(self, username):
        """Возвращает список всех записей пользователя ``username``.

        Если записей нет, возвращается пустой список.
        """
        if not isinstance(username, str):
            raise ValidationError(
                f"name должен быть строкой, получено: {type(username).__name__}"
            )
        rows = self._connection.execute(
            "SELECT id, name, message FROM comments WHERE name = ? ORDER BY id",
            (username.strip(),),
        ).fetchall()
        return [dict(row) for row in rows]

    def update(self, comment_id, new_message):
        """Изменяет текст существующего комментария и возвращает ``True``.

        Если запись с таким ``id`` отсутствует, выбрасывается
        :class:`CommentNotFoundError`.
        """
        comment_id = _validate_comment_id(comment_id)
        text = _validate_message(new_message)
        cursor = self._connection.execute(
            "UPDATE comments SET message = ? WHERE id = ?",
            (text, comment_id),
        )
        self._connection.commit()
        if cursor.rowcount == 0:
            raise CommentNotFoundError(
                f"Комментарий с id={comment_id} не найден"
            )
        return True

    def delete(self, comment_id):
        """Удаляет запись по ``id``.

        Возвращает ``True``, если запись существовала, иначе ``False``.
        """
        comment_id = _validate_comment_id(comment_id)
        cursor = self._connection.execute(
            "DELETE FROM comments WHERE id = ?",
            (comment_id,),
        )
        self._connection.commit()
        return cursor.rowcount > 0

    def close(self):
        """Закрывает соединение с базой данных."""
        self._connection.close()
