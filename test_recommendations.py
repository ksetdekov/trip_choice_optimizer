import unittest

from database_driver import DatabaseDriver
from services.recommendations import (
    get_active_or_only_optimization_id,
    get_recommendation,
)


class TestRecommendations(unittest.TestCase):
    def setUp(self):
        self.db = DatabaseDriver(db_name=":memory:")
        self.user_id = 1
        self.optimization_id = self.db.add_optimization(
            "Commute",
            self.user_id,
            metric_type="time",
            objective="minimize",
            recency_days=30,
            rho=1.0,
        )
        self.variant_a = self.db.add_variant_by_id(self.optimization_id, "A")
        self.variant_b = self.db.add_variant_by_id(self.optimization_id, "B")

    def tearDown(self):
        self.db.close()

    def test_recency_window_is_relative_to_latest_sample(self):
        self.db.add_sample_by_ids(
            self.optimization_id,
            self.variant_a,
            1.0,
            change_datetime="2024-01-01 08:00:00",
        )
        self.db.add_sample_by_ids(
            self.optimization_id,
            self.variant_b,
            3.0,
            change_datetime="2025-01-10 08:00:00",
        )
        self.db.add_sample_by_ids(
            self.optimization_id,
            self.variant_a,
            2.0,
            change_datetime="2025-01-15 08:00:00",
        )

        recommendation = get_recommendation(self.db, self.user_id, self.optimization_id)

        counts = {
            row["name"]: int(row["Te"])
            for _, row in recommendation.ranking.iterrows()
        }
        self.assertEqual(counts["A"], 1)
        self.assertEqual(counts["B"], 1)

    def test_recommendation_rebuild_does_not_double_count(self):
        self.db.add_sample_by_ids(
            self.optimization_id,
            self.variant_a,
            1.0,
            change_datetime="2025-01-01 08:00:00",
        )

        first = get_recommendation(self.db, self.user_id, self.optimization_id)
        second = get_recommendation(self.db, self.user_id, self.optimization_id)

        first_count = int(first.ranking[first.ranking["name"] == "A"]["Te"].iloc[0])
        second_count = int(second.ranking[second.ranking["name"] == "A"]["Te"].iloc[0])
        self.assertEqual(first_count, 1)
        self.assertEqual(second_count, 1)

    def test_only_optimization_becomes_active(self):
        self.assertEqual(
            get_active_or_only_optimization_id(self.db, self.user_id),
            self.optimization_id,
        )
        self.assertEqual(
            self.db.get_active_optimization_id(self.user_id),
            self.optimization_id,
        )


if __name__ == "__main__":
    unittest.main()
