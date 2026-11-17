"""Break archival hardlinks only for editable non-data files. No calculations."""
from pathlib import Path
import shutil,os,tempfile
ROOT=Path(__file__).resolve().parent
count=0
for p in ROOT.rglob('*'):
 if not p.is_file() or p.is_symlink() or 'data' in p.relative_to(ROOT).parts:continue
 if p.stat().st_nlink<2:continue
 fd,tmp=tempfile.mkstemp(prefix='.unlink-',dir=p.parent);os.close(fd)
 shutil.copy2(p,tmp);os.replace(tmp,p);count+=1
print('Editable hardlinks separated:',count,'; contents unchanged; data untouched')
