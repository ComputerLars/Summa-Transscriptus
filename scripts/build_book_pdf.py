"""Typeset the public Summa reading with its sources, syntheses and photographs."""
from pathlib import Path
import json,re
from archive_pdf import Book,E,link
from reportlab.platypus import KeepTogether
R=Path(__file__).resolve().parents[1];H=json.loads((R/'hyperbook-data.json').read_text());SITE='https://computerlars.github.io/Summa-Transscriptus/'
OUT=R/'Summa-Transscriptus.pdf';b=Book(R);records={r['id']:r for r in H['records']};refs={r['id']:r for r in H['bibliography']}
registry={r['id']:r for r in json.loads((R/'documentation/references.json').read_text())}
def url(u):return u if u.startswith('http')else SITE+u
def cites(ids):return ' <super><font name="BookMeta" size="6.2">'+', '.join(link('#bib-'+i,str(refs[i]['number']))for i in ids)+'</font></super>'if ids else''
def caption(p):return p['title']+(' · Fotografi: '+p['credit']if p.get('credit')else'')+'<br/>'+p.get('place','')
def photo(pid,maxheight=340):
 p=next(p for p in H['photos']if p['id']==pid)
 b.image(p['src'],caption(p).replace('<br/>','\n'),p['source_url'],maxheight=maxheight,anchor='image-'+pid)

def record(r):
 rid=r['id'];b.heading(r['position']+' · '+r['title'] if not r['title'].startswith(r['position'])else r['title'],rid,1)
 b.p(rid+' · '+r['date'],'source')
 written=H['collation']['records'][rid].get('written',[])
 if written:
  b.p('Skriftligt forlæg','meta')
  for i,w in enumerate(written):b.p(link(url(w['url']),w['label'])+'<br/>'+E(w['text']),'source',True,anchor=rid+'-written-'+str(i))
 b.p('Disput','meta')
 for t in r['utterances']:
  sec=int(t['start']);clock=f'{sec//3600:02}:{sec%3600//60:02}:{sec%60:02}'
  b.p(E(t['speaker'])+' · '+link(SITE+'#disput/'+rid+'/'+t['id'],clock),'meta',True)
  for i,block in enumerate(t['blocks']):
   anchor=rid+'-'+t['id']+'-'+str(i)
   b.p(E(block)+cites(H['reference_loci'].get(f'{rid}:{t["id"]}:{i}',[])),raw=True,anchor=anchor)
 sourceids=[x['id']for x in H['record_references'].get(rid,[])]
 if sourceids:b.p('Henvisninger: '+', '.join(link('#bib-'+i,'['+str(refs[i]['number'])+']')for i in sourceids)+'.','source',True)
 h=H['collation']['records'][rid].get('historical')
 if h:
  b.p('Maskinsyntese · 2023','h3');b.p(h['synthesis'],anchor='synthesis-'+rid)
  b.p(link(url(h['url']),'Syntesens kildetekst'),'source',True)
 elif rid=='D4-21':b.p('Maskinsyntese · 2023','h3');b.p('Ingen maskinsyntese er bevaret for Metatese 21.','source')
 b.p(link('#recording-'+rid,'Lyd og originaloptagelse')+' · '+link(SITE+'#disput/'+rid,'Læseudgave med lydsteder'),'source',True)

b.story.append(__import__('reportlab.platypus',fromlist=['Spacer']).Spacer(1,85))
b.p('Summa Transscriptus','cover');b.p('Disputter over Computer Lars-spektaklet','centre');b.p('Organ for de Autonome Videnskaber<br/>Under Bugten · Aarhus · 17.–24. september 2023','centre',True)
b.contents()
b.heading('Praefatio','praefatio',0)
for n in range(4,70):
 p=next((p for p in H['manuscript']if p['p']==n),{'text':''})
 if p['text'].strip():b.p(E(p['text'])+cites([r['id']for r in H.get('frame_references',{}).get(str(n),[])]),raw=True,anchor='manuscript-'+str(n))
 for f in H['figures']:
  if f['paragraph']==n and 4<=n<=69:b.image(f['src'],f['title'],SITE+'manuscript.html#p'+str(n),anchor='figure-'+f['id'])
b.heading('Ordo disputandi','ordo',0,new=True)
for n in [72,74,76,77,78]:
 p=next(p for p in H['manuscript']if p['p']==n);b.p(p['text'],anchor='manuscript-'+str(n))
b.p(H['performance']['closing_signal'],'source');b.p(link(SITE+'organ-tekst.html','Organ Tekst · 40 slides')+' · '+link(SITE+'manuscript.html','Manuscriptum'),'source',True)
cover={1:'kaelder-1',2:'cille-hvass-holm-3',3:'computer-lars-bind',4:'projektion'}
for g in H['groups']:
 b.heading(['I','II','III','IV'][g['number']-1]+' · '+g['guest'],'group-'+str(g['number']),0,new=True)
 b.p(g['date']+' · '+g['guest']+' og Computer Lars','source');photo(cover[g['number']],360)
 b.story.append(__import__('reportlab.platypus',fromlist=['PageBreak']).PageBreak())
 for rid in g['records']:record(records[rid])
b.heading('Imagines','imagines',0,new=True)
for p in H['photos']:
 if p['id']not in cover.values():photo(p['id'],355)
b.heading('Kilder og forlæg','bibliography',0,new=True)
b.p('“Jf.” angiver en konteksthenvisning. Sidetal gælder de angivne udgaver.','source')
for ref in H['bibliography']:
 first=len(b.story)
 rid=ref['id'];entry=registry[rid]
 b.p('['+str(ref['number'])+'] '+E(ref['display']),'source',True,anchor='bib-'+rid)
 if entry.get('note'):b.p(entry['note'],'source')
 b.p(link(url(ref['url']),url(ref['url'])),'source',True)
 locations=[]
 for loc in ref['loci']:
  anchor=loc['record']+'-'+loc['turn']+'-'+str(loc['block'])
  locations.append(link('#'+anchor,loc['record']))
 for n in ref.get('manuscript',[]):locations.append(link('#manuscript-'+str(n),'Rammeteksten §'+str(n)))
 if locations:b.p('Tekststeder: '+' · '.join(dict.fromkeys(locations))+'.','source',True)
 b.story[first:]=[KeepTogether(b.story[first:])]
b.heading('Optagelser','recordings',0,new=True)
b.p('Tiderne regnes fra begyndelsen af den enkelte optagelse. Lyttekopierne og originalerne indeholder også pauser og opførelsens lyde.','source')
for r in H['records']:
 b.p(E(r['id']+' · '+r['title']),'source',True,anchor='recording-'+r['id'])
 b.p(link('#'+r['id'],'Disput')+' · '+link(r['audio'],'Lyttekopi')+' · '+link(r['original'],'Originaloptagelse')+'<br/>'+link(SITE+'#disput/'+r['id'],SITE+'#disput/'+r['id']),'source',True)
b.heading('Kolofon','colophon',0,new=True)
b.p('Summa Transscriptus. Disputter over Computer Lars-spektaklet. Organ for de Autonome Videnskaber. Under Bugten, Aarhus Bugt Center for Kunst på Det Jyske Kunstakademi, 17.–24. september 2023.')
b.p('Læseudgave, oktober 2026. Redigeret efter optagelserne, de oprindelige transskriptioner og de skriftlige forlæg. De oprindelige maskinsynteser fra 2023 er gengivet som særskilte tekster. Begge kunstnerstemmer betegnes Computer Lars.')
b.p('Udstillingsfotografierne er gengivet i deres bevarede billedrammer. Fotografi: Cille Hvass Holm, hvor dette er dokumenteret; de øvrige fotografier har ingen identificeret fotograf i kildens metadata. Fotografier og øvrige tredjepartsbidrag har deres egne rettigheder.')
b.p(link(SITE,SITE)+'<br/>'+link(SITE+'documentation/editorial-principles.md','Udgaveprincipper')+' · '+link(SITE+'sources/under-bugten/photos/sources.json','Billedkilder')+' · '+link(SITE+'LICENSE','Rettigheder'),'source',True)
report=b.build(OUT,'Summa Transscriptus','Organ for de Autonome Videnskaber','Summa Transscriptus')
print(json.dumps(report))
