import os
import unittest
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.edge.options import Options

from calc_pages.calc_page import CalculatorPage


FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "simple_calculator.html"
LIVE_URL = "https://www.globalsqa.com/angularJs-protractor/SimpleCalculator/"
SCREENSHOT_DIR = Path(__file__).resolve().parent.parent / "test_screen"


class TestSimpleCalculator(unittest.TestCase):

    def setUp(self):
        SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

        edge_options = Options()
        # По умолчанию браузер видимый. HEADLESS=1 включает скрытый режим.
        if os.environ.get("HEADLESS", "").lower() in ("1", "true", "yes"):
            edge_options.add_argument("--headless=new")
        edge_options.add_argument("--disable-gpu")
        edge_options.add_argument("--window-size=1280,900")
        self.driver = webdriver.Edge(options=edge_options)
        self.calculator = CalculatorPage(self.driver)
        target_url = os.environ.get("CALC_URL") or FIXTURE_PATH.as_uri()
        self.calculator.open(target_url)

    def tearDown(self):
        test_name = self.id().split(".")[-1]
        screenshot_path = SCREENSHOT_DIR / f"{test_name}.png"
        try:
            self.driver.save_screenshot(str(screenshot_path))
        except Exception as error:
            print(f"Не удалось сохранить скриншот {screenshot_path}: {error}")
        finally:
            self.driver.quit()

    # ---------- Сложение ----------
    def test_addition_positive(self):
        self.assertEqual(self.calculator.calculate(5, 3, "+"), "8")

    def test_addition_negative(self):
        self.assertEqual(self.calculator.calculate(-5, -3, "+"), "-8")

    def test_addition_with_zero(self):
        self.assertEqual(self.calculator.calculate(0, 7, "+"), "7")

    # ---------- Вычитание ----------
    def test_subtraction(self):
        self.assertEqual(self.calculator.calculate(10, 4, "-"), "6")

    def test_subtraction_negative_result(self):
        self.assertEqual(self.calculator.calculate(3, 9, "-"), "-6")

    # ---------- Умножение ----------
    def test_multiplication(self):
        self.assertEqual(self.calculator.calculate(6, 7, "*"), "42")

    def test_multiplication_by_zero(self):
        self.assertEqual(self.calculator.calculate(123, 0, "*"), "0")

    # ---------- Деление ----------
    def test_division_exact(self):
        self.assertEqual(self.calculator.calculate(20, 4, "/"), "5")

    def test_division_decimal(self):
        self.assertEqual(self.calculator.calculate(10, 4, "/"), "2.5")

    def test_division_by_zero(self):
        """При делении на ноль AngularJS-калькулятор возвращает null."""
        result = self.calculator.calculate(10, 0, "/")
        self.assertEqual(result, "null")

    # ---------- Граничные значения ----------
    def test_large_numbers(self):
        self.assertEqual(self.calculator.calculate(1_000_000, 1_000_000, "+"), "2000000")

    def test_float_addition(self):
        result = self.calculator.calculate(0.1, 0.2, "+")
        self.assertIn(result, ("0.3", "0.30000000000000004"))

    def test_negative_multiplication(self):
        self.assertEqual(self.calculator.calculate(-4, 5, "*"), "-20")

    # ---------- Кнопки +1 / -1 ----------
    def test_increment_a(self):
        self.calculator.enter_first_number(5)
        self.calculator.enter_second_number(0)
        self.calculator.select_operator("+")
        self.calculator.increment_a()
        self.assertEqual(self.calculator.get_result_value(), "6")

    def test_decrement_a(self):
        self.calculator.enter_first_number(5)
        self.calculator.enter_second_number(0)
        self.calculator.select_operator("+")
        self.calculator.decrement_a()
        self.assertEqual(self.calculator.get_result_value(), "4")

    def test_increment_b(self):
        self.calculator.enter_first_number(0)
        self.calculator.enter_second_number(7)
        self.calculator.select_operator("+")
        self.calculator.increment_b()
        self.assertEqual(self.calculator.get_result_value(), "8")

    # ---------- Проверка полного текста результата ----------
    def test_result_text_format(self):
        self.calculator.calculate(5, 3, "+")
        self.assertEqual(self.calculator.get_result_text(), "5 + 3 = 8")


if __name__ == "__main__":
    unittest.main()