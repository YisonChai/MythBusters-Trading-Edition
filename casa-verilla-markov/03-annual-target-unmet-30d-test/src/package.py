"""Local complete and lightweight bundles; no uploads/network."""
from pathlib import Path
import csv,hashlib,zipfile,json
ROOT=Path(__file__).resolve().parents[1]
def main():
 files=sorted(p for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.zip' and p.name!='FILES_SHA256.csv')
 with (ROOT/'FILES_SHA256.csv').open('w',newline='') as f:
  w=csv.writer(f);w.writerow(['path','bytes','sha256'])
  for p in files:w.writerow([p.relative_to(ROOT).as_posix(),p.stat().st_size,hashlib.sha256(p.read_bytes()).hexdigest()])
 files.append(ROOT/'FILES_SHA256.csv')
 light_results={'results.csv','prediction_metrics.csv','calibration.csv','validation_candidates.csv','state_diagnostics.csv','monthly_coverage.csv','test_reuse.csv','test_reuse_daily.csv','reuse_summary.json','availability.json','half_results.csv','half_prediction_metrics.csv','half_actual_cohorts.csv','audit_checks.json','run_summary.json'}
 light_logs={'environment.json','html_meta.json','html_test.json','loader_test.json','reproduction.json','freeze.json','unit.log','audit_final.log','final_checks.json'}
 lightweight=[p for p in files if p.parent==ROOT or p.parent.name=='src' or p.parent.name=='docs' or (p.parent.name=='results' and p.name in light_results) or (p.parent.name=='logs' and p.name in light_logs)]
 output=[]
 for name,items in [('年度目标核查_30日回测_完整包.zip',files),('年度目标核查_30日回测_轻量报告包.zip',lightweight)]:
  out=ROOT/name
  with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
   for p in items:z.write(p,Path('year-backtest')/p.relative_to(ROOT))
  with zipfile.ZipFile(out) as z:assert z.testzip() is None
  output.append({'path':str(out),'files':len(items),'bytes':out.stat().st_size})
 print(json.dumps(output,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
