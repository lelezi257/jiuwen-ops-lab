import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'apps/order_api'))
from pricing import total_cents
class OptionalCouponTests(unittest.TestCase):
 def test_coupon_none_uses_base_price(self):self.assertEqual(total_cents(3,None),30000)
 def test_coupon_empty_string_uses_base_price(self):self.assertEqual(total_cents(1,''),10000)
 def test_coupon_whitespace_uses_base_price(self):self.assertEqual(total_cents(2,'   '),20000)
 def test_coupon_lowercase_valid(self):self.assertEqual(total_cents(1,' save10 '),9000)
 def test_invalid_coupon_rejected(self):
  with self.assertRaises(ValueError):total_cents(1,'BOGUS')
if __name__=='__main__':unittest.main()
