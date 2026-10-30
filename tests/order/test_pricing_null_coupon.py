import sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'apps/order_api'))
from pricing import total_cents


class NullCouponRegressionTests(unittest.TestCase):
    """Regression: POST /orders with no coupon returned 500
    AttributeError: 'NoneType' object has no attribute 'strip'."""

    def test_none_coupon_is_accepted_at_base_price(self):
        self.assertEqual(total_cents(1, None), 10000)

    def test_none_coupon_multiple_quantity(self):
        self.assertEqual(total_cents(3, None), 30000)

    def test_empty_and_whitespace_coupon_are_base_price(self):
        self.assertEqual(total_cents(1, ''), 10000)
        self.assertEqual(total_cents(1, '   '), 10000)

    def test_coupon_still_normalized_and_applied(self):
        self.assertEqual(total_cents(2, ' save10 '), 18000)

    def test_invalid_coupon_still_rejected(self):
        with self.assertRaises(ValueError):
            total_cents(1, 'BOGUS')


if __name__ == '__main__':
    unittest.main()
