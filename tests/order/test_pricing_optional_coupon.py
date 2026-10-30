import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'apps/order_api'))
from pricing import total_cents
class OptionalCouponRegressionTests(unittest.TestCase):
 """POST /orders sends coupon=None when the field is omitted (Order.coupon default=None)."""
 def test_missing_coupon_is_not_a_server_error(self):
  self.assertEqual(total_cents(1,None),10000)
 def test_empty_coupon_matches_missing_coupon(self):
  self.assertEqual(total_cents(3,''),total_cents(3,None))
  self.assertEqual(total_cents(3,''),30000)
 def test_coupon_is_still_normalized(self):
  self.assertEqual(total_cents(2,' save10 '),18000)
 def test_invalid_coupon_still_rejected(self):
  with self.assertRaises(ValueError):total_cents(1,'BADCODE')
if __name__=='__main__':unittest.main()
