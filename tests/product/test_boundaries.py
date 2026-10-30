import os,tempfile,unittest
from pathlib import Path
os.environ['LAB_DATA']=tempfile.mkdtemp(prefix='ops-tests-')
os.environ['GITHUB_REPOSITORY']='owner/lab'
os.environ['HOST_REPO']='/lab'
from unittest.mock import patch
from fastapi.testclient import TestClient
from lab import delivery,control
from lab.common import put,get

class ProductBoundaries(unittest.TestCase):
 def test_candidate_paths(self):
  for p in ['apps/order_api/pricing.py','tests/order/test_optional.py']:self.assertTrue(delivery.path_allowed(p))
  for p in ['../../etc/passwd','/apps/order_api/a.py','apps/order_api/../../lab/control.py','.github/workflows/contract.yml','contracts/check_http.py','tests/order/../product/test_x.py']:self.assertFalse(delivery.path_allowed(p),p)
 def test_symlink_cannot_escape(self):
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);(r/'apps/order_api').mkdir(parents=True);(r/'apps/order_api/leak').symlink_to('/etc')
   with self.assertRaises(Exception):delivery.safe_path(r,'apps/order_api/leak/passwd')
 def test_agent_cannot_reach_merge(self):
  c=TestClient(delivery.app)
  self.assertEqual(c.post('/ops/merge',json={'case_id':'x'}).status_code,403)
 def test_operator_required_for_fault_or_cancel(self):
  c=TestClient(control.app)
  self.assertEqual(c.post('/api/experiment/fault',json={}).status_code,403)
  self.assertEqual(c.post('/api/cases/x/cancel',json={}).status_code,403)
 def test_delayed_result_does_not_reverse_cancellation(self):
  c={'id':'cancel-test','state':'CANCELLED','cancelled':True};put('case',c['id'],c)
  stale={**c,'state':'REPAIRING','cancelled':False};control.save(stale,'CI_PENDING')
  self.assertTrue(get('case',c['id'])['cancelled']);self.assertEqual(get('case',c['id'])['state'],'CANCELLED')
 def test_cli_key_is_not_in_committed_template(self):
  text=(Path(__file__).resolve().parents[2]/'config/model.env.example').read_text();self.assertIn('API_KEY=\n',text)
