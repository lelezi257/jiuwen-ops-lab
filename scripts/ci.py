#!/usr/bin/env python3
"""Run candidate in disposable containers. No candidate Python runs on host."""
import argparse,json,os,secrets,subprocess,tempfile,time,uuid
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--candidate',default='.');p.add_argument('--trusted',default='.');p.add_argument('--oracle-host-path');a=p.parse_args()
candidate=Path(a.candidate).resolve();trusted=Path(a.trusted).resolve();tag='lab-test-'+uuid.uuid4().hex[:10];net=tag;password=secrets.token_hex(20)
def run(argv,**kw):return subprocess.run(argv,check=True,**kw)
try:
 run(['docker','network','create','--internal',net],stdout=subprocess.DEVNULL)
 run(['docker','build','-f',str(trusted/'deploy/Order.Dockerfile'),'-t',tag,str(candidate)])
 with tempfile.TemporaryDirectory() as temp:
  secret=Path(temp)/'password';secret.write_text(password);secret.chmod(0o644)
  run(['docker','run','-d','--name',tag+'-db','--network',net,'--network-alias','db','-e','POSTGRES_USER=orders','-e','POSTGRES_DB=orders','-e','POSTGRES_PASSWORD='+password,'postgres:16.9-alpine'],stdout=subprocess.DEVNULL)
  for _ in range(60):
   r=subprocess.run(['docker','exec',tag+'-db','pg_isready','-U','orders'],capture_output=True)
   if r.returncode==0:break
   time.sleep(1)
  run(['docker','run','-d','--name',tag+'-app','--network',net,'--network-alias','candidate','--read-only','--tmpfs','/tmp','--tmpfs','/logs','-e','DB_PASSWORD='+password,tag],stdout=subprocess.DEVNULL)
  # Oracle code comes from the trusted checkout, mounted read-only.
  for _ in range(60):
   r=subprocess.run(['docker','exec',tag+'-app','python','-c',"import urllib.request;urllib.request.urlopen('http://localhost:8080/health')"],capture_output=True)
   if r.returncode==0:break
   time.sleep(1)
  run(['docker','run','--rm','--network',net,'--read-only','--tmpfs','/tmp','--mount',f"type=bind,src={a.oracle_host_path or str(trusted/'contracts')},dst=/oracle,readonly",tag,'python','/oracle/check_http.py','http://candidate:8080'])
  run(['docker','run','--rm','--network','none','--read-only','--tmpfs','/tmp','--mount',f'type=bind,src={candidate},dst=/candidate,readonly','-w','/candidate',tag,'python','-m','unittest','discover','-s','tests/order','-v'])
finally:
 for name in [tag+'-app',tag+'-db']:subprocess.run(['docker','rm','-f',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 subprocess.run(['docker','network','rm',net],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 subprocess.run(['docker','image','rm',tag],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
