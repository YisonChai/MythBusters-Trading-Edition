"""Deterministic offline proxy study. Run only after download.py. No network."""
import bisect,csv,datetime as dt,hashlib,heapq,json,math,pathlib
from collections import Counter
import numpy as np
ROOT=pathlib.Path(__file__).resolve().parents[1];RAW=ROOT/'raw';OUT=ROOT/'results'
START=int(dt.datetime(2026,11,11,tzinfo=dt.timezone.utc).timestamp());TEST=START+3*86400;END=START+6*86400
B=20;N=100.;INITIAL=10000.;MIN=30
VARIANTS=['terminal_e05_p87','terminal_e05_nofilter','terminal_e03_p87','terminal_e03_band','terminal_e05_band','literal_e05_p87','literal_e03_band','calibrated_e05','favorite_fixed','market_edge']
SCENARIOS=['quote0','fee_only','stress1','stress2_delay','fee_double']
def iso(t):return dt.datetime.fromtimestamp(t,dt.timezone.utc).isoformat()
def stamp(s):
 if not s:return None
 return int(dt.datetime.fromisoformat(s.replace('Z','+00:00')).timestamp())
def bucket(q):return max(0,min(B-1,int(q*B)))
def fee(n,q,rate,exponent=1):return round(n*rate*(q*(1-q))**exponent,5)
def writecsv(name,rows,fields=None):
 rows=list(rows)
 if not fields:fields=list(rows[0]) if rows else ['empty_reason']
 with (OUT/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
def pointseries(p,start,end):
 if not p.exists():return [],'missing_download'
 d=json.loads(p.read_text())
 if not isinstance(d,dict) or 'data' not in d:return [],'invalid_envelope'
 pts=[]
 for x in d['data']:
  if x.get('resolution_seconds')!=60:continue
  ts=x['timestamp'];q=x['price']
  if ts>1e11:raise AssertionError('milliseconds unexpectedly in price-history')
  if start-120<=ts<end and 0<q<1:pts.append((int(ts)+60,float(q),int(ts)))
 # Unique timestamps: accept exact duplicates, fail closed on conflicting values.
 grouped={}
 for t,q,rawt in pts:
  if t in grouped and grouped[t][1]!=q:return [],'conflicting_timestamp'
  grouped[t]=(t,q,rawt)
 return sorted(grouped.values()),''
def asof(pts,t):
 i=bisect.bisect_right([x[0] for x in pts],t)-1
 if i<0:return None
 x=pts[i]
 return x if t-x[0]<=90 else None

def load():
 raw=json.loads((RAW/'markets.json').read_text());ok=[];ex=[];quality=[];manifest=[]
 refs={}
 for a in ['btc','eth']:
  p=RAW/f'reference/{a.upper()}_1h.json'
  if p.exists():refs[a]={int(x[0]//1000):x for x in json.loads(p.read_text())}
 for w in raw:
  m=w['market'];mid=str(m['id']);reason='';outs=json.loads(m['outcomes']);op=list(map(float,json.loads(m['outcomePrices'])))
  if not m.get('closed') or m.get('umaResolutionStatus')!='resolved':reason='not_resolved'
  elif outs!=['Up','Down'] or sorted(op)!=[0.,1.]:reason='nonbinary_or_unsettled'
  elif stamp(m['endDate'])!=w['end']:reason='end_time_mismatch'
  elif stamp(m.get('eventStartTime'))!=w['start']:reason='event_start_mismatch'
  rate=m.get('feeSchedule',{}).get('rate');exp=m.get('feeSchedule',{}).get('exponent')
  if rate is None or exp is None:reason=reason or 'missing_fee_schedule'
  y=int(op[0]==1.);refcheck='not_available';meta=w.get('event_metadata',{})
  if w['duration']==15:
   if 'chain.link' not in m.get('resolutionSource',''):reason=reason or 'unexpected_resolution_source'
   if 'finalPrice' in meta and 'priceToBeat' in meta:
    ry=int(float(meta['finalPrice'])>=float(meta['priceToBeat']));refcheck='match' if ry==y else 'mismatch'
  else:
   if 'binance.com' not in m.get('resolutionSource',''):reason=reason or 'unexpected_resolution_source'
   rr=refs.get(w['asset'],{}).get(w['start'])
   if rr:refcheck='match' if int(float(rr[4])>=float(rr[1]))==y else 'mismatch'
  if refcheck=='mismatch':reason=reason or 'reference_settlement_mismatch'
  sides={};sideerr=[]
  for side in ['Up','Down']:
   sides[side],err=pointseries(RAW/f'prices/{mid}_{side}.json',w['start'],w['end'])
   if err:sideerr.append(side+':'+err)
  obs={}
  for k in range(1,w['duration']):
   t=w['start']+k*60;u=asof(sides['Up'],t);d=asof(sides['Down'],t)
   if u and d:obs[k]={'k':k,'t':t,'up':u[1],'down':d[1],'up_avail':u[0],'down_avail':d[0],'up_raw':u[2],'down_raw':d[2]}
  if len(obs)<max(5,w['duration']//2):reason=reason or 'insufficient_60s_observations'
  close=stamp(m.get('closedTime')) or w['end']+3600;settle=max(w['end'],close)
  manifest.append({'market_id':mid,'slug':w['slug'],'asset':w['asset'],'duration_min':w['duration'],'start_utc':iso(w['start']),'end_utc':iso(w['end']),'start_epoch_seconds':w['start'],'end_epoch_seconds':w['end'],'settle_epoch_seconds':settle,'label_available':max(settle,w['end']+3600),'up_payout':y,'resolution_source':m.get('resolutionSource'),'resolution_rule':m.get('description'),'reference_check':refcheck,'fee_rate':rate,'fee_exponent':exp,'fee_schedule_as_retrieved':json.dumps(m.get('feeSchedule')),'up_points':len(sides['Up']),'down_points':len(sides['Down']),'valid_observations':len(obs),'excluded_reason':reason,'download_issue':';'.join(sideerr)})
  if reason:ex.append({'market_id':mid,'slug':w['slug'],'reason':reason});continue
  ok.append(dict(w,id=mid,y=y,rate=float(rate),exponent=float(exp),settle=settle,label_available=max(settle,w['end']+3600),obs=obs))
 writecsv('market_manifest.csv',manifest);writecsv('exclusions.csv',ex,['market_id','slug','reason'])
 return ok,manifest

class Model:
 def __init__(self,train,D):
  self.D=D;counts=np.zeros((D,B,B));term_n=np.zeros(B);term_y=np.zeros(B);cn=np.zeros((D,B));cy=np.zeros((D,B));P=np.zeros((B,B))
  for w in train:
   for k,o in w['obs'].items():
    i=bucket(o['up']);cn[k,i]+=1;cy[k,i]+=w['y']
    nxt=w['obs'].get(k+1)
    if nxt:
     j=bucket(nxt['up']);counts[k,i,j]+=1;P[i,j]+=1
    if k==D-1:term_n[i]+=1;term_y[i]+=w['y']
  self.support=P.sum(axis=1);self.P=(P+10*np.eye(B))/(P.sum(axis=1)[:,None]+10)
  self.Pcounts=P.copy();self.cn=cn;self.cy=cy
  mids=(np.arange(B)+.5)/B;self.H=np.zeros((D,B));self.H[D-1]=(term_y+10*mids)/(term_n+10)
  for k in range(D-2,0,-1):
   Q=(counts[k]+10*np.eye(B))/(counts[k].sum(axis=1)[:,None]+10);self.H[k]=Q@self.H[k+1]
 def predict(self,o):
  i=bucket(o['up']);k=o['k'];j=int(np.argmax(self.P[i]));s=float(self.P[j,j]);ph=float(self.P[i,j]);lside='Up' if (j+.5)/B>=.5 else 'Down'
  cal=(self.cy[k,i]+20*o['up'])/(self.cn[k,i]+20)
  return {'p_terminal':float(self.H[k,i]),'p_calibrated':float(cal),'p_market':o['up'],'persistent':s,'state_support':int(self.support[i]),'state_bucket':i,'j_star':j,'literal_side':lside,'literal_probability':ph,'p_literal_up':ph if lside=='Up' else 1-ph}

def choose(variant,o,p):
 if variant=='market_edge':return None # Per-side market probability equals its own price by definition.
 if p['state_support']<MIN:return None
 if variant=='favorite_fixed':
  if o['k']!=2:return None
  side='Up' if o['up']>=o['down'] else 'Down';prob=o['up'] if side=='Up' else 1-o['up'];return side,prob,'fixed'
 if variant.startswith('literal'):
  side=p['literal_side'];prob=p['literal_probability']
 else:
  pu=p['p_calibrated'] if variant.startswith('calibrated') else (p['p_market'] if variant=='market_edge' else p['p_terminal'])
  edgeu=pu-o['up'];edged=(1-pu)-o['down'];side='Up' if edgeu>=edged else 'Down';prob=pu if side=='Up' else 1-pu
 q=o[side.lower()];eps=.03 if 'e03' in variant else .05
 if prob-q+1e-12<eps:return None
 if ('p87' in variant or 'band' in variant) and p['persistent']<.87:return None
 if 'band' in variant and not .83<=q<=.97:return None
 return side,prob,'threshold'

def portfolio(trades,scenario,rate_mult=1.):
 rows=[];cash=INITIAL;equity=INITIAL;peak=INITIAL;maxdd=0.;maxused=0.;pending=[];seq=0;skip=Counter()
 def settle_until(t):
  nonlocal cash,equity,peak,maxdd
  while pending and pending[0][0]<=t:
   _,_,cost,pay=heapq.heappop(pending);cash+=pay;equity+=pay-cost;peak=max(peak,equity);maxdd=max(maxdd,peak-equity)
 for tr in sorted(trades,key=lambda x:(x['t'],x['market_id'])):
  d=tr.copy();q=tr['q_observed'];when=tr['t'];adder=0.
  if scenario=='stress1':adder=.01
  if scenario=='stress2_delay':
   if tr['q_next'] is None:skip['no_delayed_quote']+=1;continue
   q=max(q,tr['q_next']);adder=.02;when+=60
  q+=adder
  if q>=1:skip['cost_above_payout']+=1;continue
  settle_until(when)
  f=0. if scenario=='quote0' else fee(N,q,tr['fee_rate']*(2 if scenario=='fee_double' else rate_mult),tr['fee_exponent'])
  cost=N*q+f
  if cash+1e-9<cost:skip['insufficient_cash']+=1;continue
  pay=N*tr['won'];cash-=cost;heapq.heappush(pending,(tr['settle_ts'],seq,cost,pay));seq+=1;maxused=max(maxused,sum(v[2] for v in pending))
  d.update(scenario=scenario,execution_ts=when,execution_utc=iso(when),q_scenario=q,shares=N,fee=f,cost=cost,payout=pay,raw_quote_gross=N*(tr['won']-tr['q_observed']),gross_pnl=N*(tr['won']-q),slippage_cost=N*(q-tr['q_observed']),net_pnl=pay-cost,executable_pnl='',execution_limitation='NO_HISTORICAL_BID_ASK_OR_DEPTH_PRICE_PROXY_ONLY')
  rows.append(d)
 settle_until(float('inf'))
 assert abs(cash-(INITIAL+sum(x['net_pnl'] for x in rows)))<1e-6
 assert abs(equity-cash)<1e-6
 return rows,{'trades':len(rows),'wins':sum(r['won'] for r in rows),'win_rate':float(np.mean([r['won'] for r in rows])) if rows else None,'brier_on_trades':float(np.mean([(r['p_model']-r['won'])**2 for r in rows])) if rows else None,'gross_pnl':sum(r['gross_pnl'] for r in rows),'fees':sum(r['fee'] for r in rows),'slippage_cost':sum(r['slippage_cost'] for r in rows),'net_pnl':sum(r['net_pnl'] for r in rows),'return_on_initial_pct':100*(cash/INITIAL-1),'max_realized_drawdown':maxdd,'max_concurrent_capital':maxused,'initial_capital':INITIAL,'final_cash':cash,'cost_skips':json.dumps(dict(skip)),'executable_net_pnl':None,'missing_reason':'No historical bid/ask depth or fill availability; these are scenario prices, not executable fills.'}

def main():
 OUT.mkdir(exist_ok=True);markets,manifest=load();predictions=[];signals=[];foldrows=[];modeldiag=[]
 for D in [15,60]:
  for day in range(3):
   cutoff=TEST+day*86400;train=[w for w in markets if w['duration']==D and w['label_available']<cutoff];test=[w for w in markets if w['duration']==D and cutoff<=w['start']<cutoff+86400]
   assert all(w['end']<cutoff and w['label_available']<cutoff for w in train)
   assert not {w['id'] for w in train}&{w['id'] for w in test}
   if not train:continue
   model=Model(train,D)
   foldrows.append({'duration_min':D,'fold':day,'fit_before_utc':iso(cutoff),'train_markets':len(train),'train_first_utc':iso(min(w['start'] for w in train)),'last_train_label_available_utc':iso(max(w['label_available'] for w in train)),'test_start_utc':iso(cutoff),'test_end_utc':iso(cutoff+86400),'test_markets':len(test)})
   for i in range(B):modeldiag.append({'duration_min':D,'fold':day,'bucket':i,'low':i/B,'high':(i+1)/B,'support':int(model.support[i]),'p_same':model.P[i,i],'row_max':max(model.P[i]),'literal_jstar':int(np.argmax(model.P[i]))})
   for w in sorted(test,key=lambda w:(w['start'],w['id'])):
    seen=set()
    for k,o in sorted(w['obs'].items()):
     assert o['up_avail']<=o['t'] and o['down_avail']<=o['t']<w['end']
     p=model.predict(o);base={'market_id':w['id'],'asset':w['asset'],'duration_min':D,'fold':day,'market_start':w['start'],'t':o['t'],'time_utc':iso(o['t']),'k':k,'up_quote':o['up'],'down_quote':o['down'],'y_up':w['y'],'up_point_raw_ts':o['up_raw'],'down_point_raw_ts':o['down_raw'],'up_point_available':o['up_avail'],'down_point_available':o['down_avail']}
     predictions.append(dict(base,**p))
     for v in VARIANTS:
      if v in seen:continue
      c=choose(v,o,p)
      if c is None:continue
      seen.add(v);side,prob,_=c;nexto=w['obs'].get(k+1)
      signals.append(dict(base,variant=v,side=side,p_model=prob,persistent=p['persistent'],support=p['state_support'],q_observed=o[side.lower()],q_next=nexto[side.lower()] if nexto else None,won=w['y'] if side=='Up' else 1-w['y'],fee_rate=w['rate'],fee_exponent=w['exponent'],settle_ts=w['settle']))
 writecsv('folds.csv',foldrows);writecsv('model_state_diagnostics.csv',modeldiag);writecsv('all_predictions.csv',predictions);writecsv('signals.csv',signals)
 summaries=[];alltrades=[]
 for D in [15,60]:
  pr=[p for p in predictions if p['duration_min']==D]
  for v in VARIANTS:
   trs=[t for t in signals if t['duration_min']==D and t['variant']==v]
   assert len({t['market_id'] for t in trs})==len(trs)
   for sc in SCENARIOS:
    rows,s=portfolio(trs,sc);alltrades+=rows;summaries.append(dict(duration_min=D,variant=v,scenario=sc,**s))
 writecsv('variant_results.csv',summaries);writecsv('trades.csv',alltrades)
 cal=[]
 for D in [15,60]:
  pr=[p for p in predictions if p['duration_min']==D]
  for mod in ['p_market','p_terminal','p_calibrated','p_literal_up']:
   for lo,hi in [(0,1)]+[(i/10,(i+1)/10) for i in range(10)]:
    rr=[r for r in pr if lo<=r[mod]<hi or hi==1 and r[mod]==1]
    cal.append({'duration_min':D,'model':mod,'probability_low':lo,'probability_high':hi,'observations':len(rr),'markets':len({r['market_id'] for r in rr}),'mean_probability':np.mean([r[mod] for r in rr]) if rr else None,'actual_up_rate':np.mean([r['y_up'] for r in rr]) if rr else None,'brier':np.mean([(r[mod]-r['y_up'])**2 for r in rr]) if rr else None,'semantic_warning':'one_step_state_probability_is_not_terminal_event_probability' if mod=='p_literal_up' else ''})
 writecsv('calibration.csv',cal)
 # Market-cluster bootstrap, not iid minute observations; N=1000 fixed seed.
 rng=np.random.default_rng(20261117);ci=[]
 for D in [15,60]:
  allids=sorted({p['market_id'] for p in predictions if p['duration_min']==D})
  for v in VARIANTS:
   rr=[r for r in alltrades if r['duration_min']==D and r['variant']==v and r['scenario']=='fee_only'];mp={r['market_id']:r['net_pnl'] for r in rr};a=np.array([mp.get(i,0.) for i in allids]);draw=rng.choice(a,size=(1000,len(a)),replace=True).sum(axis=1) if len(a) else np.array([0.])
   ci.append({'duration_min':D,'variant':v,'scenario':'fee_only','market_cluster_n':len(a),'net_pnl':a.sum(),'bootstrap_lo_2_5':np.quantile(draw,.025),'bootstrap_hi_97_5':np.quantile(draw,.975),'warning':'market bootstrap is descriptive; correlated BTC/ETH and just 3 test days invalidate strong significance claims'})
 writecsv('bootstrap_diagnostic.csv',ci)
 summary={'retained_markets':len(markets),'excluded':len(manifest)-len(markets),'test_markets':len({p['market_id'] for p in predictions}),'test_observations':len(predictions),'signal_count_all_variants':len(signals),'dataset_sha256':hashlib.sha256((RAW/'markets.json').read_bytes()).hexdigest(),'result_sha256':hashlib.sha256((OUT/'variant_results.csv').read_bytes()).hexdigest()}
 (OUT/'run_summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
 print('\nMAIN RESULTS fee_only')
 for r in summaries:
  if r['scenario']=='fee_only':print(r['duration_min'],r['variant'],r['trades'],round(r['net_pnl'],3),r['win_rate'])
if __name__=='__main__':main()
