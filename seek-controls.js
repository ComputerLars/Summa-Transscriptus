/* Seek controls for the archive's native media players. */
(()=>{
 const da=document.documentElement.lang!=='en';
 const clock=n=>{n=Math.max(0,Math.floor(Number(n)||0));return (n>=3600?Math.floor(n/3600)+':':'')+String(Math.floor(n%3600/60)).padStart(2,'0')+':'+String(n%60).padStart(2,'0')};
 for(const media of document.querySelectorAll('audio,video')){
  if(media.dataset.seekControls)continue;media.dataset.seekControls='true';if(media.getAttribute('src'))media.preload='metadata';
  const row=document.createElement('div');row.className='seek-controls';
  const back=document.createElement('button'),forward=document.createElement('button'),range=document.createElement('input'),position=document.createElement('output');
  back.type=forward.type='button';back.textContent='−10 s';forward.textContent='+10 s';back.setAttribute('aria-label',da?'10 sekunder tilbage':'Back 10 seconds');forward.setAttribute('aria-label',da?'10 sekunder frem':'Forward 10 seconds');
  range.type='range';range.min='0';range.max='0';range.step='0.1';range.value='0';range.setAttribute('aria-label',da?'Søg i optagelsen':'Seek in recording');range.title=da?'Træk for at spole. Piletaster: 1 sekund. Page Up/Down: 10 sekunder. Musehjul når feltet har fokus: 5 sekunder.':'Drag to seek. Arrow keys: 1 second. Page Up/Down: 10 seconds. Mouse wheel when focused: 5 seconds.';
  row.append(back,range,forward,position);media.after(row);let dragging=false;
  function update(){const duration=Number.isFinite(media.duration)?media.duration:0;range.max=String(duration);range.disabled=back.disabled=forward.disabled=!duration;if(!dragging)range.value=String(media.currentTime||0);position.textContent=clock(dragging?range.value:media.currentTime)+' / '+clock(duration);range.setAttribute('aria-valuetext',clock(range.value)+(da?' af ':' of ')+clock(duration));row.hidden=media.hidden;}
  function seek(time){if(!Number.isFinite(media.duration))return;time=Math.max(0,Math.min(media.duration,time));media.dispatchEvent(new CustomEvent('manualseek',{detail:{time}}));media.currentTime=time;range.value=String(time);update();}
  back.onclick=()=>seek(media.currentTime-10);forward.onclick=()=>seek(media.currentTime+10);
  range.addEventListener('pointerdown',()=>dragging=true);range.addEventListener('pointerup',()=>{dragging=false;update()});range.addEventListener('pointercancel',()=>{dragging=false;update()});range.addEventListener('change',()=>{dragging=false;seek(Number(range.value))});range.addEventListener('input',()=>seek(Number(range.value)));
  range.addEventListener('keydown',ev=>{let time;if(ev.key==='ArrowLeft'||ev.key==='ArrowDown')time=media.currentTime-1;else if(ev.key==='ArrowRight'||ev.key==='ArrowUp')time=media.currentTime+1;else if(ev.key==='PageDown')time=media.currentTime-10;else if(ev.key==='PageUp')time=media.currentTime+10;else if(ev.key==='Home')time=0;else if(ev.key==='End')time=media.duration;else return;ev.preventDefault();seek(time)});
  range.addEventListener('wheel',ev=>{if(document.activeElement!==range)return;ev.preventDefault();seek(media.currentTime+Math.sign(ev.deltaY)*(ev.shiftKey?1:5))},{passive:false});
  for(const event of ['loadedmetadata','durationchange','timeupdate','seeked','emptied'])media.addEventListener(event,update);
  new MutationObserver(update).observe(media,{attributes:true,attributeFilter:['hidden']});update();
 }
})();
