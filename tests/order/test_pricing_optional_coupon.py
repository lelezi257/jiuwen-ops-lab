import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'apps/order_api'))
from pricing import total_cents
class OptionalCouponTests(unittest.TestCase):
 def test_missing_coupon_is_allowed(self):self.assertEqual(total_cents(2,None),20000)
 def test_blank_coupon_is_allowed(self):self.assertEqual(total_cents(3,'  '),30000)
 def test_coupon_is_normalized(self):self.assertEqual(total_cents(1,' save10 '),9000)
 def test_unknown_coupon_rejected(self):
  with self.assertRaises(ValueError):total_cents(1,'BOGUS')
