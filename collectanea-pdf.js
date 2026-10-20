/* Client-side PDF typesetting. Source text and notes stay in the browser. */
async function exportBook(){return makePDF(collection.items,collection.title)}
async function exportEdition(){return makePDF([{kind:'frame',id:'praefatio'},{kind:'frame',id:'ordo'},...H.records.map(r=>({kind:'record',id:r.id}))],'Summa Transscriptus')}
async function makePDF(items,title){
 const status=document.getElementById('book-status');
 if(!items.length){if(status)status.textContent='Ingen opslag valgt.';return}
 if(status)status.textContent='PDF sættes …';
 try{
  const {PDFDocument,PDFName,PDFString,rgb}=PDFLib,doc=await PDFDocument.create();
  doc.registerFontkit(fontkit);
  const font=await doc.embedFont(await(await fetch('assets/fonts/DejaVuSansMono.ttf')).arrayBuffer(),{subset:true});
  doc.setTitle(title||'Collectanea');doc.setAuthor('Organ for de Autonome Videnskaber');doc.setCreator('Summa Transscriptus');doc.setSubject('Under Bugten · Disputter over Computer Lars-spektaklet · 2023');
  const W=419.528,Hh=595.276,M=44,B=45,body=9.2,lead=14;
  let page,y,refs=[];
  const newPage=()=>{page=doc.addPage([W,Hh]);y=Hh-M;return page};
  const ensure=n=>{if(!page||y-n<B)newPage()};
  const width=(s,size)=>font.widthOfTextAtSize(s,size);
  const wrap=(text,size=body,available=W-M*2)=>{
   const out=[];let line='';
   for(const word of String(text||'').normalize('NFC').split(/\s+/).filter(Boolean)){
    if(width((line?line+' ':'')+word,size)<=available){line+=(line?' ':'')+word;continue}
    if(line)out.push(line);line='';
    if(width(word,size)<=available)line=word;
    else for(const c of Array.from(word)){if(line&&width(line+c,size)>available){out.push(line);line=''}line+=c}
   }
   if(line)out.push(line);return out;
  };
  const annotation=(p,text,x,yy,size,url)=>{if(!url)return;const a=doc.context.obj({Type:'Annot',Subtype:'Link',Rect:[x,yy-2,x+width(text,size),yy+size+1],Border:[0,0,0],A:{Type:'Action',S:'URI',URI:PDFString.of(url)}});p.node.addAnnot(doc.context.register(a))};
  const draw=(text,size=body,{x=M,url=null,center=false}={})=>{const xx=center?(W-width(text,size))/2:x;page.drawText(text,{x:xx,y,size,font,color:rgb(0,0,0)});annotation(page,text,xx,y,size,url)};
  function para(text,size=body,gap=10,url=null){
   for(const block of String(text||'').split(/\n\s*\n/)){
    const lines=wrap(block,size),lh=size===body?lead:size*1.5;
    if(lines.length>2&&y-Math.min(3,lines.length)*lh<B)newPage();
    for(let i=0;i<lines.length;i++){
     const room=Math.floor((y-B)/lh)+1,remaining=lines.length-i;
     if(room<1||(remaining>room&&room<3)||(remaining>room&&remaining-room<2&&room<=3))newPage();
     draw(lines[i],size,{url});y-=lh;
    }y-=gap;
   }
  }
  const heading=(text,size=12)=>{ensure(65);para(text,size,14)};
  const ref=(label,url)=>{if(!url)return '';let n=refs.findIndex(r=>r.url===url);if(n<0){n=refs.length;refs.push({label,url})}return '['+(n+1)+']'};
  async function image(x){const f=(H.figures.find(f=>f.id===x.id)||H.photos.find(p=>p.id===x.id)||x),bytes=await(await fetch(f.src)).arrayBuffer();const im=/\.png$/i.test(f.src)?await doc.embedPng(bytes):await doc.embedJpg(bytes),scale=Math.min((W-M*2)/im.width,370/im.height),iw=im.width*scale,ih=im.height*scale;ensure(ih+65);page.drawImage(im,{x:(W-iw)/2,y:y-ih,width:iw,height:ih});y-=ih+15;para(f.title+(f.credit?' · '+f.credit:'')+(f.place?'\n'+f.place:''),7.2,12);}
  newPage();y=Hh*.67;
  for(const line of wrap(title||'Collectanea',18,W-M*2)){draw(line,18,{center:true});y-=27}
  y-=22;
  for(const line of ['Under Bugten','Disputter over Computer Lars-spektaklet','Organ for de Autonome Videnskaber','Aarhus · september 2023']){draw(line,8.5,{center:true});y-=17}
  const entries=items.map(item=>({item,x:lookup(item.kind,item.id)})).filter(o=>o.x),toc=[];
  // Reserve accurately measured contents pages before laying out the readings.
  newPage();heading('Indhold',13);let tocpage=page,tocy=y;
  for(let i=0;i<entries.length;i++){
   const lines=wrap((i+1)+'. '+entryTitle(entries[i].x),8.3,W-M*2-30),height=lines.length*12+10;
   if(tocy-height<B){newPage();tocpage=page;tocy=y}
   toc.push({page:tocpage,y:tocy,lines});tocy-=height;
  }
  for(let i=0;i<entries.length;i++){
   const {item,x}=entries[i];newPage();entries[i].page=doc.getPageCount();
   para('OPSLAG '+(i+1)+(x.record?' · '+x.record:''),7.3,13);heading(entryTitle(x),12);
   if(x.kind==='image')await image(x);
   else if(x.kind==='record'){
    const r=records.get(x.id);
    for(const t of r.utterances){ensure(60);para(t.speaker+' · '+clock(t.start),7.4,6,r.audio+'#t='+Math.floor(t.start));for(const b of t.blocks){para(b);if(b.startsWith('Incipere reconstructionem'))para('Oratio latina · rekonstrueret forlæg efter Hans-Jørgen Schanz (1973).',7.2,8,abs('sources/under-bugten/opening-latin.md'))}y-=7}
    const h=historical(x.id);for(const source of H.record_references?.[x.id]||[])para(source.citation+' '+ref(source.citation,abs(source.url)),7.2,8);
    if(h){heading('Maskinsyntese · 2023',10.5);para(h.synthesis);para('Kildetekst '+ref('Syntese · '+x.id,abs(h.url)),7.2,15)}
    else if(x.id==='D4-21'){heading('Maskinsyntese · 2023',10.5);para('Ingen maskinsyntese er bevaret for Metatese 21.')}
   }else if(x.kind==='frame'){
    for(const n of (x.id==='ordo'?[72,74,76,77,78]:Array.from({length:66},(_,i)=>i+4))){const p=manuscriptParagraph(n),f=H.figures.find(f=>f.paragraph===n);if(p?.text.trim())para(p.text);if(f)await image(f)}
   }else{
    if(x.speaker)para(x.speaker+' · '+clock(x.start),7.4,8,records.get(x.record)?.audio+'#t='+Math.floor(x.start));for(const block of x.text.split(/\n\s*\n/)){para(block);if(block.startsWith('Incipere reconstructionem'))para('Oratio latina · rekonstrueret forlæg efter Hans-Jørgen Schanz (1973).',7.2,8,abs('sources/under-bugten/opening-latin.md'))}
   }
   if(item.note){heading('Anmærkning',10.5);para(item.note)}
   const sources=[ref('Locus · '+(x.record||x.title),x.url)];
   if(x.record){const r=records.get(x.record);sources.push(ref('Optagelse · '+x.record,r.original));sources.push(ref('Lyttekopi · '+x.record,r.audio+(x.start!=null?'#t='+Math.floor(x.start):'')))}
   para('Kilder: '+sources.filter(Boolean).join(' '),7.4,10);
  }
  newPage();heading('Kilder',13);
  for(let i=0;i<refs.length;i++){ensure(45);para('['+(i+1)+'] '+refs[i].label,7.4,4,refs[i].url);para(refs[i].url,6.8,13,refs[i].url)}
  ensure(100);heading('Kolofon',11);para('Under Bugten. Aarhus Bugt Center for Kunst, Det Jyske Kunstakademi, 17.–24. september 2023. Læseudgave med lydsteder, skriftlige forlæg og de oprindelige maskinsynteser. Anmærkninger og udvalg følger denne Collectanea.',7.5);
  for(let i=0;i<toc.length;i++){const t=toc[i];for(let k=0;k<t.lines.length;k++)t.page.drawText(t.lines[k],{x:M,y:t.y-k*12,size:8.3,font});t.page.drawText(String(entries[i].page),{x:W-M-width(String(entries[i].page),8.3),y:t.y,size:8.3,font})}
  const outline=doc.context.obj({Type:'Outlines',Count:entries.length}),outlineRef=doc.context.register(outline),outlineItems=entries.map(x=>doc.context.obj({Title:PDFLib.PDFHexString.fromText(entryTitle(x.x)),Parent:outlineRef,Dest:[doc.getPages()[x.page-1].ref,PDFName.of('Fit')]})),outlineRefs=outlineItems.map(x=>doc.context.register(x));
  outlineItems.forEach((x,i)=>{if(i)x.set(PDFName.of('Prev'),outlineRefs[i-1]);if(i+1<outlineRefs.length)x.set(PDFName.of('Next'),outlineRefs[i+1])});if(outlineRefs.length){outline.set(PDFName.of('First'),outlineRefs[0]);outline.set(PDFName.of('Last'),outlineRefs.at(-1));doc.catalog.set(PDFName.of('Outlines'),outlineRef)}
  toc.forEach((t,i)=>{const a=doc.context.obj({Type:'Annot',Subtype:'Link',Rect:[M,t.y-t.lines.length*12,W-M,t.y+11],Border:[0,0,0],Dest:[doc.getPages()[entries[i].page-1].ref,PDFName.of('Fit')]});t.page.node.addAnnot(doc.context.register(a))});
  doc.getPages().forEach((p,i)=>p.drawText(String(i+1),{x:(W-width(String(i+1),8))/2,y:23,size:8,font}));
  const bytes=await doc.save(),url=URL.createObjectURL(new Blob([bytes],{type:'application/pdf'})),a=document.createElement('a');a.href=url;a.download='Summa-Transscriptus-'+(title==='Summa Transscriptus'?'Samlet-udgave':'Collectanea')+'.pdf';a.click();setTimeout(()=>URL.revokeObjectURL(url),60000);if(status)status.textContent=doc.getPageCount()+' sider · PDF';return bytes;
 }catch(err){if(status)status.textContent='PDF kunne ikke dannes: '+err.message;console.error(err);throw err}
}
