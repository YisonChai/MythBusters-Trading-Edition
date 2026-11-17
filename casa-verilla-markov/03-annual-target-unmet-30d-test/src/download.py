"""Public, cached metadata and true 300s history. No credentials/orders."""
from common import *
import shutil
START=ts(2026,9,17);TRAIN_END=ts(2026,10,17);TEST_START=ts(2026,10,18);END=ts(2026,11,17)
def wanted():
 rows=[]
 for t in range(START,END,3600):
  for a,n in [('btc','bitcoin'),('eth','ethereum')]:
   z=dt.datetime.fromtimestamp(t,ZoneInfo('America/New_York'));h=z.hour%12 or 12
   slug=f'{n}-up-or-down-{z.strftime("%B").lower()}-{z.day}-{z.year}-{h}{"am" if z.hour<12 else "pm"}-et'
   rows.append({'slug':slug,'asset':a,'start':t,'end':t+3600,'role':'train' if t<TRAIN_END else ('gap' if t<TEST_START else 'test')})
 return rows
def main():
 oldroot=Path('/workspace/casa-verilla/month-backtest');old={(w['asset'],w['start']):w for w in json.loads((oldroot/'raw/markets.json').read_text())} if (oldroot/'raw/markets.json').exists() else {}
 
 if (oldroot/'logs/requests.jsonl').exists():shutil.copy2(oldroot/'logs/requests.jsonl',ROOT/'logs/reused_month_requests.jsonl')
 ws=wanted();(RAW/'requested.json').write_text(json.dumps(ws,indent=2));todo=[w for w in ws if (w['asset'],w['start']) not in old];events=[];reuse=[]
 with cf.ThreadPoolExecutor(max_workers=4) as ex:
  fs=[]
  for k in range(0,len(todo),20):
   q=urllib.parse.urlencode([('limit','20')]+[('slug',w['slug']) for w in todo[k:k+20]])
   fs.append(ex.submit(get,'https://gamma-api.polymarket.com/events?'+q,f'events_new/{k:04d}.json'))
  for f in cf.as_completed(fs):
   d=f.result()
   if isinstance(d,list):events.extend(d)
 index={e['slug']:e for e in events};out=[];missing=[]
 for w in ws:
  prev=old.get((w['asset'],w['start']))
  if prev:
   m=prev['market'];out.append(dict(w,market=m,event_metadata=prev.get('event_metadata',{}),metadata_source='prior_month_snapshot'))
   for side in ['Up','Down']:
    src=oldroot/f'raw/prices/{m["id"]}_{side}.json';dst=RAW/f'prices/{m["id"]}_{side}.json'
    if src.exists():
     shutil.copy2(src,dst);reuse.append({'file':str(dst.relative_to(ROOT)),'original_file':str(src),'sha256':hashlib.sha256(src.read_bytes()).hexdigest()})
  else:
   e=index.get(w['slug']);mm=[m for m in e.get('markets',[]) if m.get('slug')==w['slug']] if e else []
   if len(mm)!=1:missing.append(w);continue
   out.append(dict(w,market=mm[0],event_metadata=e.get('eventMetadata',{}),metadata_source='new_gamma_request'))
 (RAW/'markets.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));(RAW/'missing.json').write_text(json.dumps(missing,indent=2));(ROOT/'logs/reused_files.json').write_text(json.dumps(reuse,indent=2));print('MARKETS',len(out),'MISSING',len(missing),'REUSED_PRICE_FILES',len(reuse),flush=True)
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
   if i%500==0:print('PRICES',i,'/',len(jobs),flush=True)
 for asset in ['BTC','ETH']:
  for n,t in enumerate(range(START,END,900*3600)):
   q=urllib.parse.urlencode({'symbol':asset+'USDT','interval':'1h','startTime':t*1000,'endTime':min(END,t+900*3600)*1000-1,'limit':1000})
   get('https://api.binance.com/api/v3/klines?'+q,f'reference/{asset}_{n}.json')
 print('DONE',flush=True)
if __name__=='__main__':main()
