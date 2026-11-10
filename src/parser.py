"""Модуль 2. Веб-парсер сообщений форума.

Класс :class:`ForumParser`:

1. скачивает HTML-страницу через ``requests`` с обязательным заголовком
   ``User-Agent`` (чтобы сайт не блокировал автоматический запрос);
2. разбирает страницу через ``BeautifulSoup`` и извлекает ID сообщения,
   логин автора и текст сообщения (с сохранением внутренней HTML-разметки);
3. сохраняет собранные записи в базу через :class:`src.database.DatabaseRepository`.
"""

import re

import requests
from bs4 import BeautifulSoup

from .database import DuplicateCommentError

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

DEFAULT_HEADERS = {
    "User-Agent": DEFAULT_USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
}

# Контейнеры сообщений на страницах разных форумов.
POST_SELECTOR = (
    "div.post, article.post, "
    "div[data-comment-id], article[data-comment-id]"
)
AUTHOR_SELECTOR = ".post__author, .author, .username, [data-author]"
MESSAGE_SELECTOR = ".post__message, .message, .post-body, .content"

# Атрибуты, в которых может лежать ID сообщения.
COMMENT_ID_ATTRIBUTES = ("data-comment-id", "data-id", "data-post-id")
# Префиксы значения атрибута id="...".
ELEMENT_ID_PREFIXES = ("post-", "comment-", "message-")
# Ссылки вида "#comment-105", "/post/105" и т.п.
LINK_ID_PATTERN = re.compile(r"(?:#|/)(?:comment|post|message)[-/_]?(\d+)/?$")

RECORD_FIELDS = ("id", "name", "message")


class ParserError(Exception):
    """Ошибка загрузки или разбора HTML-страницы."""


class ForumParser:
    """Парсер сообщений со страниц форумов."""

    def __init__(self, headers=None, timeout=10):
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)):
            raise ValueError("timeout должен быть числом")
        if timeout <= 0:
            raise ValueError("timeout должен быть положительным")

        self._headers = dict(DEFAULT_HEADERS)
        if headers is not None:
            if not isinstance(headers, dict):
                raise ValueError("headers должен быть словарём")
            self._headers.update(headers)
        self._timeout = timeout

    @property
    def headers(self):
        """Копия заголовков, которые отправляются вместе с запросом."""
        return dict(self._headers)

    @property
    def timeout(self):
        """Таймаут HTTP-запроса в секундах."""
        return self._timeout

    def fetch_page(self, url):
        """Скачивает HTML-страницу и возвращает её текст.

        Любая сетевая ошибка или ошибочный HTTP-статус превращаются
        в :class:`ParserError`.
        """
        if not isinstance(url, str) or not url.strip():
            raise ParserError("URL должен быть непустой строкой")
        try:
            response = requests.get(
                url,
                headers=self._headers,
                timeout=self._timeout,
            )
            response.raise_for_status()
        except requests.RequestException as error:
            raise ParserError(
                f"Не удалось загрузить страницу {url}: {error}"
            ) from error
        return response.text

    def parse_page(self, url):
        """Скачивает страницу по ``url`` и возвращает список сообщений."""
        return self.parse_html(self.fetch_page(url))

    def parse_html(self, html):
        """Разбирает HTML-код и возвращает список сообщений.

        Каждое сообщение — словарь ``{"id": int, "name": str, "message": str}``.
        Блоки без ID, автора или текста пропускаются; при повторном ID
        сохраняется только первое сообщение.
        """
        if not isinstance(html, str) or not html.strip():
            raise ParserError("HTML-страница пуста")

        soup = BeautifulSoup(html, "lxml")
        comments = []
        seen_ids = set()

        for post in soup.select(POST_SELECTOR):
            comment_id = self._extract_id(post)
            if comment_id is None or comment_id in seen_ids:
                continue

            name = self._extract_author(post)
            message = self._extract_message(post)
            if name is None or message is None:
                continue

            seen_ids.add(comment_id)
            comments.append(
                {"id": comment_id, "name": name, "message": message}
            )

        return comments

    def save_to_db(self, parsed_data, repository):
        """Сохраняет разобранные сообщения в базу данных.

        Новые записи добавляются через ``repository.add``, уже существующие
        обновляются через ``repository.update`` (повторный парсинг не создаёт
        дубликатов). Возвращает количество обработанных записей.
        """
        if not isinstance(parsed_data, (list, tuple)):
            raise ParserError("parsed_data должен быть списком словарей")
        if repository is None or not hasattr(repository, "add"):
            raise ParserError(
                "repository должен реализовывать интерфейс DatabaseRepository"
            )

        saved = 0
        for record in parsed_data:
            comment_id, name, message = self._validate_record(record)
            try:
                repository.add(comment_id, name, message)
            except DuplicateCommentError:
                repository.update(comment_id, message)
            saved += 1
        return saved

    @staticmethod
    def _validate_record(record):
        """Проверяет структуру одной записи перед сохранением."""
        if not isinstance(record, dict):
            raise ParserError("Каждая запись должна быть словарём")
        missing = [field for field in RECORD_FIELDS if field not in record]
        if missing:
            raise ParserError(
                f"В записи отсутствуют поля: {', '.join(missing)}"
            )

        comment_id = record["id"]
        name = record["name"]
        message = record["message"]

        if isinstance(comment_id, bool) or not isinstance(comment_id, int):
            raise ParserError("Поле id должно быть целым числом")
        if not isinstance(name, str) or not name.strip():
            raise ParserError("Поле name должно быть непустой строкой")
        if not isinstance(message, str) or not message.strip():
            raise ParserError("Поле message должно быть непустой строкой")

        return comment_id, name.strip(), message

    @staticmethod
    def _extract_id(post):
        """Ищет ID сообщения в атрибутах элемента или в ссылках."""
        for attribute in COMMENT_ID_ATTRIBUTES:
            value = post.get(attribute)
            if value is not None and str(value).strip().isdigit():
                return int(str(value).strip())

        element_id = post.get("id") or ""
        for prefix in ELEMENT_ID_PREFIXES:
            suffix = element_id[len(prefix):] if element_id.startswith(prefix) else ""
            if suffix.isdigit():
                return int(suffix)

        for link in post.find_all("a", href=True):
            match = LINK_ID_PATTERN.search(link["href"])
            if match:
                return int(match.group(1))

        return None

    @staticmethod
    def _extract_author(post):
        """Извлекает логин автора сообщения."""
        node = post.select_one(AUTHOR_SELECTOR)
        if node is None:
            return None
        name = node.get("data-author") or node.get_text(strip=True)
        name = " ".join(str(name).split())
        return name or None

    @staticmethod
    def _extract_message(post):
        """Извлекает текст сообщения с сохранением внутренней разметки."""
        node = post.select_one(MESSAGE_SELECTOR)
        if node is None:
            return None
        message = node.decode_contents().strip()
        return message or None
