/* Summa Transscriptus. All quoted text is drawn from the dated archive layers. */
const book=document.getElementById('book');
const e=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const clock=n=>[Math.floor(n/3600),Math.floor(n/60)%60,Math.floor(n)%60].map(x=>String(x).padStart(2,'0')).join(':');
const rootUnit=id=>(id||'').replace(/(-U\d+)-\d+$/,'$1');
const count=text=>text.trim().split(/\s+/).filter(Boolean).length;
const num=n=>n.toLocaleString('da-DK');
const roman=['I','II','III','IV'];
let H,records,routeVersion=0,currentTrack=null,repeatRange=null,audioRequest=0;
let localNotes={};try{localNotes=JSON.parse(localStorage.getItem('summa-reading-notes')||'{}')}catch(_){}
const sound=document.getElementById('sound');
const refLink=(url,label)=>'<a href="'+e(url)+'">'+e(label)+'</a>';
const readingLink=(id,label)=>refLink('#disput/'+id,label);
const historical=id=>H.collation.records[id]?.historical;
const hasUnit=(p,id)=>[p.id,p.unit_id,...(p.joined_units||[])].some(x=>x===id||rootUnit(x)===id);
const noteEntries=(id,unit)=>H.collation.entries.filter(n=>n.source_id===id&&(!unit||n.unit_id===rootUnit(unit)));
const selectedParagraphs=(r,units)=>r.paragraphs.filter(p=>units.some(u=>hasUnit(p,u)));
const sourceLine=(url,label)=>'<p class="source-line">'+refLink(url,label)+'</p>';
const recordMeta=r=>'<p class="meta">'+e(r.date+' · '+r.guest+' og Computer Lars · Praeses')+'</p>';

function figureCaption(f){
  return '<figcaption class="caption">'+e(f.title)+'<br>'+refLink('manuscript.html#p'+f.paragraph,'Samledokumentet · afsnit '+f.paragraph)+'</figcaption>';
}
function photoCaption(p){
  return '<figcaption class="caption">'+e(p.place)+(p.credit?'<br>Fotografi: '+e(p.credit):'')+'<br>'+refLink(p.source_url,p.title)+'</figcaption>';
}
function photo(p,link=true){
  const img='<img src="'+e(p.src)+'" width="'+p.width+'" height="'+p.height+'" alt="'+e(p.title)+'" loading="lazy">';
  return '<figure class="plate">'+(link?'<a href="#figur/'+p.id+'">'+img+'</a>':img)+photoCaption(p)+'</figure>';
}
function tabula(){
  const sw=H.records.reduce((n,r)=>n+r.paragraphs.reduce((a,p)=>a+count(p.text),0),0);
  const hs=H.records.map(r=>historical(r.id)).filter(Boolean),hw=hs.reduce((n,h)=>n+count(h.synthesis),0);
  return '<div class="title-spread"><section class="title-leaf"><p class="eyebrow">Organ for de Autonome Videnskaber</p><h1>Summa<br>Transscriptus</h1><p class="subtitle">Disputter over Computer Lars-spektaklet</p><p class="imprint">Under Bugten<br>Aarhus Bugt Center for Kunst<br>Det Jyske Kunstakademi · september 2023</p><p class="source-line">Hyperbog · udkast 01<br>'+num(sw)+' ord i læseudgaven / '+num(hw)+' ord i '+hs.length+' synteser fra 2023</p></section>'+photo(H.photos[1])+'</div>'+
    '<div class="contents-spread"><div><h2>Disputationerne</h2><ol class="chapter-entries">'+H.groups.map(g=>'<li><span class="roman">'+roman[g.number-1]+'</span><div><a class="chapter-title" href="#disput/'+g.records[0]+'">'+e(g.guest)+'<br>og Computer Lars</a><p class="meta">'+e(g.date)+' · '+g.records.length+' optagelser</p><p class="files">'+refLink(g.path+'/reading.docx','Word')+' · '+refLink(g.path+'/reading.md','Læsetekst')+'</p></div></li>').join('')+'</ol></div><div class="tabula-gloss"><p class="eyebrow">Rammetekst · samledokumentet §14</p><blockquote>»Synspunkter genereres i en maskinel proces, og formålet er konditioneret sandhed, ikke blot mening eller holdning.«</blockquote>'+sourceLine('manuscript.html#p14','Ramme og manuskript')+'<ul class="cross-list">'+H.pairs.map((p,i)=>'<li><a href="#sammen/'+p.id+'">'+roman[i]+' · '+e(p.title)+'</a><span class="meta">'+p.left.id+' / '+p.right.id+'</span></li>').join('')+'</ul><p class="fine-rule">'+refLink('#figurer','Figurer og fotografier')+'<br>'+refLink('#ars','Anagrammer af Computer Lars')+'<br>'+refLink('#synteser','Syntesernes række')+'<br>'+refLink('#register','Register over læseteksten')+'</p></div></div>'+folioFoot();
}
function folioFoot(){
  return '<div class="folio-foot">'+refLink('manuscript.html','Samledokument')+refLink('collation.html','Kilder og læsemåder')+refLink('documentation/hyperbook-sources.json','Kildegrundlag')+refLink('index.html','Arkiv og lyd')+refLink('https://github.com/ComputerLars/Summa-Transscriptus/tree/codex/retranscription-review','GitHub')+'</div>';
}
function sideIndex(id){
  return '<aside class="side-nav" aria-label="Disputationernes teser">'+H.groups.map(g=>'<details '+(g.records.includes(id)?'open':'')+'><summary>'+roman[g.number-1]+' · '+e(g.guest)+'</summary><ol>'+g.records.map(sid=>'<li><a href="#disput/'+sid+'" '+(id===sid?'aria-current="true"':'')+'>'+e(records.get(sid).title)+'</a></li>').join('')+'</ol></details>').join('')+'</aside>';
}
function turn(r,p,{compact=false,selected=false}={}){
  return '<section class="record-turn'+(selected?' selected':'')+'" id="p-'+e(p.id)+'">'+(!compact?'<button class="gloss-button" data-gloss="'+e(r.id+'/'+p.id)+'" aria-label="Glosse til '+e(p.id)+'">§</button>':'')+'<div class="turn-meta"><span>'+e(p.speaker)+'</span><button class="time-button" data-audio="'+r.id+'" data-time="'+p.start+'" aria-label="Lyt '+e(r.id)+' fra '+clock(p.start)+'">'+clock(p.start)+'</button><span>'+e(p.id)+'</span></div><p class="speech">'+e(p.text)+'</p></section>';
}
function sourceObservation(n){
  return '<section class="gloss-block"><p class="eyebrow">Glosse · redaktion 2026</p><h3>'+e(n.title)+'</h3><p>'+e(n.note)+'</p>'+(n.variants||[]).map(v=>'<span class="meta">'+e(v.label)+'</span><blockquote>'+e(v.text)+'</blockquote>').join('')+(n.references||[]).map(id=>{const ref=H.collation.references.find(r=>r.id===id);return ref?sourceLine(ref.url,ref.citation):''}).join('')+'<p class="source-line">'+refLink('collation.html#'+n.id,'Kildesammenholdelse')+'</p><button data-loop="'+e(n.source_id)+'" data-from="'+n.start+'" data-to="'+n.end+'">Gentag '+clock(n.start)+'–'+clock(n.end)+'</button></section>';
}
function recordGloss(r,p){
  const d=H.collation.records[r.id];let out='<h2>Glosse</h2>';
  const entries=noteEntries(r.id,p?.unit_id);
  if(p){
    out+='<section class="gloss-block"><p class="meta">'+e(p.id)+' · '+clock(p.start)+'</p>';
    const checks=H.collation.checks.filter(x=>hasUnit(p,x.unit_id));
    if(checks.length)out+='<p>'+checks.map(x=>e(x.phrase)).join(' · ')+'</p>';
    out+='<label class="meta" for="local-reading">Lokal læsning</label><textarea class="local-note" id="local-reading" data-note="'+e(p.id)+'" data-source="'+r.id+'">'+e(localNotes[p.id]?.text||'')+'</textarea><p><button data-export-notes>Hent lokale noter</button></p></section>';
  }
  out+=entries.map(sourceObservation).join('');
  for(const w of d?.written||[])out+='<section class="gloss-block"><p class="eyebrow">'+e(w.label)+'</p><blockquote>'+e(w.text)+'</blockquote>'+sourceLine(w.url,'Samledokumentet · afsnit '+w.paragraph)+'</section>';
  if(d?.historical)out+='<section class="gloss-block"><p class="eyebrow">Syntese · 2023</p><blockquote>'+e(d.historical.synthesis)+'</blockquote>'+sourceLine(d.historical.url,d.historical.filename)+'</section>';
  if(d?.related?.length)out+='<section class="gloss-block"><p class="eyebrow">Se også</p>'+d.related.map(x=>'<p>'+readingLink(x.id,x.id+' · '+x.title)+'</p>').join('')+'</section>';
  const comparisons=H.pairs.filter(x=>x.left.id===r.id||x.right.id===r.id);
  if(comparisons.length)out+='<section class="gloss-block"><p class="eyebrow">Sammenstillinger</p>'+comparisons.map(x=>'<p>'+refLink('#sammen/'+x.id,x.title)+'</p>').join('')+'</section>';
  return out;
}
function disput(id,unit){
  const r=records.get(id)||H.records[0];const p=unit?r.paragraphs.find(p=>p.id===unit||hasUnit(p,unit)):null;
  const i=H.records.indexOf(r),prev=H.records[i-1],next=H.records[i+1];
  return '<div class="read-layout">'+sideIndex(r.id)+'<article class="read-leaf"><header class="record-head"><p class="eyebrow">Disput '+roman[r.group-1]+' · '+r.id+'</p><h1 class="record-title">'+e(r.title)+'</h1>'+recordMeta(r)+'<p class="source-line">'+e(r.path)+' · '+r.duration+'<br>'+refLink('index.html#'+r.id,'Læseudgave og lyd')+' · '+refLink(r.original,'Originaloptagelse')+' · <button class="print-link" data-print>Udskriv</button></p></header>'+r.paragraphs.map(x=>turn(r,x,{selected:p?.id===x.id})).join('')+'<nav class="end-turn" aria-label="Forrige og næste disput">'+(prev?readingLink(prev.id,'← '+prev.id):'<span></span>')+(next?readingLink(next.id,next.id+' →'):'')+'</nav></article><aside class="gloss-leaf">'+recordGloss(r,p)+'</aside></div>';
}
function compareLeaf(spec){
  const r=records.get(spec.id),d=H.collation.records[spec.id];let body='';
  if(spec.layer==='synthesis')body='<p class="eyebrow">Syntese · 2023</p><blockquote>'+e(d.historical.synthesis)+'</blockquote>'+sourceLine(d.historical.url,d.historical.filename);
  else if(spec.layer==='written')body=(d.written||[]).map(w=>'<p class="eyebrow">'+e(w.label)+'</p><blockquote>'+e(w.text)+'</blockquote>'+sourceLine(w.url,'Samledokumentet · afsnit '+w.paragraph)).join('');
  else body='<p class="eyebrow">Fremført ordlyd · læseudgave 2026</p>'+selectedParagraphs(r,spec.units).map(p=>turn(r,p,{compact:true})).join('');
  return '<article class="compare-leaf"><p class="meta">'+e(r.id+' · '+r.date)+'</p><h2>'+e(r.title)+'</h2>'+recordMeta(r)+body+'<p class="source-line">'+readingLink(r.id,'Læs hele disputten')+'</p></article>';
}
function sammen(id){
  const pair=H.pairs.find(p=>p.id===id)||H.pairs[0];
  const notes=H.collation.entries.filter(n=>pair.notes.includes(n.id));
  return '<header class="compare-head"><p class="eyebrow">Sammenstilling · redaktion 2026</p><h1>'+e(pair.title)+'</h1><nav class="case-nav" aria-label="Sammenstillinger">'+H.pairs.map((p,i)=>'<a href="#sammen/'+p.id+'" '+(p.id===pair.id?'aria-current="true"':'')+'>'+roman[i]+' · '+e(p.title)+'</a>').join('')+'</nav></header><div class="compare-spread">'+compareLeaf(pair.left)+compareLeaf(pair.right)+'</div><aside class="comparison-gloss">'+notes.map(sourceObservation).join('')+'</aside>'+folioFoot();
}
function figurer(){
  return '<p class="eyebrow">Dokumentationsarkiv / samledokument</p><h1 class="route-title">Figurer og fotografier</h1><div class="plate-register">'+H.photos.map(p=>'<figure><a href="#figur/'+p.id+'"><img src="'+p.src+'" alt="'+e(p.title)+'" loading="lazy"></a>'+photoCaption(p)+'</figure>').join('')+H.figures.map(f=>'<figure><a href="#figur/'+f.id+'"><img src="'+f.src+'" alt="'+e(f.title)+'" loading="lazy"></a>'+figureCaption(f)+'</figure>').join('')+'</div>'+folioFoot();
}
function figur(id){
  const f=H.figures.find(f=>f.id===id),p=H.photos.find(p=>p.id===id);
  if(p)return '<article class="plate-view"><p class="eyebrow">Dokumentationsarkivet</p><h1>'+e(p.title)+'</h1>'+photo(p,false)+'<p class="source-line">'+refLink('#figurer','Alle figurer og fotografier')+'</p></article>'+folioFoot();
  if(!f)return figurer();
  return '<article class="plate-view"><p class="eyebrow">Samledokumentet · afsnit '+f.paragraph+'</p><h1>'+e(f.title)+'</h1><figure><a href="'+f.src+'"><img src="'+f.src+'" alt="'+e(f.title)+'"></a>'+figureCaption(f)+'</figure><div class="context-grid">'+f.context.map(c=>'<div><p class="meta">Samledokumentet · §'+c.paragraph+'</p><blockquote>'+e(c.text)+'</blockquote>'+sourceLine('manuscript.html#p'+c.paragraph,'Forlæg')+'</div>').join('')+'</div><p class="source-line">'+refLink('#figurer','Alle figurer')+' · '+refLink('#ars','Permutationer')+'</p></article>'+folioFoot();
}
function ars(){
  const n=H.collation.entries.find(n=>/13!|6.227|3.113/.test(n.note+(n.variants||[]).map(x=>x.text).join('')));
  return '<article class="ars-view"><p class="eyebrow">Samledokumentets fire navne</p><h1>Anagrammer af<br>Computer Lars</h1><div class="letter-field" id="letter-field" aria-hidden="true"></div><p class="meta" id="anagram-label" aria-live="polite">Computer Lars</p><div class="anagram-options" aria-label="Navne fra samledokumentet">'+['Computer Lars','Marcel Proust','Carol Stumper','Corrupt Males'].map((s,i)=>'<button data-anagram="'+s+'" aria-pressed="'+(i===0)+'">'+s+'</button>').join('')+'</div><p class="source-line">'+refLink('manuscript.html#p47','Navnene i samledokumentet')+' · '+refLink('#figur/dueller','De seks sammenligninger')+' · '+readingLink('D3-02','Computer Lars’ etymologi')+'</p><figure class="source-figure"><a href="#figur/anagrammer"><img src="sources/under-bugten/image6.png" alt="'+e(H.figures[0].title)+'"></a>'+figureCaption(H.figures[0])+'</figure>'+(n?'<div class="numeric-note">'+sourceObservation(n)+'</div>':'')+'</article>'+folioFoot();
}
function animateLetters(name,animate=true){
  const field=document.getElementById('letter-field');if(!field)return;
  if(!field.children.length)for(const [i,c]of [...'COMPUTERLARS'].entries()){const span=document.createElement('span');span.textContent=c;span.dataset.char=c;span.dataset.index=i;field.append(span)}
  const pool=Array.from(field.children),available=[...pool],style=getComputedStyle(pool[0]),canvas=document.createElement('canvas'),ctx=canvas.getContext('2d');
  let size=parseFloat(style.fontSize);ctx.font=size+'px Georgia';let width=ctx.measureText(name.toUpperCase()).width;const scale=Math.min(1,(field.clientWidth-12)/width);size*=scale;ctx.font=size+'px Georgia';width=ctx.measureText(name.toUpperCase()).width;let x=(field.clientWidth-width)/2;
  for(const char of name.toUpperCase()){
    const advance=ctx.measureText(char).width;
    if(char!==' '){const i=available.findIndex(s=>s.dataset.char===char);if(i<0)throw new Error('Not a permutation: '+name);const span=available.splice(i,1)[0];span.style.fontSize=size+'px';const previous=span.style.transform||'translateX('+x+'px)',target='translateX('+x+'px)';span.getAnimations().forEach(a=>a.cancel());span.style.transform=target;if(animate&&!matchMedia('(prefers-reduced-motion: reduce)').matches)span.animate([{transform:previous},{transform:target}],{duration:1150,easing:'cubic-bezier(.2,.7,.2,1)'});}
    x+=advance;
  }
  if(available.length)throw new Error('Incomplete permutation: '+name);
  field.dataset.name=name;document.getElementById('anagram-label').textContent=name;
  document.querySelectorAll('[data-anagram]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.anagram===name)));
}
function synteser(){
  return '<article class="synthesis-index"><p class="eyebrow">Bevarede synteser · september 2023</p><h1>Syntesernes række</h1><p class="source-line">48 synteser · 1.245 ord · '+refLink('https://github.com/ComputerLars/Summa-Transscriptus/tree/codex/retranscription-review/archive/2023','Historiske TXT-filer')+'</p>'+H.groups.map(g=>'<section class="synthesis-section"><h2>'+roman[g.number-1]+' · '+e(g.guest)+'</h2>'+g.records.map(id=>{const h=historical(id),r=records.get(id);return '<section class="synthesis-entry"><div class="meta">'+readingLink(id,id)+'<br>'+e(g.date)+(h?'<br>'+refLink(h.url,'Kildefil'):'')+'</div><div><p>'+e(h?h.synthesis:'Ingen tilknyttet syntesefil i det bevarede materiale.')+'</p><p class="source-line">'+readingLink(id,r.title)+'</p></div></section>'}).join('')+'</section>').join('')+'</article>'+folioFoot();
}
function register(query=''){
  return '<article class="register-view"><p class="eyebrow">På tværs af de fire disputter</p><h1>Register</h1><form class="search-line" id="search-form"><input id="global-search" type="search" aria-label="Søg i læseteksten" placeholder="Ord, navn eller formulering" value="'+e(query)+'"><button>Søg</button></form><div class="term-list">'+['lumpenintelligentsia','dømmekraft','Proust','tredjehed','dialektik','chips','klient'].map(s=>'<button data-term="'+s+'">'+s+'</button>').join('')+'</div><p class="meta" id="result-count"></p><div id="results"></div></article>'+folioFoot();
}
function search(query){
  const q=query.trim().toLocaleLowerCase('da'),out=document.getElementById('results');if(!out)return;
  if(!q){out.innerHTML=H.groups.map(g=>'<section class="synthesis-section"><h2>'+roman[g.number-1]+' · '+e(g.guest)+'</h2><ol>'+g.records.map(id=>'<li>'+readingLink(id,records.get(id).title)+'</li>').join('')+'</ol></section>').join('');document.getElementById('result-count').textContent='49 optagelser · læseudgaver redigeret oktober 2026';return;}
  const hits=[];for(const r of H.records)for(const p of r.paragraphs)if(p.text.toLocaleLowerCase('da').includes(q))hits.push({r,p});
  document.getElementById('result-count').textContent=hits.length+' afsnit med »'+query+'«';
  out.innerHTML=hits.slice(0,60).map(({r,p})=>{const at=p.text.toLocaleLowerCase('da').indexOf(q),start=Math.max(0,at-200),end=Math.min(p.text.length,at+q.length+360),slice=p.text.slice(start,end),relative=at-start;
    return '<section class="search-result"><p class="meta">'+e(r.id+' · '+p.speaker)+' · '+clock(p.start)+'</p><h2>'+refLink('#disput/'+r.id+'/'+p.id,r.title)+'</h2><p class="result-text">'+(start?'[…] ':'')+e(slice.slice(0,relative))+'<mark>'+e(slice.slice(relative,relative+q.length))+'</mark>'+e(slice.slice(relative+q.length))+(end<p.text.length?' […]':'')+'</p><p class="source-line">'+refLink('#disput/'+r.id+'/'+p.id,'Læs hele afsnittet')+' · <button class="time-button" data-audio="'+r.id+'" data-time="'+p.start+'">Lyt '+clock(p.start)+'</button></p></section>';
  }).join('')+(hits.length>60?'<p class="source-line">De første 60 af '+hits.length+' afsnit. Afgræns med flere ord.</p>':'');
}

async function playAt(id,time,until=null){
  const r=records.get(id);if(!r)return;
  const request=++audioRequest;repeatRange=until&&until>time?{from:time,to:Math.min(until,r.seconds)}:null;
  document.getElementById('stop-loop').hidden=!repeatRange;
  document.getElementById('sound-desk').hidden=false;document.getElementById('sound-title').textContent=r.id+' · '+r.guest+' · '+clock(time)+(repeatRange?'–'+clock(repeatRange.to):'');document.getElementById('sound-original').href=r.original;
  if(currentTrack!==id){sound.pause();currentTrack=id;sound.src=r.audio;sound.load()}
  const begin=()=>{if(request!==audioRequest)return;sound.currentTime=Math.max(0,time);sound.playbackRate=Number(document.getElementById('speed').value);sound.play().catch(()=>{})};
  if(sound.readyState>=1)begin();else sound.addEventListener('loadedmetadata',begin,{once:true});
}
sound.ontimeupdate=()=>{if(repeatRange&&sound.currentTime>=repeatRange.to)sound.currentTime=repeatRange.from};
document.getElementById('speed').onchange=event=>{sound.playbackRate=Number(event.target.value)};
document.getElementById('back-sound').onclick=()=>{sound.currentTime=Math.max(0,sound.currentTime-5)};
document.getElementById('stop-loop').onclick=()=>{repeatRange=null;document.getElementById('stop-loop').hidden=true};
document.getElementById('close-sound').onclick=()=>{audioRequest++;sound.pause();repeatRange=null;document.getElementById('sound-desk').hidden=true};
function exportNotes(){const blob=new Blob([JSON.stringify({archive:'Under Bugten',date:new Date().toISOString(),notes:localNotes},null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='Under-Bugten-lokale-noter.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),500)}

book.addEventListener('click',event=>{
  const b=event.target.closest('button');if(!b)return;
  if(b.dataset.audio)playAt(b.dataset.audio,Number(b.dataset.time));
  else if(b.dataset.loop)playAt(b.dataset.loop,Number(b.dataset.from),Number(b.dataset.to));
  else if(b.dataset.gloss)location.hash='disput/'+b.dataset.gloss;
  else if(b.dataset.anagram)animateLetters(b.dataset.anagram);
  else if(b.dataset.term){document.getElementById('global-search').value=b.dataset.term;search(b.dataset.term);history.replaceState(null,'','#register/'+encodeURIComponent(b.dataset.term))}
  else if(b.hasAttribute('data-export-notes'))exportNotes();
  else if(b.hasAttribute('data-print'))window.print();
});
book.addEventListener('input',event=>{
  const input=event.target;
  if(input.dataset.note){localNotes[input.dataset.note]={source_id:input.dataset.source,text:input.value,date:new Date().toISOString()};try{localStorage.setItem('summa-reading-notes',JSON.stringify(localNotes))}catch(_){}}
});
book.addEventListener('submit',event=>{if(event.target.id==='search-form'){event.preventDefault();const q=document.getElementById('global-search').value;search(q);history.replaceState(null,'','#register/'+encodeURIComponent(q))}});

function renderRoute(){
  if(!H)return;const version=++routeVersion;const parts=location.hash.slice(1).split('/').map(decodeURIComponent),mode=parts[0]||'tabula',id=parts[1],unit=parts[2];let output;
  if(mode==='disput')output=disput(id,unit)+folioFoot();
  else if(mode==='sammen')output=sammen(id);
  else if(mode==='figurer')output=figurer();
  else if(mode==='figur')output=figur(id);
  else if(mode==='ars')output=ars();
  else if(mode==='synteser')output=synteser();
  else if(mode==='register')output=register(id||'');
  else output=tabula();
  book.innerHTML=output;document.title='Summa Transscriptus · '+({disput:records.get(id)?.title,sammen:H.pairs.find(p=>p.id===id)?.title,figurer:'Figurer',figur:'Figur',ars:'Permutationer',synteser:'Syntesernes række',register:'Register'}[mode]||'Hyperbog');
  document.querySelectorAll('.book-nav a').forEach(a=>{if(a.dataset.mode===mode||mode==='figur'&&a.dataset.mode==='figurer')a.setAttribute('aria-current','page');else a.removeAttribute('aria-current')});
  window.scrollTo(0,0);
  if(mode==='ars')requestAnimationFrame(()=>{if(version===routeVersion)animateLetters('Computer Lars',false)});
  if(mode==='register')search(id||'');
  if(mode==='disput'&&unit)requestAnimationFrame(()=>{const p=records.get(id)?.paragraphs.find(p=>p.id===unit||hasUnit(p,unit));if(p)document.getElementById('p-'+p.id)?.scrollIntoView({block:'start'})});
}
window.addEventListener('hashchange',renderRoute);
window.addEventListener('resize',()=>{const f=document.getElementById('letter-field');if(f?.dataset.name)animateLetters(f.dataset.name,false)});

/* Keep manual edits in the canonical Markdown available to the hyperbook too. */
async function hydrateReadings(){
  await Promise.allSettled(H.groups.map(async group=>{
    const response=await fetch(group.path+'/reading.md',{cache:'no-store'});if(!response.ok)return;const source=await response.text();
    const parsed=new Map(group.records.map(id=>[id,[]]));let current=null,anchors=[],speaker=null,start=0,body=[];
    const flush=()=>{const text=body.join('\n').trim();if(current&&speaker&&text){const r=records.get(current),id=anchors[0],unit_id=rootUnit(id),old=r.paragraphs.find(p=>p.id===id);parsed.get(current).push({id,unit_id,joined_units:anchors.slice(1).map(rootUnit),start,end:old?.end||start,speaker,text,uncertain:/\[(uklart|latin utydeligt|muligvis:)/i.test(text)||speaker.includes('[?]')||speaker==='Uidentificeret stemme'})}anchors=[];speaker=null;body=[]};
    for(const line of source.split(/\r?\n/)){
      const h=line.match(/^## (D\d-\d+) · /),a=line.match(/^<a id="([^"]+)"><\/a>$/),s=line.match(/^\*\*(.+?) · (\d\d:\d\d:\d\d)\*\*$/);
      if(h){flush();current=h[1]}else if(a){if(speaker)flush();anchors.push(a[1])}else if(s){if(speaker)flush();speaker=s[1];start=s[2].split(':').reduce((n,x)=>n*60+Number(x),0)}else if(speaker)body.push(line);
    }flush();for(const id of group.records)if(parsed.get(id)?.length)records.get(id).paragraphs=parsed.get(id);
  }));
}
(async()=>{
  try{const response=await fetch('hyperbook-data.json',{cache:'no-store'});if(!response.ok)throw new Error('Kildedata '+response.status);H=await response.json();records=new Map(H.records.map(r=>[r.id,r]));await hydrateReadings();renderRoute()}
  catch(error){book.innerHTML='<section class="error"><h1>Summa Transscriptus</h1><p>'+e(error.message)+'</p><p>'+refLink('index.html','Disputationer og lyd')+'</p></section>';console.error(error)}
})();
