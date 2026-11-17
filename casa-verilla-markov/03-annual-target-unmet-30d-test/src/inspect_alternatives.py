from common import *
def binary(url,p):
 p=RAW/p;p.parent.mkdir(parents=True,exist_ok=True)
 if not p.exists():
  res=subprocess.run(['curl','-L','-sS','--max-time','90','-w','\n%{http_code}',url],capture_output=True)
  body,_,status=res.stdout.rpartition(b'\n');code=int(status) if status.isdigit() else 0
  with (ROOT/'logs/alternative_requests.jsonl').open('a') as f:f.write(json.dumps({'url':url,'retrieved_at':dt.datetime.now(dt.timezone.utc).isoformat(),'status':code,'file':str(p.relative_to(ROOT)),'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest()})+'\n')
  if code!=200:return None
  p.write_bytes(body)
 return p
if __name__=='__main__':
 import pyarrow.parquet as pq
 out=[]
 for name in ['ywf1112','aliplayer1']:
  meta=json.loads((RAW/f'probes/hf_{name}.json').read_text());repo=meta['id'];rev=meta['sha']
  paths=[x['rfilename'] for x in meta['siblings'] if x['rfilename'] in ['README.md','data/markets.parquet'] or (x['rfilename'].startswith('data/prices/') and '/timeframe=1-hour/' in x['rfilename'] and ('crypto=BTC/' in x['rfilename'] or 'crypto=ETH/' in x['rfilename']))]
  for path in paths:
   p=binary(f'https://huggingface.co/datasets/{repo}/resolve/{rev}/'+urllib.parse.quote(path,safe='/='),f'alternatives/{name}/'+path)
   if p and p.suffix=='.parquet':
    pf=pq.ParquetFile(p);fields=pf.schema_arrow.names;times=[k for k in fields if k in ['timestamp','start_ts','end_ts']]
    tab=pf.read(columns=times).to_pydict();row={'repo':repo,'revision':rev,'file':path,'rows':pf.metadata.num_rows,'schema':str(pf.schema_arrow),'time_ranges':{k:[min(v),max(v)] for k,v in tab.items() if v}}
    out.append(row);print(row,flush=True)
 (RAW/'alternative_coverage.json').write_text(json.dumps(out,indent=2))
