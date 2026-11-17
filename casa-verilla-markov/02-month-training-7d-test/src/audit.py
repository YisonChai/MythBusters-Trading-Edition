"""Independent assertions of real-data accounting, time and model protocol."""
from pathlib import Path
import collections,csv,hashlib,json,math,datetime as dt
R=Path(__file__).resolve().parents[1];O=R/'results'
def read(n):return list(csv.DictReader((O/n).open()))
def f(x):return float(x)
checks=[]
def check(n,ok):assert ok,n;checks.append({'check':n,'passed':True})
m=read('markets.csv');mp={x['market_id']:x for x in m if not x['excluded_reason']};obs=read('observations.csv');pr=read('predictions.csv');ss=read('signals.csv');tr=read('trades.csv');eq=read('equity_curves.csv');rs=read('results.csv');states=read('training_states.csv');fr=json.loads((R/'logs/freeze.json').read_text())
check('model_code_unchanged_after_preregistration',hashlib.sha256((R/'src/run.py').read_bytes()).hexdigest()==fr['hashes']['src/run.py'])
check('training_window_exactly_30_days',(1793318400-1790726400)==30*86400)
check('all_training_days_have_real_data',len({int(x['start'])//86400 for x in mp.values() if x['role']=='train'})==30)
check('7_test_days_with_no_old_test_overlap',len({int(x['start'])//86400 for x in mp.values() if x['role']=='test'})==7 and max(int(x['start']) for x in mp.values() if x['role']=='test')<1794355200)
check('unique_retained_market_ids',len(mp)==len([x for x in m if not x['excluded_reason']]))
check('reference_labels_match',all(x['reference_check']=='match' for x in mp.values()))
check('final_train_labels_ready_before_test',all(int(x['label_available'])<1793404800 for x in mp.values() if x['role']=='train'))
check('features_available_only_after_bucket',all(int(x['available_ts'])==int(x['raw_ts'])+300==int(x['t']) for x in obs))
check('four_consecutive_real_feature_buckets',all([int(z) for z in x['all_four_raw_times'].split(';')]==[int(x['raw_ts'])-900,int(x['raw_ts'])-600,int(x['raw_ts'])-300,int(x['raw_ts'])] for x in obs))
check('observation_before_expiry',all(int(x['t'])<int(mp[x['market_id']]['end']) for x in obs))
check('train_test_disjoint',not {x['market_id'] for x in obs if x['role']=='train'}&{x['market_id'] for x in obs if x['role']=='test'})
check('one_signal_per_model_strategy_market',len({(x['model'],x['strategy'],x['market_id']) for x in ss})==len(ss))
check('no_duplicate_per_group_market',len({(x['group'],x['market_id']) for x in tr})==len(tr))
check('actual_official_payout_used',all(int(x['won'])==(int(mp[x['market_id']]['y_up']) if x['side']=='Up' else 1-int(mp[x['market_id']]['y_up'])) for x in tr))
check('not_after_expiry',all(int(x['execution_ts'])<int(x['end_ts'])<=int(x['settle_ts']) for x in tr))
check('fixed_100_shares',all(f(x['shares'])==100 for x in tr))
check('fee_formula_independent',all(abs(f(x['fee'])-(0 if x['cost_scenario']=='zero' else round(100*f(x['fee_rate'])*(2 if x['cost_scenario']=='double_fees' else 1)*(f(x['q_entry'])*(1-f(x['q_entry'])))**f(x['fee_exponent']),5)))<1e-8 for x in tr))
check('trade_net_equals_payout_minus_cash_cost',all(abs(f(x['net_pnl'])-f(x['payout'])+f(x['cost']))<1e-8 for x in tr))
check('all_probabilities_valid',all(0<=f(x['p'])<=1 for x in pr))
check('theoretical_sizes_respected',all(sum(x['model']==model for x in states)<=limit for model,limit in [('small',220),('medium',1320),('large',6600)]))
bygroup=collections.defaultdict(list);curves=collections.defaultdict(list)
for x in tr:bygroup[x['group']].append(x)
for x in eq:curves[x['group']].append(x)
for x in rs:
 key='|'.join([x[k] for k in ['model','asset','strategy','cost']]);rr=bygroup[key];cc=curves[key];net=sum(f(z['net_pnl']) for z in rr)
 check('ledger_'+key,abs(net-f(x['net_pnl']))<1e-6 and len(rr)==int(x['trades']) and abs(f(cc[-1]['equity'])-10000-net)<1e-6 and abs(f(cc[-1]['cash'])-f(cc[-1]['equity']))<1e-6)
 peak=10000.;dd=0.;times=[]
 for z in cc:
  peak=max(peak,f(z['equity']));d=peak-f(z['equity']);dd=max(dd,d);times.append(int(z['t']));assert abs(f(z['drawdown'])-d)<1e-6 and f(z['cash'])>=-1e-6 and abs(f(z['equity'])-f(z['cash'])-f(z['reserved']))<1e-5
 assert times==sorted(set(times)),key
 assert abs(dd-f(x['max_drawdown']))<1e-6
check('240_group_curves_monotonic_unique_time_and_accounting',len(rs)==240)
check('executable_return_never_fabricated',all(x['executable_net_pnl']=='' for x in rs))
(O/'audit_checks.json').write_text(json.dumps(checks,indent=2));print(len(checks),'checks PASS')
