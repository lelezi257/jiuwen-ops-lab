#!/usr/bin/env python3
"""Wait for actual HTTP readiness, CLI discovery and consistent running release."""
import json,time,urllib.request
client=urllib.request.build_opener(urllib.request.ProxyHandler({}));deadline=time.monotonic()+120;last='starting'
while time.monotonic()<deadline:
 try:
  with client.open('http://127.0.0.1:18780/api/status',timeout=10) as r:status=json.load(r)
  if all(status.get(x,{}).get('ok') for x in ['runner','delivery','evidence']) and status.get('release',{}).get('consistent'):
   print('Ready: http://127.0.0.1:18780 ; runner='+status['runner']['state']);break
  last='Components or release identity are not ready'
 except Exception as exc:last=type(exc).__name__
 time.sleep(1)
else:raise SystemExit('Readiness deadline exceeded: '+last+'; inspect scripts/lab logs')
