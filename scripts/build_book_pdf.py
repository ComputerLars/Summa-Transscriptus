"""Typeset the complete Summa from canonical sources with Typst."""
from pathlib import Path
import json
from typst_book import Book,rich,link,italic
R=Path(__file__).resolve().parents[1];H=json.loads((R/'hyperbook-data.json').read_text());SITE='https://computerlars.github.io/Summa-Transscriptus/'
refs={r['id']:r for r in H['bibliography']};registry={r['id']:r for r in json.loads((R/'documentation/references.json').read_text())}
def url(u):return u if u.startswith('http')else SITE+u
imprint=[
 rich('Organ for de Autonome Videnskaber. ',italic('Summa Transscriptus. Disputter over Computer Lars-spektaklet.')),
 rich('Under Bugten, Aarhus Bugt Center for Kunst på Det Jyske Kunstakademi. Mejlgade 32, Aarhus. 17.–24. september 2023.'),
 rich('Læseudgave, oktober 2026. Redigeret efter optagelserne, de oprindelige transskriptioner og de skriftlige forlæg. Begge kunstnerstemmer betegnes Computer Lars. De oprindelige maskinsynteser fra 2023 er gengivet særskilt og uændret.'),
 rich('Fotografi: Cille Hvass Holm, hvor dette er dokumenteret. Fotografier og øvrige tredjepartsbidrag har deres egne rettigheder.'),
 rich('Sats: DejaVu Sans Mono. A5. Typst.'),
 rich(link(SITE+'documentation/editorial-principles.md','Udgaveprincipper'),' · ',link(SITE+'LICENSE','Rettigheder'))]
b=Book(R,'summa','Summa Transscriptus','Disputter over Computer Lars-spektaklet','Organ for de Autonome Videnskaber','Under Bugten · Aarhus · 17.–24. september 2023',SITE,'Summa\nTransscriptus','Disputter over\nComputer Lars-spektaklet','ORGAN FOR DE AUTONOME VIDENSKABER',imprint)
def cites(ids):
 parts=[]
 for n,i in enumerate(ids):
  if n:parts.append(', ')
  parts.append(link('#bib-'+i,str(refs[i]['number'])))
 return [{'t':'sup','body':parts}]if parts else[]
def photo(pid,height=120):
 p=next(p for p in H['photos']if p['id']==pid)
 cap=p['title']+(' · Fotografi: '+p['credit']if p.get('credit')else'')+'\n'+p.get('place','')
 b.image(p['src'],cap,p['source_url'],height,id='image-'+pid)
b.chapter('Praefatio','praefatio')
for n in range(4,70):
 p=next((p for p in H['manuscript']if p['p']==n),{'text':''})
 if p['text'].strip():b.p(rich(p['text'])+cites([r['id']for r in H.get('frame_references',{}).get(str(n),[])]),id='manuscript-'+str(n),first=n==4)
 for f in H['figures']:
  if f['paragraph']==n:b.image(f['src'],f['title'],SITE+'manuscript.html#p'+str(n),id='figure-'+f['id'])
b.chapter('Ordo disputandi','ordo')
for n in [72,74,76,77,78]:b.p(next(p for p in H['manuscript']if p['p']==n)['text'],id='manuscript-'+str(n),first=n==72)
b.p(H['performance']['closing_signal'],'source',first=True)
b.p(rich(link(SITE+'organ-tekst.html','Organ Tekst · 40 slides'),' · ',link(SITE+'manuscript.html','Manuscriptum')),'source')
cover={1:'kaelder-1',2:'cille-hvass-holm-3',3:'computer-lars-bind',4:'projektion'};records={r['id']:r for r in H['records']}
for g in H['groups']:
 b.chapter(['I','II','III','IV'][g['number']-1]+' · '+g['guest'],'group-'+str(g['number']),g['date']+' · '+g['guest']+' og Computer Lars')
 photo(cover[g['number']],112);b.add('break')
 for rid in g['records']:
  r=records[rid];b.section(r['position']+' · '+r['title']if not r['title'].startswith(r['position'])else r['title'],rid,rid+' · '+r['date'])
  written=H['collation']['records'][rid].get('written',[])
  if written:b.add('written',label=['Skriftligt forlæg'],paragraphs=[dict(id=rid+'-written-'+str(i),body=rich(link(url(w['url']),w['label']),{'t':'br'},w['text']))for i,w in enumerate(written)])
  b.meta('Disput')
  for t in r['utterances']:
   sec=int(t['start']);clock=f'{sec//3600:02}:{sec%3600//60:02}:{sec%60:02}'
   paragraphs=[dict(id=rid+'-'+t['id']+'-'+str(i),body=rich(block)+cites(H['reference_loci'].get(f'{rid}:{t["id"]}:{i}',[])))for i,block in enumerate(t['blocks'])]
   b.add('turn',speaker=t['speaker'],clock=clock,url=SITE+'#disput/'+rid+'/'+t['id'],paragraphs=paragraphs)
  sr=H['record_references'].get(rid,[])
  if sr:
   parts=['Henvisninger: ']
   for n,ref in enumerate(sr):parts+=rich(link('#bib-'+ref['id'],'['+str(ref['number'])+']'),', 'if n<len(sr)-1 else'.')
   b.p(parts,'source')
  h=H['collation']['records'][rid].get('historical')
  if h:b.add('synthesis',title='Maskinsyntese · 2023',text=h['synthesis'],id='synthesis-'+rid,source=rich(link(url(h['url']),'Syntesens kildetekst')))
  elif rid=='D4-21':b.add('synthesis',title='Maskinsyntese · 2023',text='Ingen maskinsyntese er bevaret for Metatese 21.',id='synthesis-'+rid,source=[])
  b.p(rich(link('#recording-'+rid,'Lyd og originaloptagelse'),' · ',link(SITE+'#disput/'+rid,'Læseudgave med lydsteder')),'source')
b.chapter('Imagines','imagines')
for p in H['photos']:
 if p['id']not in cover.values():photo(p['id'],130)
b.chapter('Kilder og forlæg','bibliography')
b.p('“Jf.” angiver en konteksthenvisning. Sidetal gælder de angivne udgaver.','source',first=True)
for ref in H['bibliography']:
 parts=['Tekststeder: '];locations=[]
 for loc in ref['loci']:
  key=(loc['record'],loc['record']+'-'+loc['turn']+'-'+str(loc['block']))
  if key not in locations:locations.append(key)
 for n in ref.get('manuscript',[]):locations.append(('Rammeteksten §'+str(n),'manuscript-'+str(n)))
 for i,(text,dest)in enumerate(locations):parts+=rich(link('#'+dest,text),' · 'if i<len(locations)-1 else'.')
 b.add('bibliography',id='bib-'+ref['id'],citation=rich('['+str(ref['number'])+'] ',link(url(ref['url']),ref['display'])),note=registry[ref['id']].get('note',''),backlinks=parts if locations else[])
b.chapter('Optagelser','recordings')
b.p('Tiderne regnes fra begyndelsen af den enkelte optagelse. Lyttekopierne og originalerne indeholder også pauser og opførelsens lyde.','source',first=True)
for r in H['records']:
 b.p(r['id']+' · '+r['title'],'source',id='recording-'+r['id'],first=True)
 b.p(rich(link('#'+r['id'],'Disput'),' · ',link(r['audio'],'Lyttekopi'),' · ',link(r['original'],'Originaloptagelse'),' · ',link(SITE+'#disput/'+r['id'],'Læseudgave')),'source')
b.chapter('Kolofon','colophon')
for p in imprint:b.p(p,'source',first=True)
b.p(rich(link(SITE,SITE)),'source')
print(json.dumps(b.build(R/'Summa-Transscriptus.pdf')))
