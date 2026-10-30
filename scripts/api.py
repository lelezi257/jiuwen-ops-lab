#!/usr/bin/env python3
import json,sys,urllib.request
from pathlib import Path
root=Path(__file__).resolve().parents[1];action=sys.argv[1]
path='/api/investigate' if action=='investigate' else '/api/experiment/'+action
request=urllib.request.Request('http://127.0.0.1:18780'+path,data=b'{}',headers={'Content-Type':'application/json','Authorization':'Bearer '+(root/'.local/secrets/control_token').read_text().strip()},method='POST')
with urllib.request.urlopen(request,timeout=650) as r:print(json.dumps(json.load(r),ensure_ascii=False,indent=2))
