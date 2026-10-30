#!/usr/bin/env python3
"""Actual no-model environment qualification. Does not claim Agent success."""
import json,time,urllib.request,uuid
from pathlib import Path
root=Path(__file__).resolve().parents[1]
def read(path,base='http://127.0.0.1:18780'):
 with urllib.request.urlopen(base+path,timeout=30) as r:return json.load(r)
status=read('/api/status');assert status['runner']['ok'],status['runner'];assert status['runner']['fake_model'] is False
assert status['evidence']['ok'] and status['delivery']['ok'];assert status['release']['consistent'],status['release']
report={'scope':'no_model_environment','time':time.time(),'status':status,'real_model_qualified':False,'full_agent_e2e':'PENDING_MODEL_CONFIGURATION'}
(root/'.local/evidence').mkdir(parents=True,exist_ok=True);(root/'.local/evidence/smoke.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
