import unittest

from src.converter import Converter


class TestConverter(unittest.TestCase):
    def test_range_ge_100_7_returns_1000(self):
        self.assertEqual(Converter.do(100.7), 1000)
        self.assertEqual(Converter.do(150.0), 1000)
        self.assertEqual(Converter.do(1000.9), 1000)

    def test_range_between_0_and_100_7_returns_int_part(self):
        self.assertEqual(Converter.do(65.7), 65)
        self.assertEqual(Converter.do(0.1), 0)
        self.assertEqual(Converter.do(5.9), 5)
        self.assertEqual(Converter.do(100.6), 100)
        self.assertEqual(Converter.do(99.9), 99)

    def test_zero_raises_value_error(self):
        with self.assertRaises(ValueError):
            Converter.do(0.0)

    def test_range_between_minus30_4_and_0_returns_int_part_minus_5(self):
        self.assertEqual(Converter.do(-5.7), -10)
        self.assertEqual(Converter.do(-1.2), -6)
        self.assertEqual(Converter.do(-30.4), int(-30.4) - 5)
        self.assertEqual(Converter.do(-0.1), int(-0.1) - 5)

    def test_range_le_minus30_5_returns_minus2000(self):
        self.assertEqual(Converter.do(-30.5), -2000)
        self.assertEqual(Converter.do(-50.0), -2000)
        self.assertEqual(Converter.do(-94.5), -2000)
        self.assertEqual(Converter.do(-1000.0), -2000)

    def test_boundaries_between_ranges(self):
        self.assertEqual(Converter.do(100.7), 1000)
        self.assertEqual(Converter.do(-30.5), -2000)
        self.assertEqual(Converter.do(-30.4), int(-30.4) - 5)
        self.assertEqual(Converter.do(100.6), 100)
        with self.assertRaises(ValueError):
            Converter.do(0.0)

    def test_truncation_towards_zero_for_negative(self):
        self.assertEqual(Converter.do(-10.8), int(-10.8) - 5)
        self.assertEqual(Converter.do(-29.9), int(-29.9) - 5)


if __name__ == "__main__":
    unittest.main()