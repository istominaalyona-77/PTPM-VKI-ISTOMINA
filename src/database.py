"""Класс работы с базой данных (пункт «b» требований ЛР3).

Хранит записи о регистрации в SQLite. Одна запись содержит логин, пароль,
подтверждение пароля, результат авторизации и сообщение об ошибке.
Запись идентифицируется тройкой (логин, пароль, подтверждение пароля).
"""

import sqlite3

CREATE_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS registrations (
        login    TEXT    NOT NULL,
        password TEXT    NOT NULL,
        confirm  TEXT    NOT NULL,
        result   INTEGER NOT NULL,
        message  TEXT    NOT NULL,
        PRIMARY KEY (login, password, confirm)
    )
"""


class RegistrationDatabase:
    """Методы добавления, получения и удаления записей о регистрации."""

    def __init__(self, db_path=":memory:"):
        self._connection = sqlite3.connect(db_path)
        self._connection.execute(CREATE_TABLE_SQL)
        self._connection.commit()

    def add_record(self, login, password, confirm, result, message):
        """Добавляет запись. Повторная вставка с тем же ключом перезаписывает её."""
        self._connection.execute(
            "INSERT OR REPLACE INTO registrations "
            "(login, password, confirm, result, message) VALUES (?, ?, ?, ?, ?)",
            (login, password, confirm, int(bool(result)), message),
        )
        self._connection.commit()

    def get_record(self, login, password, confirm):
        """Возвращает ``(результат, сообщение)`` или ``None``, если записи нет."""
        cursor = self._connection.execute(
            "SELECT result, message FROM registrations "
            "WHERE login = ? AND password = ? AND confirm = ?",
            (login, password, confirm),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return bool(row[0]), row[1]

    def delete_record(self, login, password, confirm):
        """Удаляет запись. Возвращает ``True``, если запись существовала."""
        cursor = self._connection.execute(
            "DELETE FROM registrations "
            "WHERE login = ? AND password = ? AND confirm = ?",
            (login, password, confirm),
        )
        self._connection.commit()
        return cursor.rowcount > 0

    def close(self):
        self._connection.close()
