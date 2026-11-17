"""Coverage and researcher-exposure audit, independent of returns."""
from run import *
from calendar import monthrange

def prior_index():
 p=RAW/'prior_research_index.json'
 if p.exists():return json.loads(p.read_text())
 root=R.parent;ev=set();seen=set();sources=[]
 for rel in ['month-backtest/results/predictions.csv','backtest/results/all_predictions.csv']:
  f=root/rel;rows=list(csv.DictReader(f.open()));ids={x['market_id'] for x in rows};ev|=ids;sources.append({'file':str(f),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'rows':len(rows),'unique_ids':len(ids),'kind':'evaluated'})
 for rel in ['month-backtest/raw/markets.json','backtest/raw/markets.json']:
  f=root/rel;ids={str(x['market']['id']) for x in json.loads(f.read_text())};seen|=ids;sources.append({'file':str(f),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'unique_ids':len(ids),'kind':'downloaded'})
 out={'sources':sources,'evaluated_ids':sorted(ev),'downloaded_ids':sorted(seen)};p.write_text(json.dumps(out,indent=2));return out

def main():
 idx=prior_index();evaluated=set(idx['evaluated_ids']);downloaded=set(idx['downloaded_ids']);markets=list(csv.DictReader((OUT/'markets.csv').open()));rows=[]
 test=[w for w in markets if w['role']=='test' and not w['excluded_reason']]
 for w in test:rows.append({'market_id':w['market_id'],'asset':w['asset'],'start':w['start'],'start_utc':w['start_utc'],'prior_evaluated':int(w['market_id'] in evaluated),'prior_downloaded':int(w['market_id'] in downloaded)})
 save('test_reuse.csv',rows);daily=[]
 for t in range(TEST_START,END,86400):
  rr=[x for x in rows if t<=int(x['start'])<t+86400];daily.append({'day_start':t,'day_start_taipei':dt.datetime.fromtimestamp(t,dt.timezone(dt.timedelta(hours=8))).isoformat(),'markets':len(rr),'prior_evaluated':sum(x['prior_evaluated'] for x in rr),'prior_downloaded':sum(x['prior_downloaded'] for x in rr)})
 save('test_reuse_daily.csv',daily)
 full=len(rows);reuse={'test_markets':full,'prior_evaluated':sum(x['prior_evaluated'] for x in rows),'prior_downloaded':sum(x['prior_downloaded'] for x in rows),'evaluated_ratio':sum(x['prior_evaluated'] for x in rows)/full,'downloaded_ratio':sum(x['prior_downloaded'] for x in rows)/full,'evaluated_days':sum(x['prior_evaluated']>0 for x in daily),'downloaded_days':sum(x['prior_downloaded']>0 for x in daily),'total_days':30,'daily':daily}
 (OUT/'reuse_summary.json').write_text(json.dumps(reuse,indent=2))
 probes=json.loads((RAW/'probe_summary.json').read_text());coverage=[]
 req_start=utc(2025,10,17);req_end=TRAIN_END
 for year,mo in [(2025,k) for k in range(10,13)]+[(2026,k) for k in range(1,12)]:
  lo=utc(year,mo,1);hi=utc(year+int(mo==12),1 if mo==12 else mo+1,1);key=f'{year}-{mo:02}'
  requested=max(0,min(hi,req_end)-max(lo,req_start))//3600*2
  pp=[p for p in probes if lo<=p['t']<hi];mm=[w for w in markets if lo<=int(w['start'])<hi];good=[w for w in mm if not w['excluded_reason']]
  rp=[]
  for p in pp:
   if p.get('market'):
    e=json.loads((RAW/f'probes/event_{p["asset"]}_{p["t"]}.json').read_text())
    if not e:e=json.loads((RAW/f'probes/event_noyear_{p["asset"]}_{p["t"]}.json').read_text())
    rp.append(e[0]['markets'][0].get('resolutionSource','unknown'))
  coverage.append({'month':key,'requested_year_training_markets':requested,'probe_markets_found':sum(bool(x.get('market')) for x in pp),'probe_markets_tested':len(pp),'probe_with_300s':sum(x.get('up_300s_points',0)>0 for x in pp),'probe_fee_snapshots':';'.join(sorted(set('未知' if not x.get('fee') else str(x['fee']) for x in pp))),'probe_300s_points':sum(x.get('up_300s_points',0) for x in pp),'downloaded_markets':len(mm),'usable_training_markets':sum(w['role']=='train' for w in good),'usable_testing_markets':sum(w['role']=='test' for w in good),'excluded_markets':sum(bool(w['excluded_reason']) for w in mm),'actual_fee_rate_snapshots':';'.join(sorted(set(w['fee_rate'] for w in mm))),'actual_fee_exponents':';'.join(sorted(set(w['fee_exponent'] for w in mm))),'probe_resolution_sources':';'.join(sorted(set(rp))),'coverage_note':'探针数不是全月市场数；未抓取部分不能当已全面检查；月份以台北1日08:00划分'})
 save('monthly_coverage.csv',coverage)
 # Real histories before source retention are not replaced by coarse points or spot data.
 available={'requested_training_days':365,'actual_training_days':(TRAIN_END-START)//86400,'requested_training_markets':365*48,'actual_training_markets':sum(w['role']=='train' and not w['excluded_reason'] for w in markets),'earliest_verified_300s':min(p['min_timestamp'] for p in probes if p.get('min_timestamp') is not None),'official_probe_count':len(probes),'annual_training_completed':False,'coverage':coverage,'reuse':reuse}
 (OUT/'availability.json').write_text(json.dumps(available,ensure_ascii=False,indent=2));print('COVERAGE',available['actual_training_markets'],'REUSE',reuse['prior_evaluated'],reuse['prior_downloaded'])
if __name__=='__main__':main()
