"""Build the continuous reading from the preserved 18 October source edition.

2023 transcriptions, syntheses and the diplomatic manuscript remain unchanged.
"""
from pathlib import Path
from copy import deepcopy
import json,re,subprocess
from difflib import SequenceMatcher
R=Path(__file__).resolve().parents[1]
BASE='3224e3c74cf4505f2683a036e103fa3de4900531'
log=[];boundary_log=[]
READING_REPLACEMENTS={
 ('D2-07','D2-07-U012-2'):{
  'text':'Jeg håber, at det er okay, at jeg kom til at tænde maskinen.',
  'basis':'Efter forfatterens anvisning beholdes kun denne replik fra det praktiske replikskifte uden for disputten. Kildeenheder og optagelse bevares.'
 }
}
names={'Mikkel Bolt':'Mikhailos Boltus','Maja Bak Herrie':'Maia Bacchus','Peter Borum':'Petrus Borumanum'}
PROSE_EDITS=json.loads((R/'documentation/reading-prose.json').read_text())['edits']
TURN_HINGES=json.loads((R/'documentation/reading-paragraphs.json').read_text())['turn_hinges']
SPEAKER_BOUNDARIES=json.loads((R/'documentation/speaker-boundaries.json').read_text())
SPEAKER_SPLITS=SPEAKER_BOUNDARIES['splits']
SPEAKER_STARTS={(s['record'],s['turn']):s['time'] for s in SPEAKER_BOUNDARIES.get('starts',[])}
def prose(text,rid):
 for edit in PROSE_EDITS:
  if edit['record']==rid:text=text.replace(edit['before'],edit['after'])
 return text

def clean(text,rid=''):
 for before,after in names.items():text=text.replace(before,after)
 # Remove only the detached tag, not meaningful negative questions.
 text=text.replace('Carol Stombaugh','Carol Stumper').replace('Carl Miles','Corrupt Males')
 if rid=='D2-02':text=text.replace('står i i forhold til netværket','står i forhold til netværket')
 if rid=='D4-17':text=text.replace('Og problemet, der er, er, at spørgsmålet','Og problemet er, at spørgsmålet')
 if rid=='D3-02':text=text.replace('[Oplæsning på latin.]','Martius praepositus')
 text=re.sub(r',\s*ikke\?(?:\s*,)?', '.',text)
 if rid=='D2-04':
  text=text.replace('Computer Lars har mindst to lemmer','Computer Lars har mindst to legemer').replace('Computer Lars har to lemmer','Computer Lars har mindst to legemer')
 text=prose(text,rid)
 text=re.sub(r'\.\s*\.', '.',text)
 text=re.sub(r' {2,}',' ',text)
 return text.strip()
HINGES={
"D2-04":["Og på samme måde har maskiner", "I dag ville det også være nemt", "Men Computer Lars er jo ikke en suveræn", "Der er aldrig nogen, der helt ved"],
"D3-08":["Det tror jeg er Computer Lars' trivielle tese", "Og der er i høj grad en fransk", "Men noget, man bare savner", "Men jeg tror også, at motivationen"],
"D3-06":["På sporet af den tabte tid slutter så", "Og i det hele taget er simpliciteten", "Og når man betragter det fra Proust", "Men det gør vel ikke noget"],
"D2-01":["Så hvordan er Computer Lars flad", "På denne måde minder Computer Lars", "Og det fører mig til den anden måde"],
"D1-07":["Men dialektikken er gået i stykker", "Og Computer Lars er jo selv et svar", "Så problemet er jo", "Så vi er i den situation", "Så på en eller anden måde er vi full circle"],
"D1-03":["Men hvis man nu ikke var enig", "Så i antitesedannelsen"],
"D3-02":["Men det, den siger, er", "Så sammenlagt bliver", "Så hvis Computer Lars"]
}

def blocks_at_hinges(blocks,rid,turn=None):
 out=[]
 phrases=HINGES.get(rid,[])+[clean(p,rid)for p in TURN_HINGES.get(turn,[])]
 for b in blocks:
  cuts=[0]+[b.index(phrase)for phrase in phrases if phrase in b and b.index(phrase)>0 and re.search(r'[.!?][”\'\"]?\s+$',b[:b.index(phrase)])]+[len(b)]
  cuts=sorted(set(cuts));out += [b[a:z].strip()for a,z in zip(cuts,cuts[1:])if b[a:z].strip()]
 return out

def reading_boundaries(blocks):
 """Join source chunk boundaries inside one speaker's sentence."""
 out=[]
 for block in blocks:
  if out and not re.search(r'[.!?…][”\'\"]?$',out[-1]):
   out[-1]+=' '+block
  else:out.append(block)
 if out:
  # A stranded connector at the end of a turn carries no proposition.
  out[-1]=re.sub(r'\s+\b(?:og|men|eller|så)$','',out[-1],flags=re.I).rstrip(',;: ')
  if not re.search(r'[.!?…][”\'\"]?$',out[-1]):
   if re.search(r'[,;:]$',out[-1]):out[-1]=out[-1][:-1]+'…'
   else:out[-1]+='…'
  if out[0] and out[0][0].islower():out[0]=out[0][0].upper()+out[0][1:]
 return out

def jslen(text):return len(text.encode('utf-16-le'))//2

def source_turns(record):
 """Separate actual replies inside an old recognition unit, retaining its anchors."""
 for old in record['utterances']:
  rule=next((s for s in SPEAKER_SPLITS if s['record']==record['id'] and s['turn']==old['id']),None)
  if not rule:
   yield old
   continue
  assert old['text'].count(rule['before'])==1
  cut=old['text'].index(rule['before']);off=jslen(old['text'][:cut])
  left=deepcopy(old);right=deepcopy(old)
  left['text']=old['text'][:cut].rstrip();right['text']=old['text'][cut:]
  left['blocks']=[];right['blocks']=[];position=0
  for block in old['blocks']:
   a=block[:max(0,cut-position)].strip();b=block[max(0,cut-position):].strip()
   if a:left['blocks'].append(a)
   if b:right['blocks'].append(b)
   position+=len(block)+1
  left['speaker']=rule['first_speaker'];right['speaker']=rule['second_speaker']
  left['end']=right['start']=rule['time'];right['id']=rule['second_id']
  right['units']=rule['second_units'];left['units']=[u for u in old['units']if u not in right['units']]
  left['loci']=[l for l in old.get('loci',[])if l['offset']<off]
  right['loci']=[{**l,'offset':l['offset']-off}for l in old.get('loci',[])if l['offset']>=off]
  assert left['text']+' '+right['text']==old['text']
  assert left['units']+right['units']==old['units']
  yield left
  yield right

def shifted_offset(before,after,offset):
 # Source loci use UTF-16 offsets in the browser. Keep them attached through
 # punctuation and word edits, including a correction across source chunks.
 a=before.encode('utf-16-le');b=after.encode('utf-16-le')
 a=[a[n:n+2]for n in range(0,len(a),2)];b=[b[n:n+2]for n in range(0,len(b),2)]
 for tag,i,j,x,y in SequenceMatcher(None,a,b,autojunk=False).get_opcodes():
  if i<=offset<j:return x+min(offset-i,y-x)
 return len(b)

def build():
 h=json.loads(subprocess.check_output(['git','show',BASE+':hyperbook-data.json'],cwd=R))
 # An accidental keystroke in the manuscript is omitted from the reading display.
 # The diplomatic manuscript and original Word source remain available unchanged.
 for p in h['manuscript']:p['text']=p['text'].replace('€€€#€€##€####DD###€','')
 speaker_path=R/'documentation/speaker-readings-20261019.json'
 speaker_edits={(x['record'],x['turn']):x['after']for x in json.loads(speaker_path.read_text())['changes']}if speaker_path.exists()else{}
 speaker_edits.update({(x['record'],x['turn']):x['speaker']for x in SPEAKER_BOUNDARIES.get('confirmed_turns',[])})
 synthesis_before={k:(v.get('historical')or{}).get('synthesis')for k,v in h['collation']['records'].items()}
 for r in h['records']:
  for p in r['paragraphs']:
   before=p['text'];p['text']=clean(before,r['id'])
   if before!=p['text']:log.append({'record':r['id'],'locus':p['id'],'before':before,'after':p['text']})
  turns=[]
  for old in source_turns(r):
   t=deepcopy(old);oldtext=old['text'];t['blocks']=[clean(s,r['id'])for s in old['blocks']];t['blocks']=blocks_at_hinges(t['blocks'],r['id']);t['text']=' '.join(t['blocks'])
   t['speaker']=speaker_edits.get((r['id'],t['id']),t['speaker'])
   t['loci']=[{**l,'offset':jslen(clean(oldtext.encode('utf-16-le')[:l['offset']*2].decode('utf-16-le'),r['id']))}for l in old.get('loci',[])]
   if (r['id'],t['id']) in SPEAKER_STARTS:
    t['start']=SPEAKER_STARTS[(r['id'],t['id'])]
    t['loci']=[{**l,'start':t['start']}if l['offset']==0 else l for l in t['loci']]
   # Two named Computer Lars voices share one public speaking position.
   same=bool(turns and turns[-1]['speaker']==t['speaker'])
   if t['speaker']=='Interventio' and turns and turns[-1].get('voice')!=t.get('voice'):same=False
   if same:
    prior=turns[-1];offset=jslen(prior['text'])+1
    prior['text']+=' '+t['text'];prior['blocks']+=t['blocks'];prior['end']=t['end'];prior['units']+=t['units'];prior['loci'] += [{**l,'offset':l['offset']+offset}for l in t['loci']]
   else:turns.append(t)
  for t in turns:
   before={'text':t['text'],'blocks':list(t['blocks'])}
   replacement=READING_REPLACEMENTS.get((r['id'],t['id']))
   if replacement:
    assert '[Kort udveksling ved maskinen.]' in t['text']
    t['blocks']=[replacement['text']]
    # Retain links to all source units without indexing the omitted chatter.
    t['loci']=[{**l,'offset':0}for l in t.get('loci',[])]
   t['blocks']=blocks_at_hinges([prose(b,r['id'])for b in reading_boundaries(t['blocks'])],r['id'],t['id'])
   t['text']=' '.join(t['blocks'])
   if before['text']!=t['text'] and not replacement:
    t['loci']=[{**l,'offset':shifted_offset(before['text'],t['text'],l['offset'])}for l in t.get('loci',[])]
   if before['text']!=t['text'] or before['blocks']!=t['blocks']:
    entry={'record':r['id'],'turn':t['id'],'before':before,'after':{'text':t['text'],'blocks':t['blocks']}}
    if replacement:entry['basis']=replacement['basis']
    boundary_log.append(entry)
  r['utterances']=turns
  n=int(r['id'].split('-')[1]);r['position']='Pseudotese' if r['id']=='D3-09' else 'Metatese' if r['group']==4 else 'Tese' if n%2 else 'Antitese'
  r['pair']=None if r['group']==4 or r['id']=='D3-09' else r['id'][:-2]+f'{n if n%2 else n-1:02}'
  # The public reading files use the same grouped turns and real paragraphs.
 for g in h['groups']:
  text=['# '+g['guest']+' og Computer Lars',g['date']]
  for rid in g['records']:
   r=next(x for x in h['records']if x['id']==rid);text+=['## '+rid+' · '+r['position']+' · '+r['title']]
   for t in r['utterances']:
    text += ['<a id="'+u+'"></a>'for u in t['units']]
    secs=int(t['start']);clock=f'{secs//3600:02}:{secs%3600//60:02}:{secs%60:02}'
    text+=['**'+t['speaker']+' · '+clock+'**',*t['blocks']]
  (R/g['path']/'reading.md').write_text('\n\n'.join(text)+'\n')
 additional_refs={
 'D1-01':[{'id':'oratio-latina','citation':'Oratio latina · rekonstrueret forlæg efter Hans-Jørgen Schanz, Til rekonstruktionen af kritikken af den politiske økonomis omfangslogiske status. Aarhus: Modtryk, 1973.','url':'sources/under-bugten/opening-latin.md'}],
 'D2-01':[{'id':'anagrams','citation':'Figur 1: Anagrammer af Computer Lars. Samledokumentet, §40, 2023.','url':'manuscript.html#p40'}],
 'D3-02':[{'id':'praepositus','citation':'Prévôt, fra latin praepositus. Dictionnaire de l’Académie française, 9. udgave.','url':'https://www.dictionnaire-academie.fr/article/A9P4273'},{'id':'martius','citation':'Martius: tilhørende Mars. Lewis & Short, A Latin Dictionary (1879), “Mars”, III.','url':'https://www.perseus.tufts.edu/hopper/text?doc=Perseus%3Atext%3A1999.04.0059%3Aentry%3DMars'}],
 'D2-04':[{'id':'bratton-stack','citation':'Benjamin H. Bratton, The Stack: On Software and Sovereignty. MIT Press, 2016.','url':'https://mitpress.mit.edu/9780262029575/the-stack/'},{'id':'wynter-ceremony','citation':'Sylvia Wynter, The Ceremony Must Be Found: After Humanism. boundary 2, 12/13, 1984, pp. 19–70.','url':'https://www.jstor.org/stable/302808'},{'id':'kantorowicz','citation':'Ernst H. Kantorowicz, The King’s Two Bodies: A Study in Mediaeval Political Theology. Princeton University Press, 1957.','url':'https://www.jstor.org/stable/j.ctvcszz1c'}],
 }
 additional_refs['D1-06']=[
  {'id':'beer-cybersyn','citation':'Stafford Beer og Project Cybersyn. ZKM, Thinking Inside Out: Cybernetics and Viable Utopias, 2025.','url':'https://zkm.de/en/2025/01/thinking-inside-out-cybernetics-and-viable-utopias'},
  {'id':'urquhart-genealogy','citation':'Thomas Urquhart, Pantochronachanon (1652). Slægtstavlen er gengivet i John Willcock, Sir Thomas Urquhart of Cromartie, Knight (1899), tillæg I.','url':'https://www.gutenberg.org/files/38604/38604-h/38604-h.htm#Page_211'}]
 additional_refs['D2-04'].append({'id':'hui-sovereignty','citation':'Yuk Hui, Machine and Sovereignty: For a Planetary Thinking. University of Minnesota Press, 2024.','url':'https://www.upress.umn.edu/9781517917418/machine-and-sovereignty/'})
 additional_refs['D2-07']=[{'id':'peirce-lowell','citation':'Charles Sanders Peirce, Lowell Lectures (1903), Collected Papers 1.536–537.','url':'https://colorysemiotica.wordpress.com/wp-content/uploads/2014/08/peirce-collectedpapers.pdf'}]
 additional_refs['D3-05']=[{'id':'magliabechi','citation':'Antonio Magliabechi (1633–1714). Biblioteca Nazionale Centrale di Firenze, The origins and evolution of the Magliabechiana library.','url':'https://bncf.cultura.gov.it/en/library/the-origins-and-evolution-of-the-magliabechiana-library/'}]
 h['record_references']={}
 for r in h['records']:
  refs=[]
  for entry in h['collation']['entries']:
   if entry['source_id']==r['id']:
    for refid in entry.get('references',[]):
     ref=next((x for x in h['collation']['references']if x['id']==refid),None)
     if ref and refid!='old-art' and ref not in refs:refs.append({k:ref[k]for k in ['id','citation','url']})
  additions=additional_refs.get(r['id'],[])
  if r['id']=='D2-04':refs=[ref for ref in refs if ref['id']!='hui-machine']
  if r['id']=='D2-07':refs=[ref for ref in refs if ref['id']!='peirce']
  addition_ids={ref['id']for ref in additions}
  h['record_references'][r['id']]=[ref for ref in refs if ref['id']not in addition_ids]+additions
 h['edition']='2026-10-20'
 h['reading_policy']['speaker']='Navnene følger opførelsen. Begge kunstnerstemmer hedder Computer Lars. Sammenhængende tale fra samme offentlige position har én talerbetegnelse; lydsteder og kildeankre bevares.'
 h['reading_policy']['paragraphs']='Afsnit følger argumentet. Optagelsesbrud inde i samme talers sætning sammenføjes; afbrudte sætninger markeres med udeladelsesprikker. Optagelses- og genkendelsesenhederne bevares som kildeankre.'
 assert synthesis_before=={k:(v.get('historical')or{}).get('synthesis')for k,v in h['collation']['records'].items()}
 (R/'hyperbook-data.json').write_text(json.dumps(h,ensure_ascii=False,separators=(',',':'))+'\n')
 (R/'documentation/paragraph-boundaries.json').write_text(json.dumps({'edition':'2026-10-20','changes':boundary_log,'source_unit_ids_preserved':True},ensure_ascii=False,indent=2)+'\n')
 (R/'documentation/reading-corrections.json').write_text(json.dumps({'base_commit':BASE,'changes':log,'syntheses_2023_unchanged':True,'paragraph_hinges':HINGES,'name_sources':{'Carol Stumper':'Figure 1 in the 2023 manuscript, p40 / image6.png; thesis pp. 7, 23, 244.','Corrupt Males':'Figure 1 in the 2023 manuscript, p40 / image6.png; anagram name, not Carl Miles.'},'selected_readings':[{'record':'D3-02','reading':'Martius praepositus','basis':'Konjektural rekonstruktion, godkendt af Asker Bryld Staunæs. Valgt ved sammenhold af lydgenkendelserne, den efterfølgende danske forklaring og de latinske ordformer.','references':additional_refs['D3-02']}]},ensure_ascii=False,indent=2)+'\n')
 print('Reading:',len(log),'locally edited source paragraphs;',sum(len(r['utterances'])for r in h['records']),'speaking turns;',sum(bool(v.get('historical'))for v in h['collation']['records'].values()),'original syntheses.')
if __name__=='__main__':build()
