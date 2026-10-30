import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'apps/order_api'))
from pricing import total_cents


class OptionalCouponTests(unittest.TestCase):
    def test_missing_coupon_is_full_price(self):
        self.assertEqual(total_cents(3, None), 30000)

    def test_blank_coupon_is_full_price(self):
        self.assertEqual(total_cents(1, ''), 10000)
        self.assertEqual(total_cents(1, '   '), 10000)

    def test_valid_coupon_still_applies(self):
        self.assertEqual(total_cents(2, 'save10'), 18000)

    def test_invalid_coupon_rejected(self):
        with self.assertRaises(ValueError):
            total_cents(1, 'BOGUS')


if __name__ == '__main__':
    unittest.main()
