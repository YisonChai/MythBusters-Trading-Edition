"""Read-only public history, cached and rate-limited; no credentials or orders."""
from pathlib import Path
import concurrent.futures as cf,datetime as dt,hashlib,json,subprocess,threading,time,urllib.parse
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parents[1];RAW=ROOT/'raw';LOCK=threading.Lock();RATE=threading.Lock();last=[0.]
def ts(y,m,d):return int(dt.datetime(y,m,d,tzinfo=dt.timezone.utc).timestamp())
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
