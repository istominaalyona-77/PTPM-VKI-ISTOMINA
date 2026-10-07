"""Класс-контроллер (пункт «e» требований ЛР3).

Реализует бизнес-логику сквозного сценария:

1. запрашивает входные данные через класс взаимодействия с пользователем;
2. если записи в БД нет — вычисляет результат валидатором и сохраняет запись;
   если запись есть — берёт результат из БД;
3. отправляет строку-результата сторонней зависимости;
4. возвращает результат выполнения операции.
"""


class Controller:
    """Объединяющий класс с бизнес-логикой сквозного сценария."""

    def __init__(self, validator, database, user_interaction,
                 external_dependency, recipient="admin@example.com"):
        self._validator = validator
        self._database = database
        self._user_interaction = user_interaction
        self._external_dependency = external_dependency
        self._recipient = recipient

    def run(self):
        """Выполняет один полный проход сценария.

        Возвращает кортеж ``(результат: bool, сообщение_об_ошибке: str)``.
        """
        login, password, confirm = self._user_interaction.request_registration_data()

        cached = self._database.get_record(login, password, confirm)
        if cached is None:
            result, message = self._validator.validate(login, password, confirm)
            self._database.add_record(login, password, confirm, result, message)
            taken_from_cache = False
        else:
            result, message = cached
            taken_from_cache = True

        summary = self._build_summary(login, result, message, taken_from_cache)
        self._external_dependency.send(summary, self._recipient)
        return result, message

    @staticmethod
    def _build_summary(login, result, message, taken_from_cache):
        source = "из БД" if taken_from_cache else "вычислено"
        status = "успех" if result else "ошибка"
        text = message if message else "нет"
        return f"Регистрация ({source}): логин={login}, статус={status}, сообщение={text}"
