import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'apps/order_api'))
from pricing import total_cents
class OptionalCouponTests(unittest.TestCase):
 def test_none_coupon(self):self.assertEqual(total_cents(1,None),10000)
 def test_empty_coupon(self):self.assertEqual(total_cents(3,''),30000)
 def test_blank_coupon(self):self.assertEqual(total_cents(2,'   '),20000)
 def test_none_coupon_with_save10_case(self):self.assertEqual(total_cents(5,' save10 '),45000)
 def test_none_coupon_rejects_invalid(self):
  with self.assertRaises(ValueError):total_cents(1,'BAD')
