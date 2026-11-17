"""Build an auditable local archive. No network or account actions."""
from pathlib import Path
import csv,hashlib,zipfile
ROOT=Path(__file__).resolve().parents[1]
def main():
 files=sorted(p for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.zip' and p.name!='FILES_SHA256.csv')
 with (ROOT/'FILES_SHA256.csv').open('w',newline='') as f:
  w=csv.writer(f);w.writerow(['path','bytes','sha256'])
  for p in files:w.writerow([p.relative_to(ROOT).as_posix(),p.stat().st_size,hashlib.sha256(p.read_bytes()).hexdigest()])
 files.append(ROOT/'FILES_SHA256.csv')
 out=ROOT/'月度马尔可夫回测_完整包.zip'
 with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for p in files:z.write(p,Path('month-backtest')/p.relative_to(ROOT))
 with zipfile.ZipFile(out) as z:assert z.testzip() is None
 print(out,'files',len(files),'bytes',out.stat().st_size)
if __name__=='__main__':main()
