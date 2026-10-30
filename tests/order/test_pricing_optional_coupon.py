import sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'apps/order_api'))
from pricing import total_cents


class OptionalCouponRegressionTests(unittest.TestCase):
    """POST /orders allows coupon to be omitted, which reaches pricing as None."""

    def test_missing_coupon_is_not_discounted(self):
        self.assertEqual(total_cents(3, None), 30000)

    def test_missing_coupon_does_not_raise(self):
        try:
            total_cents(1, None)
        except AttributeError as exc:
            self.fail(f'None coupon must not raise AttributeError: {exc}')

    def test_empty_and_blank_coupon_are_not_discounted(self):
        self.assertEqual(total_cents(2, ''), 20000)
        self.assertEqual(total_cents(2, '   '), 20000)

    def test_coupon_case_and_padding_are_normalized(self):
        self.assertEqual(total_cents(2, ' save10 '), 18000)

    def test_unknown_coupon_still_rejected(self):
        with self.assertRaises(ValueError):
            total_cents(1, 'BOGUS')


if __name__ == '__main__':
    unittest.main()
