"""Refresh the published archive's file inventory."""
from pathlib import Path
import json,hashlib,subprocess
R=Path(__file__).resolve().parents[1]
names=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=R).decode().split('\0');files=[]
for name in sorted(set(names)):
 p=R/name
 if not name or name=='FILE-MANIFEST.json' or not p.is_file():continue
 b=p.read_bytes();files.append({'path':name,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
(R/'FILE-MANIFEST.json').write_text(json.dumps({'edition_date':'2026-10-19','files':files},ensure_ascii=False,indent=2)+'\n')
print('Manifest:',len(files),'files')
