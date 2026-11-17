"""Two prespecified 15-day test halves; never used for model selection."""
from run import *
def main():
 signals=list(csv.DictReader((OUT/'signals.csv').open()));pred=list(csv.DictReader((OUT/'predictions.csv').open()));out=[];metrics_rows=[]
 floatfields=['p_model','p_up','persistence','q_observed','fee_rate','fee_exponent']
 intfields=['signal_ts','end_ts','settle_ts','won','y_up']
 for s in signals:
  for k in floatfields:s[k]=float(s[k])
  for k in intfields:s[k]=int(s[k])
  s['q_next']=float(s['q_next']) if s['q_next'] else None
 midpoint=TEST_START+15*86400
 for half,lo,hi in [('first15',TEST_START,midpoint),('last15',midpoint,END)]:
  for model in MODELS:
   for asset in ASSETS:
    pp=[p for p in pred if p['model']==model and (asset=='all' or p['asset']==asset) and lo<=int(p['t'])<hi]
    mm=metrics([float(x['p']) for x in pp],[int(x['y_up']) for x in pp]);metrics_rows.append(dict(half=half,model=model,asset=asset,start=lo,end=hi,observations=len(pp),**mm))
    for strategy in STRATEGIES:
     ss=[s for s in signals if s['model']==model and s['strategy']==strategy and (asset=='all' or s['asset']==asset) and lo<=s['signal_ts']<hi]
     for cost in COSTS:
      tr,curve,s=ledger(ss,cost);out.append(dict(half=half,model=model,asset=asset,strategy=strategy,cost=cost,**s))
 save('half_results.csv',out);save('half_prediction_metrics.csv',metrics_rows)
 actual=list(csv.DictReader((OUT/'trades.csv').open()));groups=list(csv.DictReader((OUT/'results.csv').open()));cohorts=[]
 for g in groups:
  key='|'.join(g[k] for k in ['model','asset','strategy','cost'])
  for half,lo,hi in [('first15',TEST_START,midpoint),('last15',midpoint,END)]:
   rr=[x for x in actual if x['group']==key and lo<=int(x['signal_ts'])<hi]
   cohorts.append(dict(half=half,model=g['model'],asset=g['asset'],strategy=g['strategy'],cost=g['cost'],trades=len(rr),net_pnl=sum(float(x['net_pnl']) for x in rr),fees=sum(float(x['fee']) for x in rr),basis='whole_month_actual_fills_grouped_by_signal_time_not_cash_reset'))
 save('half_actual_cohorts.csv',cohorts);print('HALVES',len(out),len(metrics_rows),'ACTUAL_COHORTS',len(cohorts))
if __name__=='__main__':main()
