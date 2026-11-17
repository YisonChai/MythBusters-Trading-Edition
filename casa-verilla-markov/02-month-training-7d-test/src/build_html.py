from pathlib import Path
import csv,json
R=Path(__file__).resolve().parents[1];data=json.loads((R/'results/dashboard_data.json').read_text())
missing=json.loads((R/'raw/missing.json').read_text());data['meta']['missing_count']=len(missing);data['meta']['missing_markets']=missing
learned=[x for x in data['validation'] if x['model']!='market'];data['meta']['default_trained_model']=min(learned,key=lambda x:x['brier'])['model']
rows=list(csv.DictReader((R/'results/training_states.csv').open()))
for d in data['diagnostics']:
 vals=[int(x['sample_count']) for x in rows if x['model']==d['model']];d['histogram']=[sum(1 for n in vals if lo<=n<hi) for lo,hi in [(1,2),(2,5),(5,10),(10,20),(20,10**9)]]
cols=next(list(g['trades'][0]) for g in data['groups'].values() if g['trades']);data['trade_columns']=cols
for g in data['groups'].values():g['trades']=[[t.get(c) for c in cols] for t in g['trades']]
blob=json.dumps(data,ensure_ascii=False,separators=(',',':'),allow_nan=False).replace('</','<\\/')
html=(R/'src/dashboard.template.html').read_text().replace('__DATA__',blob)
assert '—' not in html
out=R/'月度马尔可夫回测.html';out.write_text(html);print('HTML bytes',out.stat().st_size,'groups',len(data['groups']),'default learned',data['meta']['default_trained_model'])
(R/'logs/html_meta.json').write_text(json.dumps({'html_bytes':out.stat().st_size,'groups':len(data['groups']),'default_model':data['meta']['default_trained_model'],'overall_validation_best':data['meta']['champion_from_validation']},indent=2))
