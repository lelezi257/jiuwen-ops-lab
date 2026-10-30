#!/usr/bin/env python3
"""Generate the checked-in Compose deployment from a readable service map."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
base={'image':'jiuwen-ops-runtime:local','build':{'context':'.','dockerfile':'deploy/Dockerfile'},'restart':'unless-stopped','networks':['ops'],'read_only':True,'tmpfs':['/tmp'],'security_opt':['no-new-privileges:true'],'cap_drop':['ALL'],'environment':{'LAB_DATA':'/data'},'volumes':[]}
def service(module,volume,secrets=(),networks=('ops',),env=None):
 x={**base,'command':['python','-m','uvicorn','lab.'+module+':app','--host','0.0.0.0','--port','8080'],'volumes':[volume+':/data'],'secrets':list(secrets),'networks':list(networks),'environment':{**base['environment'],**(env or {})}};return x
s={}
s['control']=service('control','control',['control_token','runner_token'],env={'LAB_AUTO_DELIVER':'${LAB_AUTO_DELIVER:-true}','LAB_REPAIR_LIMIT':'${LAB_REPAIR_LIMIT:-2}'})
s['control']['ports']=['127.0.0.1:18780:8080']
s['evidence']=service('evidence','evidence',['runner_token','control_token'])
s['delivery']=service('delivery','delivery',['runner_token','control_token','github_token'],('ops','app'),{'GITHUB_REPOSITORY':'${GITHUB_REPOSITORY}','GITHUB_BRANCH':'${GITHUB_BRANCH:-lab-live}','LAB_TRUST_SHA':'${LAB_TRUST_SHA}','HOST_REPO':'${HOST_REPO}','HTTP_PROXY':'${HTTP_PROXY:-}','HTTPS_PROXY':'${HTTPS_PROXY:-}','NO_PROXY':'localhost,127.0.0.1,control,probe,order-api'})
s['delivery']['read_only']=False;s['delivery']['volumes']+=['work:/work','/var/run/docker.sock:/var/run/docker.sock'];s['delivery']['cap_drop']=[]
s['runner']=service('runner','runner',['runner_token'])
s['runner'].update(image='jiuwen-ops-runner:local',build={'context':'.','dockerfile':'deploy/Runner.Dockerfile'},env_file=['.local/model.env'])
s['runner']['volumes']+=['./.local/swarm:/config/swarm'];s['runner']['environment'].update({'API_BASE':'${API_BASE:-}','API_KEY':'${API_KEY:-}','MODEL_NAME':'${MODEL_NAME:-}'})
# Model values come ONLY from the per-service env_file, not global Compose env.
for key in ['API_BASE','API_KEY','MODEL_NAME']:s['runner']['environment'].pop(key)
s['probe']=service('probe','probe',['control_token'],('ops','app'),{'LAB_VERIFY_SECONDS':'${LAB_VERIFY_SECONDS:-60}','LAB_VERIFY_WINDOWS':'${LAB_VERIFY_WINDOWS:-2}','LAB_VERIFY_MIN_REQUESTS':'${LAB_VERIFY_MIN_REQUESTS:-30}'})
s['collector']={**base,'command':['python','-m','lab.collector'],'volumes':['collector:/data','logs:/logs:ro']}
s['db']={'image':'postgres:16.9-alpine','restart':'unless-stopped','networks':['app'],'environment':{'POSTGRES_USER':'orders','POSTGRES_DB':'orders','POSTGRES_PASSWORD_FILE':'/run/secrets/db_password'},'secrets':['db_password'],'volumes':['postgres:/var/lib/postgresql/data'],'healthcheck':{'test':['CMD-SHELL','pg_isready -U orders'],'interval':'3s','timeout':'3s','retries':30}}
s['order-api']={'image':'${ORDER_IMAGE:-jiuwen-order:bootstrap}','build':{'context':'.','dockerfile':'deploy/Order.Dockerfile','args':{'SOURCE_SHA':'${LAB_TRUST_SHA}'}},'container_name':'ops-order-api','restart':'unless-stopped','read_only':True,'tmpfs':['/tmp'],'networks':['app'],'ports':['127.0.0.1:18080:8080'],'secrets':['db_password'],'volumes':['logs:/logs'],'environment':{'RELEASE_ID':'release-baseline','IMAGE_DIGEST':'${ORDER_IMAGE:-bootstrap}'},'depends_on':{'db':{'condition':'service_healthy'}}}
s['prometheus']={'image':'prom/prometheus:v3.4.1','restart':'unless-stopped','networks':['ops','app'],'volumes':['./config/prometheus.yml:/etc/prometheus/prometheus.yml:ro','./config/alerts.yml:/etc/prometheus/alerts.yml:ro','prometheus:/prometheus'],'command':['--config.file=/etc/prometheus/prometheus.yml','--storage.tsdb.retention.time=3d']}
s['alertmanager']={'image':'prom/alertmanager:v0.28.1','restart':'unless-stopped','networks':['ops'],'volumes':['./config/alertmanager.yml:/etc/alertmanager/alertmanager.yml:ro'],'secrets':['control_token']}
s['loki']={'image':'grafana/loki:3.5.1','restart':'unless-stopped','networks':['ops'],'volumes':['./config/loki.yml:/etc/loki/config.yml:ro','loki:/loki'],'command':['-config.file=/etc/loki/config.yml']}
s['registry']={'image':'registry:2.8.3','restart':'unless-stopped','networks':['ops'],'ports':['127.0.0.1:5000:5000'],'volumes':['registry:/var/lib/registry']}
volumes=['control','evidence','delivery','runner','probe','collector','work','postgres','logs','prometheus','loki','registry']
compose={'name':'jiuwen-ops-lab','services':s,'volumes':{v:{} for v in volumes},'networks':{'ops':{},'app':{}},'secrets':{k:{'file':'.local/secrets/'+k} for k in ['control_token','runner_token','db_password','github_token']}}
(root/'compose.yaml').write_text(json.dumps(compose,ensure_ascii=False,indent=2)+'\n')
