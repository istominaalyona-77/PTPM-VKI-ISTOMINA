from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class CalculatorPage:
    """Page Object для Simple Calculator (globalsqa.com)."""

    _URL = "https://www.globalsqa.com/angularJs-protractor/SimpleCalculator/"

    # Реальные локаторы из DOM
    _FIRST_INPUT = (By.CSS_SELECTOR, "input[ng-model='a']")
    _SECOND_INPUT = (By.CSS_SELECTOR, "input[ng-model='b']")
    _OPERATOR_SELECT = (By.CSS_SELECTOR, "select[ng-model='operation']")
    _RESULT_TEXT = (By.CSS_SELECTOR, "b.result")

    # Кнопки инкремента/декремента
    _INCA_BUTTON = (By.XPATH, "//tr[.//input[@ng-model='a']]//button[normalize-space()='+1']")
    _DECA_BUTTON = (By.XPATH, "//tr[.//input[@ng-model='a']]//button[normalize-space()='-1']")
    _INCB_BUTTON = (By.XPATH, "//tr[.//input[@ng-model='b']]//button[normalize-space()='+1']")
    _DECB_BUTTON = (By.XPATH, "//tr[.//input[@ng-model='b']]//button[normalize-space()='-1']")

    def __init__(self, driver, timeout=15):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)

    def open(self, url=None):
        """Открыть страницу калькулятора.

        По умолчанию используется живой сайт, но тесты могут передать путь
        к локальной копии, чтобы прогон не зависел от сети.
        """
        self.driver.get(url or self._URL)
        # Angular рендерит элементы динамически — ждём видимости, а не просто presence
        self.wait.until(EC.visibility_of_element_located(self._FIRST_INPUT))

    # -------- Ввод значений --------
    def enter_first_number(self, value):
        field = self.wait.until(EC.element_to_be_clickable(self._FIRST_INPUT))
        field.clear()
        field.send_keys(str(value))

    def enter_second_number(self, value):
        field = self.wait.until(EC.element_to_be_clickable(self._SECOND_INPUT))
        field.clear()
        field.send_keys(str(value))

    def select_operator(self, operator):
        """Допустимые: '+', '-', '*', '/'."""
        select_el = self.wait.until(EC.presence_of_element_located(self._OPERATOR_SELECT))
        Select(select_el).select_by_value(operator)

    # -------- Кнопки +1 / -1 --------
    def increment_a(self):
        self.wait.until(EC.element_to_be_clickable(self._INCA_BUTTON)).click()

    def decrement_a(self):
        self.wait.until(EC.element_to_be_clickable(self._DECA_BUTTON)).click()

    def increment_b(self):
        self.wait.until(EC.element_to_be_clickable(self._INCB_BUTTON)).click()

    def decrement_b(self):
        self.wait.until(EC.element_to_be_clickable(self._DECB_BUTTON)).click()

    # -------- Результат --------
    def get_result_text(self):
        """Вернуть полный текст вида '5 + 3 = 8'."""
        el = self.wait.until(EC.visibility_of_element_located(self._RESULT_TEXT))
        return el.text.strip()

    def get_result_value(self):
        """Вернуть только числовой результат (после '=')."""
        text = self.get_result_text()
        # Формат "a op b = result"
        return text.split("=")[-1].strip()

    def calculate(self, first, second, operator):
        """Ввести данные и вернуть числовой результат."""
        self.enter_first_number(first)
        self.enter_second_number(second)
        self.select_operator(operator)
        return self.get_result_value()