from common import *
def probe(t,a):
 z=dt.datetime.fromtimestamp(t,ZoneInfo('America/New_York'));h=z.hour%12 or 12;n={'btc':'bitcoin','eth':'ethereum'}[a]
 sl=f'{n}-up-or-down-{z.strftime("%B").lower()}-{z.day}-{z.year}-{h}{"am" if z.hour<12 else "pm"}-et'
 e=get('https://gamma-api.polymarket.com/events?'+urllib.parse.urlencode({'slug':sl}),f'probes/event_{a}_{t}.json')
 if not e:
  sl=sl.replace(f'-{z.year}-','-')
  e=get('https://gamma-api.polymarket.com/events?'+urllib.parse.urlencode({'slug':sl}),f'probes/event_noyear_{a}_{t}.json')
 if not isinstance(e,list) or not e:return {'asset':a,'t':t,'date':dt.datetime.fromtimestamp(t,dt.timezone.utc).isoformat(),'market':None}
 m=e[0]['markets'][0];outs=json.loads(m['outcomes']);tokens=json.loads(m['clobTokenIds']);q={'token_id':tokens[outs.index('Up')],'start':t-1200,'end':t+3900,'bucket_seconds':300}
 p=get('https://data-api.polymarket.com/v2/prices-history?'+urllib.parse.urlencode(q),f'probes/price_{a}_{t}.json')
 good=[x for x in p.get('data',[]) if x.get('resolution_seconds')==300]
 return {'asset':a,'t':t,'date':dt.datetime.fromtimestamp(t,dt.timezone.utc).isoformat(),'market':m['id'],'slug':e[0]['slug'],'up_300s_points':len(good),'min_timestamp':min([x['timestamp'] for x in good],default=None),'resolved':m.get('umaResolutionStatus'),'fee':m.get('feeSchedule')}
if __name__=='__main__':
 times=[ts(2025,10,17),ts(2025,11,15),ts(2025,12,15)]+[ts(2026,m,15) for m in range(1,12)]
 times+= [ts(2026,9,k) for k in [1,10,14,16,17,18,19,20,21,22,24,26,28,30]]
 jobs=sorted(set((t,a) for t in times for a in ['btc','eth']))
 with cf.ThreadPoolExecutor(max_workers=3) as ex:
  out=list(ex.map(lambda x:probe(*x),jobs))
 (RAW/'probe_summary.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2),flush=True)
 for repo in ['ywf1112/polymarket-btc-updown','aliplayer1/polymarket-crypto-updown','SII-WANGZJ/Polymarket_data']:
  d=get('https://huggingface.co/api/datasets/'+repo+'?blobs=true','probes/hf_'+repo.split('/')[0]+'.json')
  print('HF',repo,[(x['rfilename'],x.get('size')) for x in d.get('siblings',[])],flush=True)
