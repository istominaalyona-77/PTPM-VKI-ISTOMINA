"""Тесты веб-парсера :class:`ForumParser`.

Разбор HTML проверяется на заранее сохранённой странице-фикстуре
``tests/fixtures/forum_page.html``, поэтому тесты не зависят от сети.
Сетевые запросы в ``parse_page`` заменяются заглушками ``unittest.mock``.
"""

import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import requests

from src.database import DatabaseRepository
from src.parser import DEFAULT_USER_AGENT, ForumParser, ParserError

FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "forum_page.html"


class ParserTestCase(unittest.TestCase):
    def setUp(self):
        self.parser = ForumParser()
        self.html = FIXTURE_PATH.read_text(encoding="utf-8")


class TestParseHtml(ParserTestCase):
    def test_parse_html_returns_all_valid_comments(self):
        comments = self.parser.parse_html(self.html)
        self.assertEqual([comment["id"] for comment in comments],
                         [101, 102, 103, 104, 105])

    def test_parse_html_extracts_id_name_and_message(self):
        comments = {comment["id"]: comment
                    for comment in self.parser.parse_html(self.html)}
        self.assertEqual(comments[101]["name"], "alice")
        self.assertEqual(comments[101]["message"], "<p>Привет, <b>мир</b>!</p>")

    def test_parse_html_preserves_inner_html_markup(self):
        comments = {comment["id"]: comment
                    for comment in self.parser.parse_html(self.html)}
        self.assertIn("<b>мир</b>", comments[101]["message"])
        self.assertIn("<i>пост</i>", comments[103]["message"])

    def test_parse_html_reads_id_from_element_attribute_and_link(self):
        comments = {comment["id"]: comment
                    for comment in self.parser.parse_html(self.html)}
        self.assertEqual(comments[103]["name"], "alice")
        self.assertEqual(comments[103]["message"],
                         "<span>Ответ на <i>пост</i> 101</span>")
        self.assertEqual(comments[105]["name"], "erin")

    def test_parse_html_skips_service_block_without_id(self):
        names = [comment["name"] for comment in self.parser.parse_html(self.html)]
        self.assertNotIn("system", names)

    def test_parse_html_skips_duplicate_ids(self):
        html = """
        <div class="post" data-comment-id="7">
            <span class="post__author">alice</span>
            <div class="post__message">первое</div>
        </div>
        <div class="post" data-comment-id="7">
            <span class="post__author">bob</span>
            <div class="post__message">второе</div>
        </div>
        """
        comments = self.parser.parse_html(html)
        self.assertEqual(comments, [{"id": 7, "name": "alice",
                                     "message": "первое"}])

    def test_parse_html_skips_posts_without_author_or_message(self):
        html = """
        <div class="post" data-comment-id="1">
            <div class="post__message">без автора</div>
        </div>
        <div class="post" data-comment-id="2">
            <span class="post__author">bob</span>
        </div>
        """
        self.assertEqual(self.parser.parse_html(html), [])

    def test_parse_html_returns_empty_list_when_no_posts(self):
        html = "<html><body><p>Сообщений на странице нет</p></body></html>"
        self.assertEqual(self.parser.parse_html(html), [])

    def test_parse_html_raises_on_empty_page(self):
        for html in ("", "   ", None):
            with self.subTest(html=html):
                with self.assertRaises(ParserError):
                    self.parser.parse_html(html)


class TestParsePage(ParserTestCase):
    @patch("src.parser.requests.get")
    def test_parse_page_sends_user_agent_header(self, mock_get):
        response = Mock()
        response.text = self.html
        mock_get.return_value = response

        self.parser.parse_page("https://forum.example.com/topic/1")

        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertEqual(args[0], "https://forum.example.com/topic/1")
        self.assertEqual(kwargs["headers"]["User-Agent"], DEFAULT_USER_AGENT)
        self.assertEqual(kwargs["timeout"], 10)
        response.raise_for_status.assert_called_once_with()

    @patch("src.parser.requests.get")
    def test_parse_page_returns_comments_from_downloaded_html(self, mock_get):
        response = Mock()
        response.text = self.html
        mock_get.return_value = response

        comments = self.parser.parse_page("https://forum.example.com/topic/1")

        self.assertEqual(len(comments), 5)
        self.assertEqual(comments[0]["id"], 101)

    @patch("src.parser.requests.get",
           side_effect=requests.ConnectionError("нет сети"))
    def test_parse_page_raises_parser_error_on_network_failure(self, mock_get):
        with self.assertRaises(ParserError):
            self.parser.parse_page("https://forum.example.com/topic/1")

    @patch("src.parser.requests.get")
    def test_parse_page_raises_parser_error_on_http_error(self, mock_get):
        response = Mock()
        response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        mock_get.return_value = response

        with self.assertRaises(ParserError):
            self.parser.parse_page("https://forum.example.com/missing")

    def test_parse_page_rejects_empty_url(self):
        with self.assertRaises(ParserError):
            self.parser.parse_page("")
        with self.assertRaises(ParserError):
            self.parser.parse_page(None)


class TestParserSetup(unittest.TestCase):
    def test_default_headers_contain_user_agent(self):
        parser = ForumParser()
        self.assertEqual(parser.headers["User-Agent"], DEFAULT_USER_AGENT)
        self.assertEqual(parser.timeout, 10)

    def test_custom_headers_are_merged_with_defaults(self):
        parser = ForumParser(headers={"X-Test": "1"})
        self.assertEqual(parser.headers["X-Test"], "1")
        self.assertEqual(parser.headers["User-Agent"], DEFAULT_USER_AGENT)

    def test_custom_user_agent_overrides_default(self):
        parser = ForumParser(headers={"User-Agent": "Custom-Agent/1.0"})
        self.assertEqual(parser.headers["User-Agent"], "Custom-Agent/1.0")

    def test_invalid_headers_type_is_rejected(self):
        with self.assertRaises(ValueError):
            ForumParser(headers="User-Agent: test")

    def test_invalid_timeout_is_rejected(self):
        for timeout in (0, -1, "10", True):
            with self.subTest(timeout=timeout):
                with self.assertRaises(ValueError):
                    ForumParser(timeout=timeout)


class TestSaveToDb(ParserTestCase):
    def setUp(self):
        super().setUp()
        self.repository = DatabaseRepository(":memory:")
        self.comments = self.parser.parse_html(self.html)

    def tearDown(self):
        self.repository.close()

    def test_save_to_db_stores_all_comments(self):
        saved = self.parser.save_to_db(self.comments, self.repository)

        self.assertEqual(saved, 5)
        self.assertEqual(self.repository.get_by_id(101)["name"], "alice")
        self.assertEqual(self.repository.get_by_id(105)["name"], "erin")

    def test_save_to_db_updates_existing_comments_without_duplicates(self):
        self.parser.save_to_db(self.comments, self.repository)

        changed = [dict(comment) for comment in self.comments]
        changed[0]["message"] = "<p>Отредактировано</p>"
        self.parser.save_to_db(changed, self.repository)

        self.assertEqual(self.repository.get_by_id(101)["message"],
                         "<p>Отредактировано</p>")
        self.assertEqual(len(self.repository.get_by_name("alice")), 2)

    def test_save_to_db_returns_zero_for_empty_list(self):
        self.assertEqual(self.parser.save_to_db([], self.repository), 0)

    def test_save_to_db_rejects_non_list(self):
        with self.assertRaises(ParserError):
            self.parser.save_to_db({"id": 1, "name": "a", "message": "b"},
                                   self.repository)

    def test_save_to_db_rejects_malformed_records(self):
        with self.assertRaises(ParserError):
            self.parser.save_to_db([{"id": 1, "name": "alice"}],
                                   self.repository)
        with self.assertRaises(ParserError):
            self.parser.save_to_db([{"id": "1", "name": "alice",
                                     "message": "текст"}], self.repository)
        with self.assertRaises(ParserError):
            self.parser.save_to_db([{"id": 1, "name": "  ",
                                     "message": "текст"}], self.repository)
        with self.assertRaises(ParserError):
            self.parser.save_to_db([{"id": 1, "name": "alice",
                                     "message": 123}], self.repository)
        with self.assertRaises(ParserError):
            self.parser.save_to_db([{"id": 1, "name": "alice",
                                     "message": "   "}], self.repository)
        with self.assertRaises(ParserError):
            self.parser.save_to_db(["не словарь"], self.repository)

    def test_save_to_db_requires_repository(self):
        with self.assertRaises(ParserError):
            self.parser.save_to_db(self.comments, None)


if __name__ == "__main__":
    unittest.main()
