"""Durable product state machine; no model loop here."""
import asyncio,json,os,threading,time
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI,Depends,HTTPException,Request
from fastapi.responses import FileResponse,StreamingResponse
from lab.common import *
init_store();mutex=threading.RLock();DELIVERY='http://delivery:8080';PROBE='http://probe:8080'
TERMINAL={'DELIVERY_ACCEPTANCE_PASSED','RESOLVED_FIXED','RECOVERED_ROLLBACK','NEEDS_HUMAN','CANCELLED','NO_ACTION'}
AGENT_STATES={'REPAIR_QUEUED','REPAIRING','VERIFY_AGENT_QUEUED','VERIFY_AGENT_RUNNING'}
def events(cid):return sorted((x for x in all_objects('event') if x['case_id']==cid),key=lambda x:x['time'])
def event(cid,kind,data,key=None):
 key=key or ident('event')
 if get('event',key):return
 put('event',key,{'id':key,'case_id':cid,'time':now(),'kind':kind,'data':data})
def save(c,state=None,detail=None):
 existing=get('case',c['id'])
 if existing and existing.get('cancelled'):
  c['cancelled']=True
  if state:state='CANCELLED' if existing['state']=='CANCELLED' else existing['state']
 if state:
  c['state']=state;event(c['id'],'state',{'state':state,'detail':detail})
 c['updated_at']=now();put('case',c['id'],c);return c

def create_case(trigger):
 with mutex:
  cur=call(DELIVERY,'/ops/current',{})
  if not cur['consistent']:raise HTTPException(409,'Running version is not registered consistently')
  release=cur['ledger']
  if trigger.get('source')=='alertmanager':
   relevant=[a for a in trigger['alerts'] if not a.get('labels',{}).get('release_id') or a['labels']['release_id']==release['release_id']]
   if not relevant:return {'ignored':True,'reason':'Alert belongs to an older release'}
   trigger={**trigger,'alerts':relevant}
  existing=next((c for c in all_objects('case') if c['observed_release']==release['release_id']),None)
  if existing:return existing
  cid=ident('case');c={'id':cid,'created_at':now(),'state':'REPAIR_QUEUED','observed_release':release['release_id'],'observed_sha':release['source_sha'],'trigger':trigger,'cancelled':False,'attempt':0,'feedback':None}
  save(c,'REPAIR_QUEUED','Waiting for runner / real model configuration');return c


def transition(c):
 cid=c['id'];state=c['state']
 if c['cancelled'] or state in TERMINAL or state in AGENT_STATES:return
 if state=='CI_PENDING':
  status=call(DELIVERY,'/ops/pr-status',{'case_id':cid});c['ci']=status
  if status['state']=='passed':save(c,'READY_TO_MERGE')
  elif status['state']=='failed' and c['attempt']<int(os.getenv('LAB_REPAIR_LIMIT','2'))+1:
   c['feedback']=status;save(c,'REPAIR_QUEUED','CI failed; new bounded real-model repair attempt')
  elif status['state'] in ['failed','stale']:save(c,'NEEDS_HUMAN',status)
  elif status['state']=='merged':save(c,'NEEDS_HUMAN','PR merged outside product authorization; reconcile explicitly')
  else:save(c)
 elif state=='READY_TO_MERGE':
  if os.getenv('LAB_AUTO_DELIVER','false').lower()=='true' or c.get('approved'):save(c,'MERGING')
 elif state=='MERGING':
  c['merge']=call(DELIVERY,'/ops/merge',{'case_id':cid});save(c,'BUILDING')
 elif state=='BUILDING':
  c['build']=call(DELIVERY,'/ops/build',{'case_id':cid},timeout=300)
  if c['build']['state']=='ready':save(c,'DEPLOYING')
  elif c['build']['state']=='failed':save(c,'NEEDS_HUMAN','Merged source build failed; main/experiment branch fact retained')
  else:save(c)
 elif state=='DEPLOYING':
  try:
   c['deployment']=call(DELIVERY,'/ops/deploy',{'case_id':cid,'expected_release':c['observed_release']},timeout=240);save(c,'VERIFYING')
  except Exception as exc:c['failure']=str(exc);save(c,'ROLLING_BACK')
 elif state=='VERIFYING':
  try:
   cur=call(DELIVERY,'/ops/current',{})
   if not cur['consistent']:raise RuntimeError('Runtime / release ledger differs')
   report=call(PROBE,'/verify',{k:cur['ledger'][k] for k in ['release_id','source_sha','image_digest']},timeout=600)
   c['verification']=report
   if report['passed']:
    if c.get('kind')=='engineering_acceptance':
     call(DELIVERY,'/ops/mark-good',{'verification_id':report['verification_id']});save(c,'DELIVERY_ACCEPTANCE_PASSED','Engineering chain only; human-authored patch, no model or Agent qualification')
    else:save(c,'VERIFY_AGENT_QUEUED','Independent contract passed; new Jiuwen session reads deployment evidence')
   else:save(c,'ROLLING_BACK','Candidate did not recover business paths')
  except Exception as exc:
   c['failure']='Independent verification failed: '+str(exc)[:1000];save(c,'ROLLING_BACK',c['failure'])
 elif state=='ROLLING_BACK':
  cur=call(DELIVERY,'/ops/current',{})
  c['rollback']=call(DELIVERY,'/ops/rollback',{'expected_release':cur['ledger']['release_id']},timeout=240)
  report=call(PROBE,'/verify',{k:c['rollback']['ledger'][k] for k in ['release_id','source_sha','image_digest']},timeout=600);c['rollback_verification']=report
  save(c,'RECOVERED_ROLLBACK' if report['passed'] else 'NEEDS_HUMAN')

async def scheduler():
 while True:
  for c in all_objects('case'):
   try:
    if c['state'] in ['REPAIRING','VERIFY_AGENT_RUNNING'] and now()-c.get('lease_at',now())>90:
     c['cancelled']=True;save(c,'NEEDS_HUMAN','Runner lease lost; stop and reconcile existing effects, no automatic replay')
    elif c['state'] not in TERMINAL:await asyncio.to_thread(transition,c)
   except Exception as exc:
    event(c['id'],'controller_error',{'message':str(exc)[:1500]})
    if c['state'] in ['MERGING','DEPLOYING','ROLLING_BACK']:save(c,'NEEDS_HUMAN','Action requires reconciliation: '+str(exc)[:600])
   await asyncio.sleep(.1)
  await asyncio.sleep(3)
@asynccontextmanager
async def lifespan(app):
 task=asyncio.create_task(scheduler());yield;task.cancel()
app=FastAPI(lifespan=lifespan)
@app.get('/')
def index():return FileResponse('/app/web/index.html')
@app.get('/health')
def health():return {'ok':True,'role':'our-product-control','model_loop':'official-jiuwen-child-process'}
@app.get('/api/status')
def status():
 result={}
 for name,url in [('runner','http://runner:8080/health'),('delivery','http://delivery:8080/health'),('evidence','http://evidence:8080/health')]:
  try:
   with __import__('httpx').Client(timeout=3,trust_env=False) as client:result[name]=client.get(url).json()
  except Exception:result[name]={'ok':False}
 try:result['release']=call(DELIVERY,'/ops/current',{})
 except Exception as exc:result['release']={'error':str(exc)}
 return result
@app.get('/api/cases')
def list_cases():return sorted(all_objects('case'),key=lambda x:x['created_at'],reverse=True)
@app.get('/api/cases/{cid}')
def case(cid:str):
 c=get('case',cid)
 if not c:raise HTTPException(404,'Case not found')
 return c
@app.get('/api/cases/{cid}/events')
def list_events(cid:str):return events(cid)
@app.get('/api/cases/{cid}/stream')
def stream(cid:str,request:Request,after:str=''):
 async def generate():
  seen=after
  while not await request.is_disconnected():
   rows=events(cid)
   if seen:
    matches=[i for i,x in enumerate(rows) if x['id']==seen];rows=rows[matches[0]+1:] if matches else rows
   for row in rows:
    seen=row['id'];yield 'id: '+seen+'\nevent: timeline\ndata: '+json.dumps(row,ensure_ascii=False)+'\n\n'
   yield ': heartbeat\n\n';await asyncio.sleep(2)
 return StreamingResponse(generate(),media_type='text/event-stream')
@app.post('/api/investigate',dependencies=[Depends(operator)])
def investigate():return create_case({'source':'operator','time':now()})
@app.post('/alerts',dependencies=[Depends(operator)])
def alerts(body:dict):
 firing=[a for a in body.get('alerts',[]) if a.get('status')=='firing' and a.get('labels',{}).get('alertname')=='OrderNoCouponErrors']
 return create_case({'source':'alertmanager','alerts':firing}) if firing else {'ignored':True}
@app.post('/api/cases/{cid}/cancel',dependencies=[Depends(operator)])
def cancel(cid:str):
 with mutex:
  c=case(cid);c['cancelled']=True
  if c['state'] not in TERMINAL:save(c,'CANCELLED','Stop future actions; existing PR/merge/release facts remain')
  return c
@app.post('/api/cases/{cid}/approve',dependencies=[Depends(operator)])
def approve(cid:str):
 c=case(cid)
 if c['state']!='READY_TO_MERGE':raise HTTPException(409,'Not awaiting delivery authorization')
 c['approved']=True;save(c);return c
@app.post('/api/experiment/{action}',dependencies=[Depends(operator)])
def experiment(action:str,body:dict):
 if action=='bootstrap':return call(DELIVERY,'/ops/bootstrap',body,timeout=180)
 if action=='fault':return call(DELIVERY,'/ops/fault',{},timeout=600)
 if action=='baseline':
  cur=call(DELIVERY,'/ops/register',{});report=call(PROBE,'/verify',{k:cur['ledger'][k] for k in ['release_id','source_sha','image_digest']},timeout=600)
  if not report['passed']:raise HTTPException(409,'Baseline did not pass business contract')
  return call(DELIVERY,'/ops/mark-good',{'verification_id':report['verification_id']})
 raise HTTPException(404,'Unknown experiment action')
@app.get('/internal/cases/{cid}',dependencies=[Depends(worker)])
def internal_case(cid:str):return case(cid)
@app.post('/internal/claim',dependencies=[Depends(worker)])
def claim(body:dict):
 with mutex:
  if any(x['state'] in ['REPAIRING','VERIFY_AGENT_RUNNING'] for x in all_objects('case')):return None
  for c in all_objects('case'):
   if c['state'] not in ['REPAIR_QUEUED','VERIFY_AGENT_QUEUED'] or c['cancelled']:continue
   c['phase']='repair' if c['state']=='REPAIR_QUEUED' else 'verify';c['attempt']+=1;c['attempt_id']=ident('attempt');c['lease_at']=now();save(c,'REPAIRING' if c['phase']=='repair' else 'VERIFY_AGENT_RUNNING');return c
 return None
@app.post('/internal/cases/{cid}/heartbeat',dependencies=[Depends(worker)])
def heartbeat(cid:str,body:dict):
 with mutex:
  c=case(cid)
  if c.get('attempt_id')!=body['attempt_id']:raise HTTPException(409,'Attempt changed')
  c['lease_at']=now();save(c);return {'cancelled':c['cancelled'] or c['state'] in TERMINAL}
@app.post('/internal/cases/{cid}/event',dependencies=[Depends(worker)])
def record(cid:str,body:dict):
 c=case(cid)
 if c.get('attempt_id')!=body['attempt_id']:raise HTTPException(409,'Attempt changed')
 key=cid+':'+body['attempt_id']+':'+str(body.get('sequence',ident('s')));event(cid,body['kind'],body['data'],key);return {'ok':True}
@app.post('/internal/cases/{cid}/result',dependencies=[Depends(worker)])
def result(cid:str,body:dict):
 with mutex:
  c=case(cid)
  if c.get('attempt_id')!=body['attempt_id']:raise HTTPException(409,'Attempt changed')
  if c['cancelled'] or c['state'] in TERMINAL:return {'recorded':False,'reason':'Case already terminal'}
  event(cid,'sdk_result',body['result']);c['agent_result']=body['result']
  if body['result'].get('status')!='completed' or body['result'].get('exit_code')!=0:return save(c,'NEEDS_HUMAN','Official SDK run did not complete successfully')
  output=body['result'].get('output_json') or {}
  if output.get('needs_human'):return save(c,'NEEDS_HUMAN',output.get('finding'))
  for eid in output.get('evidence_ids',[]):
   fact=call('http://evidence:8080','/evidence/'+eid)
   if fact.get('case_id')!=cid:return save(c,'NEEDS_HUMAN','Evidence does not belong to this case')
  if not output.get('evidence_ids'):return save(c,'NEEDS_HUMAN','Actual evidence references required')
  if c['phase']=='repair':
   status=call(DELIVERY,'/ops/pr-status',{'case_id':cid});pr=status['pr']
   if output.get('pr_number')!=pr['number'] or output.get('candidate_sha')!=pr['head_sha']:return save(c,'NEEDS_HUMAN','Model output does not match actual broker PR')
   if not output.get('evidence_ids'):return save(c,'NEEDS_HUMAN','Evidence references required')
   c['pr']=pr;return save(c,'CI_PENDING')
  cur=call(DELIVERY,'/ops/current',{});report=c['verification']
  if not report['passed'] or not cur['consistent'] or cur['ledger']['release_id']!=report['release_id']:return save(c,'NEEDS_HUMAN','Runtime changed after verification')
  call(DELIVERY,'/ops/mark-good',{'verification_id':report['verification_id']});return save(c,'RESOLVED_FIXED')

@app.post('/api/engineering/start',dependencies=[Depends(operator)])
def engineering_start():
 with mutex:
  if any(c['state'] not in TERMINAL for c in all_objects('case')):raise HTTPException(409,'Cancel/finish other cases before isolated engineering acceptance')
  cur=call(DELIVERY,'/ops/current',{})
  if not cur['consistent']:raise HTTPException(409,'Release mismatch')
  cid=ident('engineering');c={'id':cid,'kind':'engineering_acceptance','created_at':now(),'state':'REPAIRING','observed_release':cur['ledger']['release_id'],'observed_sha':cur['ledger']['source_sha'],'trigger':{'source':'operator_engineering_acceptance'},'cancelled':False,'attempt':1,'attempt_id':ident('manual-attempt'),'lease_at':now(),'phase':'repair'}
  event(cid,'engineering_scope',{'model_calls':0,'patch_author':'human_script','not_agent_acceptance':True});return save(c,'REPAIRING')
@app.post('/api/engineering/{cid}/submit',dependencies=[Depends(operator)])
def engineering_submit(cid:str):
 c=case(cid)
 if c.get('kind')!='engineering_acceptance' or c['cancelled'] or c['state']!='REPAIRING':raise HTTPException(409,'Not an active engineering case')
 status=call(DELIVERY,'/ops/pr-status',{'case_id':cid});c['pr']=status['pr'];return save(c,'CI_PENDING','Human-authored candidate; real delivery acceptance only')

@app.post('/api/cases/{cid}/retry',dependencies=[Depends(operator)])
def retry(cid:str):
 with mutex:
  c=case(cid)
  if c['state'] not in ['NEEDS_HUMAN','CANCELLED'] or c.get('kind')=='engineering_acceptance':raise HTTPException(409,'Not a retriable Agent case')
  cur=call(DELIVERY,'/ops/current',{})
  if not cur['consistent'] or cur['runtime']['source_sha']!=c['observed_sha'] or c.get('merge'):raise HTTPException(409,'External state changed; investigate and reconcile before retry')
  c['cancelled']=False;c['attempt_id']=ident('retry-reservation');c['feedback']={'previous_result':c.get('agent_result'),'operator_retry':True};put('case',cid,c)
  return save(c,'REPAIR_QUEUED','Operator requested new attempt; prior attempts retained')
