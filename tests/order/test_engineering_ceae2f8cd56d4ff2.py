import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'apps/order_api'))
from pricing import total_cents
class OptionalCouponRegression(unittest.TestCase):
 def test_optional_coupon(self):self.assertEqual(total_cents(2,None),20000)
 def test_discount(self):self.assertEqual(total_cents(2,'SAVE10'),18000)
