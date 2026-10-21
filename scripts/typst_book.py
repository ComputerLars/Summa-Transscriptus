"""Build self-contained Typst books from canonical archive text and images."""
from pathlib import Path
import json,os,shutil,subprocess,hashlib
from PIL import Image
from pypdf import PdfReader

def clean(s):return str(s).replace('\u200b','').replace('\ufeff','')
def link(url,text):return {'t':'link','url':url,'body':[clean(text)]}
def italic(text):return {'t':'italic','body':[clean(text)]}
def rich(*parts):return [clean(p)if isinstance(p,str)else p for p in parts]

class Book:
 def __init__(self,root,mode,title,subtitle,author,event,site,cover_title,cover_subtitle,cover_label,imprint):
  self.root=Path(root);self.work=self.root/'.book-build';self.work.mkdir(exist_ok=True)
  self.data=dict(mode=mode,title=title,subtitle=subtitle,author=author,event=event,site=site,language='da'if mode=='summa'else'en',edition='Læseudgave · oktober 2026'if mode=='summa'else'Reading edition · October 2026',imprint=imprint,blocks=[])
  self.data.update({'cover-title':cover_title,'cover-subtitle':cover_subtitle,'cover-label':cover_label,'cover-image':None});self.images=0
 def add(self,kind,**values):self.data['blocks'].append(dict(kind=kind,**values))
 def chapter(self,title,id,subtitle=''):self.add('chapter',title=title,id=id,subtitle=subtitle)
 def section(self,title,id,subtitle=''):self.add('section',title=title,id=id,subtitle=subtitle)
 def p(self,body,role='body',id=None,first=False):self.add('p',body=rich(body)if isinstance(body,str)else body,role=role,id=id,first=first)
 def meta(self,body):self.add('meta',body=rich(body)if isinstance(body,str)else body)
 def image(self,src,caption='',url=None,height=120,id=None,append=True):
  path=self.root/src
  with Image.open(path)as im:
   w,h=im.size
   if path.suffix.lower()in('.jpg','.jpeg')and max(w,h)>1800:
    key=hashlib.sha256(path.read_bytes()).hexdigest()[:16];dest=self.work/(key+'.jpg')
    if not dest.exists():
     im=im.convert('RGB');im.thumbnail((1500,1900),Image.Resampling.LANCZOS);im.save(dest,quality=89,optimize=True)
    src=dest.relative_to(self.root).as_posix()
  cap=[]
  for i,line in enumerate(caption.splitlines()):
   if i:cap.append({'t':'br'})
   cap.append(link(url,line)if url else line)
  values=dict(src=src,caption=caption,**{'caption-rich':cap,'pixel-width':w,'pixel-height':h},height=height,id=id)
  self.images+=1
  if append:self.add('image',**values)
  return values
 def build(self,output):
  path=self.work/'book.json'
  exe=os.environ.get('TYPST_BIN')or shutil.which('typst')
  if not exe:
   found=sorted((Path.home()/'.cache/codex-tools/typst').glob('*/typst'))
   if found:exe=str(found[-1])
  if not exe:raise RuntimeError('Install Typst CLI 0.15 or newer, or set TYPST_BIN.')
  candidate=self.work/'book.pdf'
  fontpaths=[self.root/'assets/fonts']
  office=Path('/Applications/Microsoft PowerPoint.app/Contents/Resources/DFonts')
  if self.data['mode']=='defence' and office.is_dir():fontpaths.append(office)
  command=[exe,'compile','--root',str(self.root)]
  for folder in fontpaths:command+=['--font-path',str(folder)]
  family_command=[exe,'fonts','--ignore-system-fonts']
  for folder in fontpaths:family_command+=['--font-path',str(folder)]
  families=subprocess.check_output(family_command,text=True).splitlines()
  if self.data['mode']=='defence':
   selected=('Garamond'if 'Garamond'in families else'EB Garamond')+' and '+('Consolas'if 'Consolas'in families else'DejaVu Sans Mono')
   encoded=json.dumps(self.data,ensure_ascii=False).replace('Garamond and Consolas',selected)
   self.data=json.loads(encoded)
  path.write_text(json.dumps(self.data,ensure_ascii=False,indent=2)+'\n')
  command+=['--ignore-system-fonts','--input','data=.book-build/book.json',str(self.root/'scripts/book.typ'),str(candidate)]
  subprocess.run(command,check=True)
  reader=PdfReader(candidate);ids={p.indirect_reference.idnum for p in reader.pages};links=0;named=reader.named_destinations
  for page in reader.pages:
   for item in page.get('/Annots',[]):
    a=item.get_object();d=a.get('/Dest');act=a.get('/A')
    if d is None and act:d=act.get_object().get('/D')
    if d is not None:
     d=d.get_object()if hasattr(d,'get_object')else d
     if isinstance(d,str):assert d in named and reader.get_destination_page_number(named[d])>=0,'Missing named PDF destination: '+d
     elif isinstance(d,list):assert d[0].idnum in ids,'Invalid internal PDF destination'
     else:raise ValueError('Unknown PDF destination: '+str(d))
     links+=1
  result=dict(pages=len(reader.pages),images=self.images,internal_links=links,bytes=candidate.stat().st_size,typst=subprocess.check_output([exe,'--version'],text=True).strip())
  (self.work/'build-report.json').write_text(json.dumps(result,indent=2)+'\n')
  shutil.copyfile(candidate,output)
  return result
