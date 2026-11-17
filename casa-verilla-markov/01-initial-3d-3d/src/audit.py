"""Independent assertions against saved real-data outputs; no downloads."""
from pathlib import Path
import csv,json,math,hashlib,datetime as dt
R=Path(__file__).resolve().parents[1];O=R/'results'
def read(n):return list(csv.DictReader((O/n).open()))
def f(x):return float(x)
checks=[]
def check(name,v):
 assert v,name;checks.append({'check':name,'passed':True})
m=read('market_manifest.csv');mp={x['market_id']:x for x in m};p=read('all_predictions.csv');s=read('signals.csv');t=read('trades.csv');v=read('variant_results.csv')
check('unique_market_ids',len(mp)==len(m)==1440)
check('actual_binary_payout',all(x['up_payout'] in ['0','1'] for x in m))
check('reference_settlement_no_mismatch',all(x['reference_check']!='mismatch' for x in m))
check('no_future_bucket_feature',all(f(x['up_point_raw_ts'])+60<=f(x['t']) and f(x['down_point_raw_ts'])+60<=f(x['t']) for x in p))
check('predictions_before_expiry',all(f(x['t'])<f(mp[x['market_id']]['end_epoch_seconds']) for x in p))
check('probabilities_in_unit_interval',all(0<=f(x[k])<=1 for x in p for k in ['p_terminal','p_calibrated','p_market','p_literal_up']))
check('one_signal_per_market_per_variant',len({(x['market_id'],x['variant']) for x in s})==len(s))
check('one_fill_per_market_per_variant_scenario',len({(x['market_id'],x['variant'],x['scenario']) for x in t})==len(t))
check('settlement_payout_matches_official',all(int(x['won'])==(int(mp[x['market_id']]['up_payout']) if x['side']=='Up' else 1-int(mp[x['market_id']]['up_payout'])) for x in t))
check('no_trade_after_expiry',all(f(x['execution_ts'])<f(mp[x['market_id']]['end_epoch_seconds']) for x in t))
check('100_shares_constant',all(f(x['shares'])==100 for x in t))
check('fee_formula_independent',all(abs(f(x['fee'])-(0 if x['scenario']=='quote0' else round(100*f(x['fee_rate'])*(2 if x['scenario']=='fee_double' else 1)*(f(x['q_scenario'])*(1-f(x['q_scenario'])))**f(x['fee_exponent']),5)))<1e-9 for x in t))
check('trade_cash_identity',all(abs(f(x['net_pnl'])-(f(x['payout'])-f(x['cost'])))<1e-8 for x in t))
check('no_claimed_executable_profit',all(x['executable_net_pnl']=='' for x in v))
check('initial_cash_and_return_denominator',all(abs(f(x['final_cash'])-10000-f(x['net_pnl']))<1e-6 and abs(f(x['return_on_initial_pct'])-f(x['net_pnl'])/100)<1e-6 for x in v))
check('frozen_baseline_has_no_trades',all(int(x['trades'])==0 for x in v if x['variant']=='market_edge'))
folds=read('folds.csv');check('training_labels_precede_test_cutoff',all(dt.datetime.fromisoformat(x['last_train_label_available_utc'])<dt.datetime.fromisoformat(x['test_start_utc']) for x in folds))
freeze=json.loads((R/'logs/protocol_freeze.json').read_text());check('fitted_code_matches_preregistered_hash',hashlib.sha256((R/'src/backtest.py').read_bytes()).hexdigest()==freeze['sha256']['src/backtest.py'])
(O/'audit_checks.json').write_text(json.dumps(checks,indent=2));print(len(checks),'real-data audit checks PASS')
