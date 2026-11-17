"""Independent assertions of real-data accounting, time and model protocol."""
from pathlib import Path
import collections,csv,hashlib,json,math,datetime as dt,ast
from run import START,TRAIN_END,TEST_START,END,VAL_START,FIT_END
R=Path(__file__).resolve().parents[1];O=R/'results'
def read(n):return list(csv.DictReader((O/n).open()))
def f(x):return float(x)
checks=[]
def check(n,ok):assert ok,n;checks.append({'check':n,'passed':True})
m=read('markets.csv');mp={x['market_id']:x for x in m if not x['excluded_reason']};obs=read('observations.csv');pr=read('predictions.csv');ss=read('signals.csv');tr=read('trades.csv');eq=read('equity_curves.csv');rs=read('results.csv');states=read('training_states.csv');fr=json.loads((R/'logs/freeze.json').read_text())
check('model_code_unchanged_after_preregistration',hashlib.sha256((R/'src/run.py').read_bytes()).hexdigest()==fr['run_py_sha256'])
check('actual_training_window_exactly_30_days',(TRAIN_END-START)==30*86400)
check('all_training_days_have_real_data',len({int(x['start'])//86400 for x in mp.values() if x['role']=='train'})==30)
check('30_test_days_after_training_with_buffer',len({int(x['start'])//86400 for x in mp.values() if x['role']=='test'})==30 and TEST_START-TRAIN_END==86400)
check('unique_retained_market_ids',len(mp)==len([x for x in m if not x['excluded_reason']]))
check('reference_labels_match',all(x['reference_check']=='match' for x in mp.values()))
check('final_train_labels_ready_before_test',all(int(x['label_available'])<TEST_START for x in mp.values() if x['role']=='train'))
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
core=['bucket','fee','getpoints','state','Chain','metrics','choose','planned','ledger']
def asts(path):
 tree=ast.parse(path.read_text());return {x.name:ast.dump(x,include_attributes=False) for x in tree.body if isinstance(x,(ast.FunctionDef,ast.ClassDef))}
a0=asts(R/'docs/prior_model_baseline.py');a1=asts(R/'src/run.py')
check('all_9_core_algorithms_identical_to_prior_model',all(a0[k]==a1[k] for k in core))
check('protocol_hash_unchanged',hashlib.sha256((R/'研究协议.md').read_bytes()).hexdigest()==fr['protocol_sha256'])
check('internal_fit_labels_before_validation',all(int(x['label_available'])<VAL_START for x in mp.values() if x['role']=='train' and int(x['start'])<FIT_END))
check('DST_market_times_verified_against_official',all(int(x['end'])-int(x['start'])==3600 for x in mp.values()))
idx=json.loads((R/'raw/prior_research_index.json').read_text());prev=set(idx['evaluated_ids']);reuse=read('test_reuse.csv')
check('all_seen_market_flags_match_previous_real_prediction_ids',all(int(x['prior_evaluated'])==int(x['market_id'] in prev) for x in reuse))
av=json.loads((O/'availability.json').read_text());check('annual_target_not_falsely_completed',av['annual_training_completed'] is False and av['actual_training_days']<365)
check('test_labels_all_known_before_preregistration_time',max(int(w['label_available']) for w in mp.values() if w['role']=='test')<int(dt.datetime.fromisoformat(fr['frozen_at_taipei']).timestamp()))
check('requested_annual_market_count_correct',sum(int(x['requested_year_training_markets']) for x in read('monthly_coverage.csv'))==365*48)
h=read('half_results.csv')
check('480_half_combinations',len(h)==480)
for x in rs:
 rr=[z for z in h if all(z[k]==x[k] for k in ['model','asset','strategy','cost'])]
 binding=ast.literal_eval(x['skips']).get('insufficient_cash',0)>0
 check('halves_independent_cash_account_'+ '|'.join([x[k] for k in ['model','asset','strategy','cost']]),all(abs(f(z['final_equity'])-10000-f(z['net_pnl']))<1e-6 for z in rr) and (binding or (sum(int(z['trades']) for z in rr)==int(x['trades']) and abs(sum(f(z['net_pnl']) for z in rr)-f(x['net_pnl']))<1e-6)))
cohorts=read('half_actual_cohorts.csv')
for x in rs:
 rr=[z for z in cohorts if all(z[k]==x[k] for k in ['model','asset','strategy','cost'])]
 check('whole_month_half_cohorts_'+ '|'.join([x[k] for k in ['model','asset','strategy','cost']]),sum(int(z['trades']) for z in rr)==int(x['trades']) and abs(sum(f(z['net_pnl']) for z in rr)-f(x['net_pnl']))<1e-6)
raw={str(w['market']['id']):w['market'] for w in json.loads((R/'raw/markets.json').read_text())}
check('retained_products_all_closed_and_resolved',all(raw[mid]['closed'] and raw[mid]['umaResolutionStatus']=='resolved' for mid in mp))
check('winner_matches_original_official_market_payout',all(int(w['y_up'])==int(float(json.loads(raw[mid]['outcomePrices'])[0])==1) for mid,w in mp.items()))
def stamp(s):return int(dt.datetime.fromisoformat(s.replace('Z','+00:00')).timestamp())
check('exact_official_market_start_end_and_DST_alignment',all(stamp(raw[mid]['eventStartTime'])==int(w['start']) and stamp(raw[mid]['endDate'])==int(w['end']) for mid,w in mp.items()))
check('fees_match_each_market_metadata_snapshot',all(abs(f(w['fee_rate'])-raw[mid]['feeSchedule']['rate'])<1e-12 and f(w['fee_exponent'])==raw[mid]['feeSchedule']['exponent'] for mid,w in mp.items()))
check('all_300s_histories_paginated_to_end',all(not json.loads(p.read_text()).get('pagination',{}).get('has_more',False) for p in (R/'raw/prices').glob('*.json')))
reused=json.loads((R/'logs/reused_files.json').read_text());check('reused_original_raw_hashes_unchanged',all(hashlib.sha256((R/x['file']).read_bytes()).hexdigest()==x['sha256'] for x in reused))
(O/'audit_checks.json').write_text(json.dumps(checks,indent=2));print(len(checks),'checks PASS')
