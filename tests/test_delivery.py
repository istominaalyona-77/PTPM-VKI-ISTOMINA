import datetime
import unittest

from delivery import calculate_delivery_cost

SHIPPING_DATE = datetime.date(2026, 9, 3)
ERROR_RESULT = (-1, "0000-00-00")


class TestWeightValidation(unittest.TestCase):
    """Проверка физических ограничений на вес посылки."""

    def test_weight_below_minimum_returns_error(self):
        self.assertEqual(calculate_delivery_cost(0.05, 100, "обычный"), ERROR_RESULT)

    def test_weight_at_minimum_boundary_is_accepted(self):
        self.assertEqual(calculate_delivery_cost(0.1, 100, "обычный"), (700, "2026-09-04"))

    def test_weight_at_maximum_boundary_is_accepted(self):
        cost, date = calculate_delivery_cost(50.0, 100, "обычный")
        self.assertEqual((cost, date), (1050, "2026-09-04"))

    def test_weight_above_maximum_returns_error(self):
        self.assertEqual(calculate_delivery_cost(50.1, 100, "обычный"), ERROR_RESULT)

    def test_negative_weight_returns_error(self):
        self.assertEqual(calculate_delivery_cost(-5.0, 100, "обычный"), ERROR_RESULT)


class TestDistanceValidation(unittest.TestCase):
    """Проверка физических ограничений на расстояние доставки."""

    def test_zero_distance_returns_error(self):
        self.assertEqual(calculate_delivery_cost(1.0, 0, "обычный"), ERROR_RESULT)

    def test_negative_distance_returns_error(self):
        self.assertEqual(calculate_delivery_cost(1.0, -100, "обычный"), ERROR_RESULT)

    def test_distance_at_maximum_boundary_is_accepted(self):
        self.assertEqual(calculate_delivery_cost(1.0, 5000, "обычный"), (25200, "2026-09-13"))

    def test_distance_above_maximum_returns_error(self):
        self.assertEqual(calculate_delivery_cost(1.0, 5001, "обычный"), ERROR_RESULT)


class TestPackageTypeValidation(unittest.TestCase):
    """Проверка допустимых типов посылки."""

    def test_unknown_package_type_returns_error(self):
        self.assertEqual(calculate_delivery_cost(1.0, 100, "неизвестный"), ERROR_RESULT)

    def test_empty_package_type_returns_error(self):
        self.assertEqual(calculate_delivery_cost(1.0, 100, ""), ERROR_RESULT)

    def test_package_type_is_case_sensitive(self):
        self.assertEqual(calculate_delivery_cost(1.0, 100, "Обычный"), ERROR_RESULT)

    def test_all_three_documented_types_are_accepted(self):
        for package_type in ("обычный", "хрупкий", "опасный"):
            with self.subTest(package_type=package_type):
                cost, date = calculate_delivery_cost(1.0, 100, package_type)
                self.assertNotEqual(cost, -1, f"Тип «{package_type}» должен приниматься")
                self.assertNotEqual(date, "0000-00-00")


class TestCostCalculation(unittest.TestCase):
    """Проверка расчёта стоимости по базовому тарифу."""

    def test_base_cost_consists_of_fixed_fee_and_distance_fee(self):
        # 200 (фиксированная) + 100 км * 5 (за км) = 700
        cost, _ = calculate_delivery_cost(1.0, 100, "обычный")
        self.assertEqual(cost, 700)

    def test_cost_grows_linearly_with_distance(self):
        near, _ = calculate_delivery_cost(1.0, 100, "обычный")
        far, _ = calculate_delivery_cost(1.0, 200, "обычный")
        self.assertEqual(far - near, 500)

    def test_minimum_distance_is_charged_as_base_fee_only(self):
        self.assertEqual(calculate_delivery_cost(0.1, 1, "обычный"), (205, "2026-09-04"))


class TestWeightCoefficients(unittest.TestCase):
    """Проверка весовых коэффициентов тарифа."""

    def test_weight_up_to_five_kg_has_no_coefficient(self):
        self.assertEqual(calculate_delivery_cost(5.0, 100, "обычный")[0], 700)

    def test_medium_weight_receives_twelve_percent_coefficient(self):
        # 700 * 1.2 = 840
        self.assertEqual(calculate_delivery_cost(10.0, 100, "обычный")[0], 840)

    def test_heavy_weight_receives_fifty_percent_coefficient(self):
        # 700 * 1.5 = 1050
        self.assertEqual(calculate_delivery_cost(30.0, 100, "обычный")[0], 1050)

    def test_weight_of_exactly_twenty_kg_uses_heavy_coefficient(self):
        self.assertEqual(calculate_delivery_cost(20.0, 100, "обычный")[0], 1050)

    def test_weight_coefficient_combines_with_distance_fee(self):
        # (200 + 1000) * 1.2 = 1440
        self.assertEqual(calculate_delivery_cost(10.0, 200, "обычный")[0], 1440)


class TestPackageSurcharges(unittest.TestCase):
    """Проверка надбавок за тип посылки."""

    def test_fragile_package_adds_three_hundred_rubles(self):
        # 700 + 300 = 1000
        self.assertEqual(calculate_delivery_cost(1.0, 100, "хрупкий")[0], 1000)

    def test_hazardous_package_adds_one_thousand_rubles(self):
        # 700 + 1000 = 1700
        self.assertEqual(calculate_delivery_cost(1.0, 100, "опасный")[0], 1700)

    def test_fragile_surcharge_is_applied_after_weight_coefficient(self):
        # 700 * 1.5 = 1050, затем 1050 + 300 = 1350
        self.assertEqual(calculate_delivery_cost(25.0, 100, "хрупкий")[0], 1350)

    def test_hazardous_surcharge_is_applied_after_weight_coefficient(self):
        # (200 + 1500) * 1.5 = 2550, затем 2550 + 1000 = 3550
        self.assertEqual(calculate_delivery_cost(25.0, 300, "опасный")[0], 3550)


class TestDeliveryDate(unittest.TestCase):
    """Проверка расчёта даты доставки."""

    def test_delivery_takes_at_least_one_day(self):
        _, date = calculate_delivery_cost(1.0, 100, "обычный")
        self.assertEqual(date, "2026-09-04")

    def test_one_day_added_per_five_hundred_kilometres(self):
        _, date = calculate_delivery_cost(1.0, 1000, "обычный")
        self.assertEqual(date, "2026-09-05")

    def test_four_days_added_for_two_thousand_kilometres(self):
        _, date = calculate_delivery_cost(1.0, 2000, "обычный")
        self.assertEqual(date, "2026-09-07")

    def test_ten_days_added_for_maximum_distance(self):
        _, date = calculate_delivery_cost(1.0, 5000, "обычный")
        self.assertEqual(date, "2026-09-13")

    def test_date_is_returned_in_iso_format(self):
        _, date = calculate_delivery_cost(1.0, 100, "обычный")
        datetime.datetime.strptime(date, "%Y-%m-%d")
        self.assertEqual(date, (SHIPPING_DATE + datetime.timedelta(days=1)).strftime("%Y-%m-%d"))


class TestExpressDelivery(unittest.TestCase):
    """Проверка экспресс-доставки."""

    def test_express_halves_delivery_time_for_long_distance(self):
        _, express_date = calculate_delivery_cost(1.0, 2000, "обычный", is_express=True)
        self.assertEqual(express_date, "2026-09-05")

    def test_express_delivery_should_cost_more_than_standard(self):
        """Экспресс — ускоренная услуга, она не может быть дешевле обычной."""
        standard, _ = calculate_delivery_cost(1.0, 100, "обычный", is_express=False)
        express, _ = calculate_delivery_cost(1.0, 100, "обычный", is_express=True)
        self.assertGreater(express, standard,
                           "Экспресс-доставка не должна стоить дешевле стандартной")

    def test_express_hazardous_should_cost_more_than_standard(self):
        """Надбавка за опасный груз не должна исчезать при заказе экспресса."""
        standard, _ = calculate_delivery_cost(1.0, 100, "опасный", is_express=False)
        express, _ = calculate_delivery_cost(1.0, 100, "опасный", is_express=True)
        self.assertGreater(express, standard)

    def test_express_delivery_should_not_be_same_day_as_shipping(self):
        """Минимальный срок доставки — один день, даже для экспресса."""
        _, date = calculate_delivery_cost(1.0, 100, "обычный", is_express=True)
        self.assertNotEqual(date, SHIPPING_DATE.strftime("%Y-%m-%d"),
                            "Экспресс не может доставлять в день отправки")

    def test_express_delivery_time_is_never_zero_days(self):
        _, date = calculate_delivery_cost(1.0, 499, "обычный", is_express=True)
        days = (datetime.datetime.strptime(date, "%Y-%m-%d").date() - SHIPPING_DATE).days
        self.assertGreaterEqual(days, 1)


class TestParameterTypeValidation(unittest.TestCase):
    """Проверка поведения при некорректных типах входных данных."""

    def test_non_numeric_weight_returns_error_instead_of_exception(self):
        """По условию задачи неверные параметры должны давать (-1, '0000-00-00')."""
        self.assertEqual(calculate_delivery_cost("тяжёлый", 100, "обычный"), ERROR_RESULT)

    def test_non_numeric_distance_returns_error_instead_of_exception(self):
        self.assertEqual(calculate_delivery_cost(1.0, "далеко", "обычный"), ERROR_RESULT)


if __name__ == "__main__":
    unittest.main()
