"""Командная строка для запуска парсера (Лабораторная работа №5).

Примеры:

    python main.py --fixture
    python main.py --fixture --db demo.db
    python main.py https://forum.example.com/topic/1 --db forum.db
"""

import argparse
from pathlib import Path

from src.database import DatabaseRepository
from src.parser import ForumParser

FIXTURE_PATH = (
    Path(__file__).resolve().parent / "tests" / "fixtures" / "forum_page.html"
)


def build_argument_parser():
    parser = argparse.ArgumentParser(
        description="Парсер сообщений форума с сохранением в SQLite"
    )
    parser.add_argument(
        "url",
        nargs="?",
        help="адрес страницы форума",
    )
    parser.add_argument(
        "--fixture",
        action="store_true",
        help="разобрать локальный HTML-слепок (без обращения к сети)",
    )
    parser.add_argument(
        "--db",
        default="forum.db",
        help="путь к файлу базы данных (по умолчанию forum.db)",
    )
    return parser


def main():
    argument_parser = build_argument_parser()
    args = argument_parser.parse_args()

    if not args.fixture and not args.url:
        argument_parser.error("укажите URL страницы или флаг --fixture")

    parser = ForumParser()
    if args.fixture:
        html = FIXTURE_PATH.read_text(encoding="utf-8")
        comments = parser.parse_html(html)
        source = f"локальный файл {FIXTURE_PATH}"
    else:
        comments = parser.parse_page(args.url)
        source = args.url

    print(f"Источник: {source}")
    print(f"Найдено сообщений: {len(comments)}\n")
    for comment in comments:
        print(f"[{comment['id']}] {comment['name']}: {comment['message']}")

    repository = DatabaseRepository(args.db)
    try:
        saved = parser.save_to_db(comments, repository)
    finally:
        repository.close()

    print(f"\nСохранено в БД '{args.db}': {saved}")


if __name__ == "__main__":
    main()
