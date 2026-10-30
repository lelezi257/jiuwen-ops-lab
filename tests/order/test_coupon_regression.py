import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'apps/order_api'))
from pricing import total_cents


class CouponRegressionTests(unittest.TestCase):
    def test_missing_coupon_is_full_price(self):
        self.assertEqual(total_cents(2,None),20000)

    def test_blank_coupon_is_full_price(self):
        self.assertEqual(total_cents(2,''),20000)

    def test_whitespace_coupon_is_full_price(self):
        self.assertEqual(total_cents(2,'   '),20000)

    def test_lowercase_coupon_is_normalized(self):
        self.assertEqual(total_cents(2,' save10 '),18000)

    def test_invalid_coupon_still_rejected(self):
        with self.assertRaises(ValueError):
            total_cents(2,'BAD')
