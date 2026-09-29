import datetime
import unittest

from delivery_fixed import calculate_delivery_cost

SHIPPING_DATE = datetime.date(2026, 9, 3)
ERROR_RESULT = (-1, "0000-00-00")


class TestFixExpressPricing(unittest.TestCase):
    """Проверка исправления №2: экспресс не должен стоить дешевле обычного."""

    def test_express_delivery_costs_more_than_standard(self):
        standard, _ = calculate_delivery_cost(1.0, 100, "обычный", is_express=False)
        express, _ = calculate_delivery_cost(1.0, 100, "обычный", is_express=True)
        self.assertGreater(express, standard)

    def test_express_hazardous_costs_more_than_standard(self):
        standard, _ = calculate_delivery_cost(1.0, 100, "опасный", is_express=False)
        express, _ = calculate_delivery_cost(1.0, 100, "опасный", is_express=True)
        self.assertGreater(express, standard)

    def test_express_surcharge_is_fifty_percent(self):
        # 700 * 1.5 = 1050
        self.assertEqual(calculate_delivery_cost(1.0, 100, "обычный", is_express=True)[0], 1050)


class TestFixExpressDeliveryTime(unittest.TestCase):
    """Проверка исправления №3: минимальный срок доставки — один день."""

    def test_express_delivery_is_not_on_shipping_day(self):
        _, date = calculate_delivery_cost(1.0, 100, "обычный", is_express=True)
        self.assertEqual(date, "2026-09-04")

    def test_express_delivery_time_is_never_zero_days(self):
        _, date = calculate_delivery_cost(1.0, 499, "обычный", is_express=True)
        days = (datetime.datetime.strptime(date, "%Y-%m-%d").date() - SHIPPING_DATE).days
        self.assertGreaterEqual(days, 1)

    def test_express_still_halves_delivery_time_for_long_distance(self):
        _, date = calculate_delivery_cost(1.0, 2000, "обычный", is_express=True)
        self.assertEqual(date, "2026-09-05")


class TestFixParameterTypeValidation(unittest.TestCase):
    """Проверка исправления №1: неверные типы не должны вызывать TypeError."""

    def test_non_numeric_weight_returns_error_instead_of_exception(self):
        self.assertEqual(calculate_delivery_cost("тяжёлый", 100, "обычный"), ERROR_RESULT)

    def test_non_numeric_distance_returns_error_instead_of_exception(self):
        self.assertEqual(calculate_delivery_cost(1.0, "далеко", "обычный"), ERROR_RESULT)

    def test_none_package_type_returns_error(self):
        self.assertEqual(calculate_delivery_cost(1.0, 100, None), ERROR_RESULT)


class TestFixDidNotBreakOriginalBehaviour(unittest.TestCase):
    """Проверка отсутствия регрессий: обычные сценарии считаются как прежде."""

    def test_light_package_cost_is_unchanged(self):
        self.assertEqual(calculate_delivery_cost(1.0, 100, "обычный"), (700, "2026-09-04"))

    def test_heavy_package_cost_is_unchanged(self):
        self.assertEqual(calculate_delivery_cost(50.0, 5000, "обычный"), (37800, "2026-09-13"))

    def test_fragile_surcharge_is_unchanged(self):
        self.assertEqual(calculate_delivery_cost(10.0, 100, "хрупкий"), (1140, "2026-09-04"))

    def test_hazardous_surcharge_is_unchanged(self):
        self.assertEqual(calculate_delivery_cost(25.0, 200, "опасный"), (2800, "2026-09-04"))

    def test_boundary_validation_is_unchanged(self):
        self.assertEqual(calculate_delivery_cost(0.05, 100, "обычный"), ERROR_RESULT)
        self.assertEqual(calculate_delivery_cost(50.1, 100, "обычный"), ERROR_RESULT)
        self.assertEqual(calculate_delivery_cost(1.0, 5001, "обычный"), ERROR_RESULT)
        self.assertEqual(calculate_delivery_cost(1.0, 100, "неизвестный"), ERROR_RESULT)


if __name__ == "__main__":
    unittest.main()
