"""Synchronise Word reading copies with the continuous public edition."""
from pathlib import Path
import json
from docx import Document
from docx.oxml.ns import qn
from docx.shared import Pt,RGBColor
R=Path(__file__).resolve().parents[1]
h=json.loads((R/'hyperbook-data.json').read_text());records={r['id']:r for r in h['records']}
for g in h['groups']:
 path=R/g['path']/'reading.docx';doc=Document(path)
 for child in list(doc._element.body):
  if child.tag!=qn('w:sectPr'):doc._element.body.remove(child)
 doc.core_properties.title='Summa Transscriptus · '+g['guest'];doc.core_properties.author='Organ for de Autonome Videnskaber';doc.core_properties.last_modified_by='Organ for de Autonome Videnskaber'
 for name in ['Normal','Title','Subtitle','Heading 1','Heading 2','Heading 3']:
  st=doc.styles[name];st.font.color.rgb=RGBColor(0,0,0)
 doc.add_paragraph('Summa Transscriptus','Title');doc.add_paragraph(g['guest']+' og Computer Lars','Subtitle');doc.add_paragraph(g['date']+' · Under Bugten · Aarhus Bugt Center for Kunst på Det Jyske Kunstakademi')
 for rid in g['records']:
  r=records[rid];doc.add_paragraph(r['position']+' · '+r['title'],'Heading 1');p=doc.add_paragraph(rid+' · '+g['date']);p.paragraph_format.space_after=Pt(18)
  for t in r['utterances']:
   sec=int(t['start']);clock=f'{sec//3600:02}:{sec%3600//60:02}:{sec%60:02}'
   p=doc.add_paragraph();p.paragraph_format.keep_with_next=True;p.paragraph_format.space_before=Pt(12);run=p.add_run(t['speaker']+' · '+clock);run.font.size=Pt(9);run.italic=True
   for b in t['blocks']:doc.add_paragraph(b)
  history=h['collation']['records'][rid].get('historical')
  if history:
   doc.add_paragraph('Maskinsyntese · 2023','Heading 2');doc.add_paragraph(history['synthesis'])
  p=doc.add_paragraph('Læseudgave og lydsteder: https://computerlars.github.io/Summa-Transscriptus/#disput/'+rid);p.paragraph_format.space_before=Pt(0);p.paragraph_format.space_after=Pt(6)
  for run in p.runs:run.font.size=Pt(8.5)
 doc.save(path)
 print(path.relative_to(R),len(doc.paragraphs),'paragraphs')
