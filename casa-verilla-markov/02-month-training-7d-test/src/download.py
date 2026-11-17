"""Read-only public history, cached and rate-limited; no credentials or orders."""
from pathlib import Path
import concurrent.futures as cf,datetime as dt,hashlib,json,subprocess,threading,time,urllib.parse
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parents[1];RAW=ROOT/'raw';LOCK=threading.Lock();RATE=threading.Lock();last=[0.]
def ts(y,m,d):return int(dt.datetime(y,m,d,tzinfo=dt.timezone.utc).timestamp())
START=ts(2026,9,30);TRAIN_END=ts(2026,10,30);TEST_START=ts(2026,10,31);END=ts(2026,11,7)
def get(url,rel):
 p=RAW/rel;p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():return json.loads(p.read_text())
 for attempt in range(4):
  with RATE:
   time.sleep(max(0,.09-(time.monotonic()-last[0])));last[0]=time.monotonic()
  r=subprocess.run(['curl','-sS','--max-time','35','-w','\n%{http_code}',url],capture_output=True)
  body,_,status=r.stdout.rpartition(b'\n');code=int(status) if status.isdigit() else 0
  row={'url':url,'retrieved_at':dt.datetime.now(dt.timezone.utc).isoformat(),'http_status':code,'attempt':attempt,'file':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(body).hexdigest()}
  with LOCK:
   with (ROOT/'logs/requests.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
  if code==200:
   try:d=json.loads(body)
   except Exception:d=None
   if d is not None:p.write_bytes(body);return d
  if code in [401,403]:p.with_suffix('.error').write_bytes(body);return {'download_error':code}
  if code not in [0,429,500,502,503,504]:p.with_suffix('.error').write_bytes(body);return {'download_error':code}
  time.sleep(2**attempt)
 return {'download_error':code}
def wanted():
 rows=[]
 for t in range(START,END,3600):
  for a,n in [('btc','bitcoin'),('eth','ethereum')]:
   z=dt.datetime.fromtimestamp(t,ZoneInfo('America/New_York'));h=z.hour%12 or 12
   slug=f'{n}-up-or-down-{z.strftime("%B").lower()}-{z.day}-{z.year}-{h}{"am" if z.hour<12 else "pm"}-et'
   rows.append({'slug':slug,'asset':a,'start':t,'end':t+3600,'role':'train' if t<TRAIN_END else ('gap' if t<TEST_START else 'test')})
 return rows

def main():
 ws=wanted();(RAW/'requested.json').write_text(json.dumps(ws,indent=2));events=[]
 with cf.ThreadPoolExecutor(max_workers=4) as ex:
  fs=[]
  for k in range(0,len(ws),20):
   q=urllib.parse.urlencode([('limit','20')]+[('slug',w['slug']) for w in ws[k:k+20]])
   fs.append(ex.submit(get,'https://gamma-api.polymarket.com/events?'+q,f'events/{k:04d}.json'))
  for f in cf.as_completed(fs):
   d=f.result()
   if isinstance(d,list):events.extend(d)
 index={e['slug']:e for e in events};out=[];missing=[]
 for w in ws:
  e=index.get(w['slug']);mm=[m for m in e.get('markets',[]) if m.get('slug')==w['slug']] if e else []
  if len(mm)!=1:missing.append(w);continue
  out.append(dict(w,market=mm[0],event_metadata=e.get('eventMetadata',{})))
 (RAW/'markets.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));(RAW/'missing.json').write_text(json.dumps(missing,indent=2));print('MARKETS',len(out),'missing',len(missing),flush=True)
 jobs=[]
 for w in out:
  m=w['market'];outs=json.loads(m['outcomes']);tokens=json.loads(m['clobTokenIds'])
  for side in ['Up','Down']:
   tok=tokens[outs.index(side)];q=urllib.parse.urlencode({'token_id':tok,'start':w['start']-1200,'end':w['end']+300,'bucket_seconds':300})
   jobs.append(('https://data-api.polymarket.com/v2/prices-history?'+q,f'prices/{m["id"]}_{side}.json'))
 with cf.ThreadPoolExecutor(max_workers=4) as ex:
  fs=[ex.submit(get,u,p) for u,p in jobs]
  for i,f in enumerate(cf.as_completed(fs),1):
   f.result()
   if i%250==0:print('PRICES',i,'/',len(jobs),flush=True)
 for asset in ['BTC','ETH']:
  for n,t in enumerate(range(START,END,900*3600)):
   q=urllib.parse.urlencode({'symbol':asset+'USDT','interval':'1h','startTime':t*1000,'endTime':min(END,t+900*3600)*1000-1,'limit':1000})
   get('https://api.binance.com/api/v3/klines?'+q,f'reference/{asset}_{n}.json')
 print('DONE',flush=True)
if __name__=='__main__':main()
