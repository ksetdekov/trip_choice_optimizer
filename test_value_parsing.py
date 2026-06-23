import unittest

from services.value_parsing import (
    format_observation_value,
    parse_observation_value,
    parse_time_to_minutes,
)


class TestValueParsing(unittest.TestCase):
    def test_parse_time_to_minutes(self):
        self.assertAlmostEqual(parse_time_to_minutes("00:35:30"), 35.5)
        self.assertAlmostEqual(parse_time_to_minutes("1:02:03"), 62.05)
        self.assertAlmostEqual(parse_time_to_minutes("0:08:03.7"), 8.0616666667)

    def test_parse_time_metric_accepts_minutes(self):
        self.assertEqual(parse_observation_value("42.5", "time"), 42.5)
        self.assertEqual(parse_observation_value("42,5", "time"), 42.5)

    def test_parse_number_metric_rejects_time(self):
        with self.assertRaises(ValueError):
            parse_observation_value("00:35:30", "number")

    def test_format_time_value(self):
        self.assertEqual(format_observation_value(35.5, "time"), "00:35:30")


if __name__ == "__main__":
    unittest.main()
