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

    def test_add_optimization_new_and_existing_user(self):
        telegram_user_id = 12345
        optimization_name_A = "Optimization A"
        optimization_name_B = "Optimization B"

        # First call: user does not exist, so new user should be inserted.
        self.db.add_optimization(optimization_name_A, telegram_user_id)
        optimizations = self.db.get_optimizations(telegram_user_id)
        self.assertEqual(len(optimizations), 1)
        self.assertEqual(optimizations[0][0], optimization_name_A)
        
        # Second call with same telegram_user_id: user exists, so branch should re-use existing user.
        self.db.add_optimization(optimization_name_B, telegram_user_id)
        optimizations = self.db.get_optimizations(telegram_user_id)
        self.assertEqual(len(optimizations), 2)
        names = [opt[0] for opt in optimizations]
        self.assertIn(optimization_name_B, names)

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
    
    def test_get_optimization_name(self):
        user_id = 1
        opt_name = "Test Optimization Name"
        # Add an optimization for the user.
        self.db.add_optimization(opt_name, user_id)
        # Retrieve the list of optimizations. Each record is (optimization_name, change_datetime, id).
        optimizations = self.db.get_optimizations(user_id)
        self.assertTrue(len(optimizations) > 0, "No optimizations found for the user.")
        
        # Get the optimization_id from the first record.
        optimization_id = optimizations[0][2]
        # Call get_optimization_name using that ID.
        retrieved_name = self.db.get_optimization_name(optimization_id)
        self.assertEqual(retrieved_name, opt_name)

if __name__ == "__main__":
    unittest.main()
