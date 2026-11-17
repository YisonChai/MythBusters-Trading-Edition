"""Offline absorbing sparse/hierarchical Markov study. No network/wallet/order code."""
from pathlib import Path
import bisect,collections,csv,datetime as dt,hashlib,json,math
import numpy as np
R=Path(__file__).resolve().parents[1];RAW=R/'raw';OUT=R/'results';OUT.mkdir(exist_ok=True)
def utc(y,m,d):return int(dt.datetime(y,m,d,tzinfo=dt.timezone.utc).timestamp())
START=utc(2026,9,30);FIT_END=utc(2026,10,23);VAL_START=utc(2026,10,24);TRAIN_END=utc(2026,10,30);TEST_START=utc(2026,10,31);END=utc(2026,11,7)
MODELS=['market','small','medium','large'];STRATEGIES=['edge05_p87','edge05_no_filter','edge03_band','favorite_fixed'];COSTS=['zero','fees','plus1','delay5_plus2','double_fees'];ASSETS=['all','btc','eth'];CAPITAL=10000.;SHARES=100.
def iso(t):return dt.datetime.fromtimestamp(int(t),dt.timezone.utc).isoformat()
def stamp(s):return int(dt.datetime.fromisoformat(s.replace('Z','+00:00')).timestamp()) if s else None
def bucket(q):return max(0,min(19,int(q*20)))
def save(name,rows,fields=None):
 rows=list(rows);fields=fields or (list(rows[0]) if rows else ['none'])
 with (OUT/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
def fee(q,rate,exp=1):return round(SHARES*rate*(q*(1-q))**exp,5)
def getpoints(path):
 d=json.loads(path.read_text()) if path.exists() else {};out={};bad=collections.Counter()
 for x in d.get('data',[]):
  if x.get('resolution_seconds')!=300:bad['excluded_resolution_'+str(x.get('resolution_seconds'))]+=1;continue
  if not 0<float(x['price'])<1:bad['boundary_price']+=1;continue
  t=int(x['timestamp']);q=float(x['price'])
  assert t<1e11
  if t in out and out[t]!=q:raise ValueError('conflicting duplicate historical aggregate')
  out[t]=q
 return out,bad

def load():
 refs={}
 for asset in ['btc','eth']:
  dd={}
  for p in sorted((RAW/'reference').glob(asset.upper()+'_*.json')):
   for x in json.loads(p.read_text()):dd[int(x[0]//1000)]=x
  refs[asset]=dd
 markets=[];manifest=[];observations=[];pointquality=collections.Counter()
 for w in json.loads((RAW/'markets.json').read_text()):
  m=w['market'];mid=str(m['id']);reason='';outcomes=json.loads(m['outcomes']);prices=list(map(float,json.loads(m['outcomePrices'])))
  if not m.get('closed') or m.get('umaResolutionStatus')!='resolved' or outcomes!=['Up','Down'] or sorted(prices)!=[0.,1.]:reason='not_binary_resolved'
  if stamp(m.get('eventStartTime'))!=w['start'] or stamp(m.get('endDate'))!=w['end']:reason=reason or 'event_time_mismatch_including_DST_slug_ambiguity'
  y=int(prices[0]==1);ref=refs[w['asset']].get(w['start']);check='missing_reference' if ref is None else ('match' if int(float(ref[4])>=float(ref[1]))==y else 'mismatch')
  if check=='mismatch':reason=reason or 'reference_winner_mismatch'
  if 'binance.com' not in m.get('resolutionSource',''):reason=reason or 'non_binance_hourly_rule'
  fs=m.get('feeSchedule',{});rate=fs.get('rate');exp=fs.get('exponent')
  if rate is None or exp is None:reason=reason or 'missing_fee_schedule'
  ps={}
  for side in ['Up','Down']:
   ps[side],b=getpoints(RAW/f'prices/{mid}_{side}.json');pointquality.update(b)
  obs={}
  for k in range(1,12):
   t=w['start']+k*300;rawt=t-300
   # No forward fill: demand the exact 4 consecutive aggregate buckets.
   times=[rawt-j*300 for j in [3,2,1,0]]
   if rawt not in ps['Down'] or not all(z in ps['Up'] for z in times):continue
   hist=[ps['Up'][z] for z in times];deltas=np.diff(hist)
   o={'k':k,'t':t,'raw_ts':rawt,'available_ts':rawt+300,'up':hist[-1],'down':ps['Down'][rawt],'momentum':hist[-1]-hist[-2],'volatility':float(np.std(deltas)),'asset':w['asset'],'state_price':bucket(hist[-1]),'all_four_raw_times':';'.join(map(str,times))}
   obs[k]=o
  close=stamp(m.get('closedTime')) or w['end']+3600;settle=max(close,w['end']);available=max(settle,w['end']+3600)
  if len(obs)<6:reason=reason or 'less_than_6_fresh_feature_rows'
  if w['role']=='train' and available>=TEST_START:reason=reason or 'training_label_not_ready'
  row={'market_id':mid,'slug':w['slug'],'asset':w['asset'],'role':w['role'],'start':w['start'],'end':w['end'],'start_utc':iso(w['start']),'end_utc':iso(w['end']),'settle':settle,'label_available':available,'y_up':y,'reference_check':check,'rule':m.get('description'),'resolution_source':m.get('resolutionSource'),'fee_rate':rate,'fee_exponent':exp,'fee_snapshot_updated_at':m.get('updatedAt'),'fee_historical_certainty':'metadata_snapshot_not_immutable_historical_audit','observations':len(obs),'excluded_reason':reason}
  manifest.append(row)
  if reason:continue
  markets.append(dict(w,id=mid,y=y,rate=float(rate),exponent=float(exp),settle=settle,label_available=available,obs=obs))
  for o in obs.values():observations.append(dict(market_id=mid,role=w['role'],y_up=y,label_available=available,**o))
 save('markets.csv',manifest);save('exclusions.csv',[x for x in manifest if x['excluded_reason']],list(manifest[0]));save('observations.csv',observations)
 (OUT/'point_quality.json').write_text(json.dumps(pointquality,indent=2))
 return markets,manifest

def state(o,arch):
 k=o['k'];i=bucket(o['up'])
 if arch=='small':return (k,i)
 if arch=='medium':return (k,i,int(np.searchsorted([-.02,.02],o['momentum'],side='right')),int(o['volatility']>=.03))
 return (k,i,int(np.searchsorted([-.1,-.02,.02,.1],o['momentum'],side='right')),int(np.searchsorted([.02,.06],o['volatility'],side='right')),0 if o['asset']=='btc' else 1)

class Chain:
 def __init__(self,markets,arch,alpha=10,min_count=5):
  self.arch=arch;self.alpha=alpha;self.min_count=min_count;self.counts=collections.Counter();self.transitions=collections.defaultdict(collections.Counter);self.h={};self.nmarkets=len(markets)
  pc=np.zeros((12,20,20));tn=np.zeros(20);ty=np.zeros(20);reg=np.zeros((20,20))
  for w in markets:
   for k,o in sorted(w['obs'].items()):
    s=state(o,arch);i=bucket(o['up']);self.counts[s]+=1
    if k==11:
     self.transitions[s]['WIN' if w['y'] else 'LOSE']+=1;tn[i]+=1;ty[i]+=w['y']
    elif k+1 in w['obs']:
     no=w['obs'][k+1];j=bucket(no['up']);pc[k,i,j]+=1;reg[i,j]+=1;self.transitions[s][state(no,arch)]+=1
  mids=(np.arange(20)+.5)/20;self.base=np.zeros((12,20));self.base[11]=(ty+10*mids)/(tn+10)
  for k in range(10,0,-1):
   Q=(pc[k]+10*np.eye(20))/(pc[k].sum(axis=1)[:,None]+10);self.base[k]=Q@self.base[k+1]
  self.reg_n=reg.sum(axis=1);self.reg=(reg+10*np.eye(20))/(reg.sum(axis=1)[:,None]+10)
  self.outn={s:sum(v.values()) for s,v in self.transitions.items()}
  for s in sorted(self.counts,key=lambda s:-s[0]):
   base=float(self.base[s[0],s[1]]);trans=self.transitions.get(s,{});n=sum(trans.values())
   if arch=='small' or n<min_count:self.h[s]=base;continue
   val=0.
   for z,c in trans.items():
    h=1. if z=='WIN' else (0. if z=='LOSE' else self.h.get(z,float(self.base[z[0],z[1]])))
    val+=c*h
   self.h[s]=(val+alpha*base)/(n+alpha)
 def predict(self,o):
  s=state(o,self.arch);i=s[1];j=int(np.argmax(self.reg[i]));n=self.outn.get(s,0)
  p=float(self.base[s[0],i]) if self.arch=='small' else self.h.get(s,float(self.base[s[0],i]));fallback=self.arch!='small' and n<self.min_count
  return {'p':p,'persistence':float(self.reg[j,j]),'regime_support':int(self.reg_n[i]),'state':json.dumps(s,separators=(',',':')),'state_count':int(self.counts.get(s,0)),'out_count':n,'fallback':int(fallback),'seen_state':int(s in self.counts)}
 def diag(self):
  a=np.array(list(self.counts.values()));theory={'small':220,'medium':1320,'large':6600}[self.arch]
  return {'model':self.arch,'alpha':self.alpha,'min_count':self.min_count,'theoretical_states':theory,'visited_states':len(a),'visited_pct':100*len(a)/theory,'count_min':int(a.min()),'count_median':float(np.median(a)),'count_p90':float(np.quantile(a,.9)),'count_max':int(a.max()),'states_ge_min_count':sum(self.outn.get(s,0)>=self.min_count for s in self.counts),'training_markets':self.nmarkets}

def metrics(probs,ys):
 p=np.clip(np.array(probs),1e-6,1-1e-6);y=np.array(ys)
 return {'brier':float(np.mean((p-y)**2)),'logloss':float(np.mean(-y*np.log(p)-(1-y)*np.log(1-p)))} if len(p) else {'brier':None,'logloss':None}

def choose(strategy,o,p,market=False):
 if strategy=='favorite_fixed':
  if o['k']!=1:return None
  side='Up' if o['up']>=o['down'] else 'Down';return side,p['p'] if side=='Up' else 1-p['p']
 if market or p['regime_support']<30:return None
 eu=p['p']-o['up'];ed=1-p['p']-o['down'];side='Up' if eu>=ed else 'Down';prob=p['p'] if side=='Up' else 1-p['p'];q=o[side.lower()]
 if prob-q<(.03 if strategy=='edge03_band' else .05):return None
 if strategy!='edge05_no_filter' and p['persistence']<.87:return None
 if strategy=='edge03_band' and not .83<=q<=.97:return None
 return side,prob

def planned(signals,cost):
 rows=[];skips=collections.Counter()
 for s in signals:
  q=s['q_observed'];t=s['signal_ts']
  if cost=='plus1':q+=.01
  if cost=='delay5_plus2':
   if s['q_next'] is None:skips['missing_next_5m_price']+=1;continue
   q=max(q,s['q_next'])+.02;t+=300
  if not 0<q<1 or t>=s['end_ts']:skips['invalid_cost_or_after_expiry']+=1;continue
  ff=0 if cost=='zero' else fee(q,s['fee_rate']*(2 if cost=='double_fees' else 1),s['fee_exponent']);cashcost=SHARES*q+ff;pay=SHARES*s['won']
  rows.append(dict(s,execution_ts=t,execution_utc=iso(t),q_entry=q,shares=SHARES,fee=ff,cost=cashcost,payout=pay,gross_pnl=SHARES*(s['won']-q),net_pnl=pay-cashcost,slippage_cost=SHARES*(q-s['q_observed']),cost_scenario=cost,executable_net_pnl=None,execution_assumption='HISTORICAL_PRICE_PROXY_NO_BID_ASK_DEPTH'))
 return rows,skips

def ledger(signals,cost):
 plans,skips=planned(signals,cost);entry=collections.defaultdict(list);mature=collections.defaultdict(list)
 for x in plans:entry[x['execution_ts']].append(x)
 for x in plans:mature[x['settle_ts']].append(x)
 cash=CAPITAL;eq=CAPITAL;peak=CAPITAL;maxdd=0.;reserved=0.;maxreserved=0.;active={};trades=[];curve=[{'t':TEST_START,'cash':cash,'equity':eq,'drawdown':0.,'reserved':0.}]
 for t in sorted(set(entry)|set(mature)):
  # Batch settlement before entries. Never create artificial same-second intermediate drawdowns.
  closing=[x for x in mature.get(t,[]) if x['market_id'] in active]
  cash+=sum(x['payout'] for x in closing);eq+=sum(x['net_pnl'] for x in closing);reserved-=sum(x['cost'] for x in closing)
  for x in closing:
   active.pop(x['market_id']);x['cash_after_settlement_batch']=cash;x['equity_after_settlement_batch']=eq
  for x in sorted(entry.get(t,[]),key=lambda x:x['market_id']):
   if cash+1e-9<x['cost']:skips['insufficient_cash']+=1;continue
   assert x['market_id'] not in active
   cash-=x['cost'];reserved+=x['cost'];active[x['market_id']]=x;trades.append(x);x['cash_after_entry']=cash;x['equity_after_entry']=eq
  maxreserved=max(maxreserved,reserved);peak=max(peak,eq);maxdd=max(maxdd,peak-eq)
  if TEST_START<=t:curve.append({'t':t,'cash':cash,'equity':eq,'drawdown':peak-eq,'reserved':max(0.,reserved)})
 finalt=max(END,max((x['settle_ts'] for x in trades),default=END))
 if curve[-1]['t']<finalt:curve.append({'t':finalt,'cash':cash,'equity':eq,'drawdown':peak-eq,'reserved':max(0.,reserved)})
 assert not active and abs(cash-eq)<1e-6 and abs(cash-CAPITAL-sum(x['net_pnl'] for x in trades))<1e-6
 n=len(trades);summary={'trades':n,'wins':sum(x['won'] for x in trades),'win_rate':sum(x['won'] for x in trades)/n if n else None,'gross_pnl':sum(x['gross_pnl'] for x in trades),'fees':sum(x['fee'] for x in trades),'net_pnl':sum(x['net_pnl'] for x in trades),'initial':CAPITAL,'final_equity':eq,'return_pct':100*(eq/CAPITAL-1),'max_drawdown':maxdd,'max_reserved':maxreserved,'skips':dict(skips),'executable_net_pnl':None,'equity_basis':'realized_PnL_open_positions_at_all_in_cost_not_mark_to_market','curve_end':finalt}
 return trades,curve,summary

def main():
 ws,manifest=load();train=[w for w in ws if w['role']=='train'];fit=[w for w in train if w['start']<FIT_END and w['label_available']<VAL_START];valid=[w for w in train if VAL_START<=w['start']<TRAIN_END];test=[w for w in ws if w['role']=='test']
 assert all(w['label_available']<TEST_START for w in train);assert not {w['id'] for w in train}&{w['id'] for w in test}
 roles={'train_full':train,'internal_fit':fit,'validation':valid,'test':test};split=[{'split':k,'markets':len(v),'first_start':iso(min(w['start'] for w in v)),'last_end':iso(max(w['end'] for w in v)),'last_label_available':iso(max(w['label_available'] for w in v))} for k,v in roles.items()];save('splits.csv',split)
 validation=[];selected={};fit_models={}
 for arch in ['small','medium','large']:
  options=[(10,5)] if arch=='small' else [(10,5),(50,15)]
  for alpha,mn in options:
   mo=Chain(fit,arch,alpha,mn);ps=[];ys=[]
   for w in valid:
    for o in w['obs'].values():ps.append(mo.predict(o)['p']);ys.append(w['y'])
   met=metrics(ps,ys);validation.append(dict(model=arch,alpha=alpha,min_count=mn,observations=len(ys),**met))
  best=min([x for x in validation if x['model']==arch],key=lambda x:(x['brier'],-x['alpha']));selected[arch]={'alpha':best['alpha'],'min_count':best['min_count']};fit_models[arch]=Chain(train,arch,**selected[arch])
 # Market model competes in validation too; champion chosen without test metrics.
 validation_market=metrics([o['up'] for w in valid for o in w['obs'].values()],[w['y'] for w in valid for o in w['obs'].values()]);validation.append(dict(model='market',alpha=0,min_count=0,observations=sum(len(w['obs']) for w in valid),**validation_market))
 bests=[min([x for x in validation if x['model']==a],key=lambda x:x['brier']) for a in MODELS];champion=min(bests,key=lambda x:x['brier'])['model'];save('validation_candidates.csv',validation)
 diagnostics=[];staterecords=[]
 for a,mo in fit_models.items():
  d=mo.diag();diagnostics.append(d)
  for s,n in sorted(mo.counts.items()):staterecords.append({'model':a,'state':json.dumps(s),'sample_count':n,'out_count':mo.outn.get(s,0),'fitted_terminal_up':mo.h[s]})
 save('training_states.csv',staterecords)
 predictions=[];signals=[]
 for w in sorted(test,key=lambda x:(x['start'],x['id'])):
  for arch in MODELS:
   seen=set()
   for k,o in sorted(w['obs'].items()):
    base=fit_models['small'].predict(o);p=dict(base,p=o['up'],fallback=0,seen_state=1) if arch=='market' else fit_models[arch].predict(o)
    predictions.append({'market_id':w['id'],'asset':w['asset'],'model':arch,'t':o['t'],'k':k,'y_up':w['y'],'market_up':o['up'],'raw_ts':o['raw_ts'],'available_ts':o['available_ts'],'momentum':o['momentum'],'volatility':o['volatility'],**p})
    for strategy in STRATEGIES:
     if strategy in seen:continue
     z=choose(strategy,o,p,arch=='market')
     if z is None:continue
     seen.add(strategy);side,prob=z;no=w['obs'].get(k+1)
     signals.append({'market_id':w['id'],'market_url':'https://polymarket.com/event/'+w['slug'],'asset':w['asset'],'product':'1h','model':arch,'strategy':strategy,'signal_ts':o['t'],'signal_utc':iso(o['t']),'end_ts':w['end'],'end_utc':iso(w['end']),'settle_ts':w['settle'],'settle_utc':iso(w['settle']),'side':side,'p_model':prob,'p_up':p['p'],'persistence':p['persistence'],'state':p['state'],'state_sample_count':p['state_count'],'fallback':p['fallback'],'q_observed':o[side.lower()],'q_next':no[side.lower()] if no else None,'fee_rate':w['rate'],'fee_exponent':w['exponent'],'y_up':w['y'],'won':w['y'] if side=='Up' else 1-w['y']})
 save('predictions.csv',predictions);save('signals.csv',signals)
 for d in diagnostics:
  pp=[x for x in predictions if x['model']==d['model']];d.update(test_rows=len(pp),test_seen_ratio=sum(x['seen_state'] for x in pp)/len(pp),test_fallback_ratio=sum(x['fallback'] for x in pp)/len(pp))
 save('state_diagnostics.csv',diagnostics)
 scores=[];cal=[]
 for arch in MODELS:
  for asset in ASSETS:
   pp=[x for x in predictions if x['model']==arch and (asset=='all' or x['asset']==asset)];scores.append(dict(model=arch,asset=asset,observations=len(pp),**metrics([x['p'] for x in pp],[x['y_up'] for x in pp])))
   for j in range(10):
    rr=[x for x in pp if j/10<=x['p']<(j+1)/10 or j==9 and x['p']==1]
    cal.append({'model':arch,'asset':asset,'bin':j,'n':len(rr),'mean_predicted':float(np.mean([x['p'] for x in rr])) if rr else None,'actual_up':float(np.mean([x['y_up'] for x in rr])) if rr else None})
 save('prediction_metrics.csv',scores);save('calibration.csv',cal)
 groups={};resultrows=[];tradecsv=[];curvecsv=[]
 for arch in MODELS:
  for asset in ASSETS:
   for strategy in STRATEGIES:
    ss=[x for x in signals if x['model']==arch and x['strategy']==strategy and (asset=='all' or x['asset']==asset)]
    for cost in COSTS:
     key='|'.join([arch,asset,strategy,cost]);trades,curve,s=ledger(ss,cost);met=next(x for x in scores if x['model']==arch and x['asset']==asset);s.update(brier=met['brier'],logloss=met['logloss']);groups[key]={'summary':s,'trades':trades,'curve':[[x[k] for k in ['t','cash','equity','drawdown','reserved']] for x in curve]}
     resultrows.append(dict(model=arch,asset=asset,strategy=strategy,cost=cost,**s))
     tradecsv.extend(dict(group=key,**x) for x in trades);curvecsv.extend(dict(group=key,**x) for x in curve)
 save('results.csv',resultrows);save('trades.csv',tradecsv);save('equity_curves.csv',curvecsv)
 meta={'train_start':START,'train_end':TRAIN_END,'fit_end':FIT_END,'validation_start':VAL_START,'test_start':TEST_START,'test_end':END,'initial':CAPITAL,'shares':SHARES,'bar_seconds':300,'champion_from_validation':champion,'chosen_params':selected,'splits':split,'market_count':len(ws),'manifest_count':len(manifest),'exclusions':len([x for x in manifest if x['excluded_reason']]),'theoretical_states':{'small':220,'medium':1320,'large':6600},'test_previously_evaluated':False,'test_note':'此前未评估该测试段收益，早于前次11月11至17日数据；本研究未按测试结果调参。','limitations':['仅BTC/ETH一小时产品；真实5分钟桶，不是5分钟合约','历史价格代理，不含bid/ask或深度，不保证成交','费率按合约元数据快照，不是完整历史费率审计','持续率一步为5分钟，不能直接等同前次1分钟持续率','已实现权益，未到期按全成本保留，非盯市','5分钟合约无法取得本实验所需的完整30天分钟级特征','市场价自比较的阈值策略没有概率优势，故不交易']}
 payload={'meta':meta,'diagnostics':diagnostics,'validation':validation,'scores':scores,'calibration':cal,'groups':groups}
 (OUT/'dashboard_data.json').write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':'),allow_nan=False));(OUT/'run_summary.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
 print(json.dumps(meta,ensure_ascii=False,indent=2));print('MAIN FEES ALL')
 for a in MODELS:
  for st in STRATEGIES:
   s=groups['|'.join([a,'all',st,'fees'])]['summary'];print(a,st,s['trades'],round(s['net_pnl'],2),'Brier',s['brier'])
if __name__=='__main__':main()
