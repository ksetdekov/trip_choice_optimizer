import unittest
from database_driver import DatabaseDriver

class TestDatabaseDriver(unittest.TestCase):
    def setUp(self):
        # Use an in-memory SQLite database for testing
        self.db = DatabaseDriver(db_name=":memory:")

    def tearDown(self):
        self.db.close()

    def test_add_and_get_optimizations(self):
        user_id = 1
        opt_name = "Test Optimization"
        self.db.add_optimization(opt_name, user_id)
        optimizations = self.db.get_optimizations(user_id)
        self.assertEqual(len(optimizations), 1)
        self.assertEqual(optimizations[0][0], opt_name)

    def test_remove_optimization(self):
        user_id = 1
        opt_name = "Optimization To Remove"
        self.db.add_optimization(opt_name, user_id)
        # Ensure the optimization exists
        optimizations = self.db.get_optimizations(user_id)
        self.assertTrue(any(opt[0] == opt_name for opt in optimizations))
        # Remove the optimization
        self.db.remove_optimization(opt_name, user_id)
        optimizations_after = self.db.get_optimizations(user_id)
        self.assertFalse(any(opt[0] == opt_name for opt in optimizations_after))

    def test_add_and_get_variant(self):
        user_id = 1
        opt_name = "Optimization With Variant"
        variant_name = "Variant A"
        # First add an optimization
        self.db.add_optimization(opt_name, user_id)
        # Now add a variant
        self.db.add_variant(opt_name, variant_name, user_id)
        variants = self.db.get_variants(opt_name, user_id)
        self.assertEqual(len(variants), 1)
        self.assertEqual(variants[0][0], variant_name)

    def test_get_all_optimizations(self):
        # This test doesn't filter by user so we can test across multiple users
        self.db.add_optimization("User1 Optimization", 1)
        self.db.add_optimization("User2 Optimization", 2)
        all_opts = self.db.get_all_optimizations()
        self.assertEqual(len(all_opts), 2)

if __name__ == "__main__":
    unittest.main()
