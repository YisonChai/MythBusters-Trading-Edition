"""Public, cached, read-only history downloads. No credentials, wallet or trades."""
import concurrent.futures as cf, datetime as dt, hashlib,json,pathlib,subprocess,time,threading,urllib.parse
from zoneinfo import ZoneInfo
ROOT=pathlib.Path(__file__).resolve().parents[1];RAW=ROOT/'raw'; LOCK=threading.Lock(); RATE=threading.Lock();last=[0.]
START=int(dt.datetime(2026,11,11,tzinfo=dt.timezone.utc).timestamp());END=START+6*86400

def get(url,rel):
 p=RAW/rel;p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():return json.loads(p.read_text())
 for attempt in range(4):
  with RATE:
   delay=max(0,.09-(time.monotonic()-last[0]));time.sleep(delay);last[0]=time.monotonic()
  r=subprocess.run(['curl','--silent','--show-error','--max-time','35','--write-out','\n%{http_code}',url],capture_output=True)
  body,_,status=r.stdout.rpartition(b'\n');code=int(status) if status.isdigit() else 0
  entry={'url':url,'retrieved_at':dt.datetime.now(dt.timezone.utc).isoformat(),'http_status':code,'attempt':attempt,'file':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(body).hexdigest()}
  with LOCK:
   with (ROOT/'logs/download_manifest.jsonl').open('a') as f:f.write(json.dumps(entry)+'\n')
  if code==200:
   try:d=json.loads(body)
   except Exception:d=None
   if d is not None:p.write_bytes(body);return d
  if code in (401,403):
   (p.with_suffix('.error')).write_bytes(body);return {'download_error':code,'body':body.decode(errors='replace')[:1000]}
  if code not in (0,429,500,502,503,504):return {'download_error':code}
  time.sleep(2**attempt)
 return {'download_error':code}

def slugs():
 rows=[]
 for dur in [15,60]:
  for t in range(START,END,dur*60):
   for asset,name in [('btc','bitcoin'),('eth','ethereum')]:
    if dur==15:s=f'{asset}-updown-15m-{t}'
    else:
     z=dt.datetime.fromtimestamp(t,ZoneInfo('America/New_York'));h=z.hour%12 or 12;s=f'{name}-up-or-down-{z.strftime("%B").lower()}-{z.day}-{z.year}-{h}{"am" if z.hour<12 else "pm"}-et'
    rows.append({'slug':s,'start':t,'end':t+dur*60,'duration':dur,'asset':asset})
 return rows

def main():
 wanted=slugs();(RAW/'requested_markets.json').write_text(json.dumps(wanted,indent=2));events=[]
 with cf.ThreadPoolExecutor(max_workers=4) as ex:
  futures=[]
  for k in range(0,len(wanted),20):
   q=[('limit','20')]+[('slug',r['slug']) for r in wanted[k:k+20]]
   url='https://gamma-api.polymarket.com/events?'+urllib.parse.urlencode(q)
   futures.append(ex.submit(get,url,f'events/batch_{k:04d}.json'))
  for f in cf.as_completed(futures):
   d=f.result()
   if isinstance(d,list):events.extend(d)
 index={e['slug']:e for e in events};markets=[];missing=[]
 for w in wanted:
  e=index.get(w['slug'])
  if not e:missing.append(w);continue
  mm=[m for m in e.get('markets',[]) if m.get('slug')==w['slug']]
  if len(mm)!=1:missing.append(w);continue
  markets.append(dict(w,market=mm[0],event_metadata=e.get('eventMetadata',{}),event_id=e['id']))
 (RAW/'markets.json').write_text(json.dumps(markets,ensure_ascii=False,indent=2));(RAW/'missing_markets.json').write_text(json.dumps(missing,indent=2))
 print('MARKETS',len(markets),'missing',len(missing),flush=True)
 jobs=[]
 for w in markets:
  m=w['market'];outs=json.loads(m['outcomes']);tokens=json.loads(m['clobTokenIds'])
  for side in ['Up','Down']:
   if side not in outs:continue
   tok=tokens[outs.index(side)]
   q=urllib.parse.urlencode({'token_id':tok,'start':w['start']-120,'end':w['end']+180,'bucket_seconds':60})
   jobs.append(('https://data-api.polymarket.com/v2/prices-history?'+q,f'prices/{m["id"]}_{side}.json'))
 with cf.ThreadPoolExecutor(max_workers=4) as ex:
  fs=[ex.submit(get,u,r) for u,r in jobs]
  for i,f in enumerate(cf.as_completed(fs),1):
   f.result()
   if i%200==0:print('PRICES',i,'/',len(jobs),flush=True)
 # Real fills demonstrate available coverage; not assumed to provide depth or a fill for our orders.
 sample=[]
 for dur in [15,60]:
  for asset in ['btc','eth']:
   sample += [w for w in markets if w['duration']==dur and w['asset']==asset][::max(1,len([w for w in markets if w['duration']==dur and w['asset']==asset])//5)][:5]
 for w in sample:
  m=w['market'];q=urllib.parse.urlencode({'condition':m['conditionId'],'limit':100})
  get('https://data-api.polymarket.com/v2/trades?'+q,f'trades/{m["id"]}.json')
 for a in ['BTC','ETH']:
  q=urllib.parse.urlencode({'symbol':a+'USDT','interval':'1h','startTime':START*1000,'endTime':END*1000-1,'limit':1000})
  get('https://api.binance.com/api/v3/klines?'+q,f'reference/{a}_1h.json')
 print('DONE',flush=True)
if __name__=='__main__':main()
