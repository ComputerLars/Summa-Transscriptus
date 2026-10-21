"""Attach bibliographic sources to passages without modifying the spoken text."""
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
SITE='https://computerlars.github.io/Summa-Transscriptus/'

def attach(h):
    entries=json.loads((ROOT/'documentation/references.json').read_text())
    records={r['id']:r for r in h['records']}
    h['bibliography']=[]
    h['record_references']={r['id']:[]for r in h['records']}
    h['reference_loci']={}
    h['frame_references']={}
    for number,entry in enumerate(entries,1):
        ref={k:entry[k]for k in ['id','citation','url','relation']}
        ref['number']=number
        ref['display']=('Jf. 'if ref['relation']=='kontekst'else'')+ref['citation']
        locations=[]
        for locus in entry.get('loci',[]):
            r=records[locus['record']]
            if not any(x['id']==ref['id']for x in h['record_references'][r['id']]):
                h['record_references'][r['id']].append(ref)
            if not locus.get('match'):continue
            hits=[(t,i)for t in r['utterances']for i,b in enumerate(t['blocks'])if locus['match']in b]
            if not hits:raise ValueError(f"Unmatched source locus: {entry['id']} / {locus}")
            if locus.get('turn'):hits=[(t,i)for t,i in hits if t['id']==locus['turn']]
            for t,i in hits[:1]:
                key=f"{r['id']}:{t['id']}:{i}"
                h['reference_loci'].setdefault(key,[]).append(ref['id'])
                locations.append({'record':r['id'],'turn':t['id'],'block':i})
        for n in entry.get('manuscript',[]):
            assert any(p['p']==n and p['text'].strip()for p in h['manuscript']),n
            h['frame_references'].setdefault(str(n),[]).append(ref)
        h['bibliography'].append(dict(ref,loci=locations,manuscript=entry.get('manuscript',[])))
    lines=['# Kilder og forlæg',
           'Henvisningerne er knyttet til bestemte replikker eller afsnit i rammeteksten. “Jf.” betegner en konteksthenvisning; den udpeger ikke en ordret citeret passage. Årstal og sidetal gælder de angivne udgaver.',
           '[Læseudgave med lydsteder]('+SITE+')']
    for entry,ref in zip(entries,h['bibliography']):
        url=ref['url']if ref['url'].startswith('http')else '../'+ref['url']
        lines+=['<a id="'+ref['id']+'"></a>','## '+str(ref['number'])+' · '+ref['citation'],
                '['+('Kontekst'if ref['relation']=='kontekst'else'Forlæg')+']('+url+')']
        if entry.get('note'):lines.append(entry['note'])
        links=[]
        for loc in ref['loci']:
            label=loc['record']+' · '+records[loc['record']]['title']
            u=SITE+'#disput/'+loc['record']+'/'+loc['turn']
            links.append('['+label+']('+u+')')
        for n in ref['manuscript']:links.append('[Rammeteksten §'+str(n)+']('+SITE+'#manuscript-'+str(n)+')')
        if not links:
            links=['['+l['record']+']('+SITE+'#disput/'+l['record']+')'for l in entry.get('loci',[])]
        lines.append(' · '.join(links))
    (ROOT/'documentation/references.md').write_text('\n\n'.join(lines)+'\n')
    return h
