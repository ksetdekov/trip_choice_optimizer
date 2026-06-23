import os
import unittest

from database_driver import DatabaseDriver
from services.plots import render_probability_plot


class TestPlots(unittest.TestCase):
    def setUp(self):
        self.db = DatabaseDriver(db_name=":memory:")
        self.user_id = 1
        self.optimization_id = self.db.add_optimization("Commute", self.user_id)
        self.variant_a = self.db.add_variant_by_id(self.optimization_id, "A")
        self.variant_b = self.db.add_variant_by_id(self.optimization_id, "B")
        self.db.add_sample_by_ids(
            self.optimization_id,
            self.variant_a,
            10,
            change_datetime="2025-01-01 08:00:00",
        )
        self.db.add_sample_by_ids(
            self.optimization_id,
            self.variant_b,
            12,
            change_datetime="2025-01-02 08:00:00",
        )

    def tearDown(self):
        self.db.close()

    def test_probability_plot_writes_png(self):
        path = render_probability_plot(
            self.db,
            self.user_id,
            self.optimization_id,
            iterations=10,
        )
        try:
            self.assertTrue(os.path.exists(path))
            self.assertGreater(os.path.getsize(path), 0)
        finally:
            if os.path.exists(path):
                os.remove(path)


if __name__ == "__main__":
    unittest.main()
