/* Under Bugten. Canonical reading text lives in the Markdown files. */
const DATA = window.ARCHIVE;
const el = id => document.getElementById(id);
let record = null, only = false, raw = false;
const localAudio = new Map();
const all = () => DATA.groups.flatMap(g => g.records);
const escapeHTML = s => { const n = document.createElement('span'); n.textContent = s; return n.innerHTML; };
const seconds = s => s.split(':').reduce((n, x) => n * 60 + Number(x), 0);
const time = s => [Math.floor(s / 3600), Math.floor(s / 60) % 60, Math.floor(s) % 60].map(n => String(n).padStart(2, '0')).join(':');

for (const group of DATA.groups) {
  const option = document.createElement('option');
  option.value = group.name; option.textContent = group.name + ' · ' + group.guest;
  el('group').append(option);
}

function buildIndex() {
  const group = DATA.groups.find(g => g.name === el('group').value);
  el('index').innerHTML = group.records.map(r => '<li><a href="#' + r.source.id + '" data-record="' + r.source.id + '">' + escapeHTML(r.source.title) + '</a></li>').join('');
  el('index').querySelectorAll('a').forEach(a => a.onclick = event => { event.preventDefault(); choose(a.dataset.record); });
  const word = DATA.local_sources ? group.name.replaceAll(' ', '-') + '-' + group.guest.replaceAll(' ', '-') + '-Læseudgave.docx' : group.path + '/reading.docx';
  el('editions').innerHTML = '<a href="' + group.path + '/reading.md">Læsetekst</a> · <a href="' + word + '">Word</a> · <a href="' + group.path + '/timed.md">Tidsforankret tekst</a>';
}

function render() {
  if (!record) return;
  const query = el('search').value.toLocaleLowerCase();
  const paragraphs = raw ? record.raw : record.paragraphs;
  const shown = paragraphs.filter(p => (!only || p.uncertain) && (!query || p.text.toLocaleLowerCase().includes(query) || p.speaker.toLocaleLowerCase().includes(query)));
  el('count').textContent = ' ' + shown.length + ' af ' + paragraphs.length + ' afsnit';
  el('text').innerHTML = shown.map(p => '<section class="passage" id="' + p.id + '" data-start="' + p.start + '"><div class="who">' + escapeHTML(p.speaker) + '<button class="time" data-t="' + p.start + '">' + time(p.start) + '</button></div><p class="speech">' + escapeHTML(p.text) + '</p></section>').join('') || '<p class="empty">Ingen afsnit i denne visning.</p>';
  el('text').querySelectorAll('button').forEach(b => b.onclick = () => play(Number(b.dataset.t)));
  el('uncertain').textContent = only ? 'Vis alle afsnit' : 'Vis kun tvivlspunkter';
  el('mode').textContent = raw ? 'Vis læseudgave' : 'Vis rå genkendelse';
}

function audioSource() {
  const source = record.source;
  const local = localAudio.get(source.id);
  const src = local || (location.protocol === 'file:' && DATA.local_sources ? '../' + source.path.split('/').map(encodeURIComponent).join('/') : source.audio_url || '../' + source.path.split('/').map(encodeURIComponent).join('/'));
  if (el('audio').getAttribute('src') !== src) el('audio').src = src;
  el('source').innerHTML = escapeHTML(source.path) + ' · ' + source.display_duration + (source.drive_url ? ' · <a target="_blank" rel="noopener" href="' + source.drive_url + '">Originaloptagelse</a>' : '');
}

function findParagraph(r, target) {
  return r.paragraphs.find(p => p.id === target || p.unit_id === target || (p.joined_units || []).includes(target));
}

function choose(id, target, seek) {
  const changed = record && record.source.id !== id;
  record = all().find(r => r.source.id === id) || all()[0];
  const group = DATA.groups.find(g => g.records.includes(record));
  el('group').value = group.name; buildIndex();
  el('title').textContent = record.source.id + ' · ' + record.source.title;
  const event = record.source.event;
  el('occasion').textContent = event.date + ' · ' + group.guest + ' og Computer Lars · Praeses';
  audioSource(); render();
  history.replaceState(null, '', '#' + (target || id));
  if (target) {
    const paragraph = findParagraph(record, target);
    if (paragraph) { document.getElementById(paragraph.id)?.scrollIntoView({ block: 'center' }); seek = paragraph.start; }
  }
  if (!target && changed) window.scrollTo({ top: 0 });
  if (seek != null) {
    const apply = () => { el('audio').currentTime = seek; };
    if (el('audio').readyState) apply(); else el('audio').addEventListener('loadedmetadata', apply, { once: true });
  }
  refreshGroup(group);
}

function play(t) {
  const audio = el('audio'); audio.currentTime = Math.max(0, t - 1);
  audio.play().catch(() => {});
  history.replaceState(null, '', '#' + record.source.id + '@' + Math.floor(t));
}

/* Markdown edits on GitHub appear in the reader without rebuilding its data. */
async function refreshGroup(group) {
  if (group.loaded || location.protocol === 'file:') return;
  group.loaded = true;
  try {
    const response = await fetch(group.path + '/reading.md', { cache: 'no-store' });
    if (!response.ok) throw new Error(response.status);
    const text = await response.text();
    let current = null, speaker = null, start = 0, anchors = [], body = [], index = 0;
    const parsed = new Map(group.records.map(r => [r.source.id, []]));
    const flush = () => {
      if (current && speaker && body.length) {
        const content = body.join('\n').trim();
        if (content) parsed.get(current).push({ id: anchors[0] || current + '-P' + (++index), unit_id: anchors[0], joined_units: anchors.slice(1), start, end: start, speaker, text: content, uncertain: /\[(uklart|latin utydeligt|muligvis:)/i.test(content) || speaker === 'Uidentificeret stemme' || speaker.includes('[?]') });
      }
      body = []; speaker = null; anchors = [];
    };
    for (const line of text.split(/\r?\n/)) {
      const sourceHeading = line.match(/^## (D\d-\d+) · /);
      const anchor = line.match(/^<a id="([^"]+)"><\/a>$/);
      const label = line.match(/^\*\*(.+?) · (\d\d:\d\d:\d\d)\*\*$/);
      if (sourceHeading) { flush(); current = sourceHeading[1]; }
      else if (anchor) { if (speaker) flush(); anchors.push(anchor[1]); }
      else if (label) { if (speaker) flush(); speaker = label[1]; start = seconds(label[2]); }
      else if (speaker) body.push(line);
    }
    flush();
    for (const r of group.records) if (parsed.get(r.source.id).length) r.paragraphs = parsed.get(r.source.id);
    if (group.records.includes(record)) {
      render();
      const target = decodeURIComponent(location.hash.slice(1));
      const paragraph = findParagraph(record, target);
      if (paragraph) document.getElementById(paragraph.id)?.scrollIntoView({ block: 'center' });
    }
  } catch (_) { /* The embedded edition remains available offline. */ }
}

el('audio').ontimeupdate = () => {
  const t = el('audio').currentTime;
  let current = null;
  el('text').querySelectorAll('.passage').forEach(p => { if (Number(p.dataset.start) <= t) current = p; p.classList.remove('active'); });
  current?.classList.add('active');
};
el('group').onchange = () => choose(DATA.groups.find(g => g.name === el('group').value).records[0].source.id);
el('search').oninput = render;
el('uncertain').onclick = () => { only = !only; render(); };
el('mode').onclick = () => { raw = !raw; render(); };

const picker = document.createElement('input');
picker.type = 'file'; picker.multiple = true; picker.setAttribute('webkitdirectory', ''); picker.hidden = true;
const chooseFiles = document.createElement('button'); chooseFiles.textContent = 'Vælg lokal lydmappe';
chooseFiles.onclick = () => picker.click();
picker.onchange = () => {
  for (const file of picker.files) {
    const matches = all().filter(r => r.source.bytes === file.size);
    if (matches.length === 1) localAudio.set(matches[0].source.id, URL.createObjectURL(file));
  }
  audioSource();
};
el('audio').after(chooseFiles, picker, document.createElement('br'));

const speed = document.createElement('select'); speed.setAttribute('aria-label', 'Afspilningshastighed');
for (const rate of [0.75, 1, 1.25, 1.5]) { const o = document.createElement('option'); o.value = rate; o.textContent = rate + ' ×'; o.selected = rate === 1; speed.append(o); }
speed.onchange = () => { el('audio').playbackRate = Number(speed.value); };
const back = document.createElement('button'); back.textContent = '−5 s'; back.onclick = () => { el('audio').currentTime = Math.max(0, el('audio').currentTime - 5); };
const forward = document.createElement('button'); forward.textContent = '+5 s'; forward.onclick = () => { el('audio').currentTime = Math.min(el('audio').duration || Infinity, el('audio').currentTime + 5); };
el('audio').after(back, forward, speed);

const hash = decodeURIComponent(location.hash.slice(1));
const [target, clock] = hash.split('@');
const selected = all().find(r => r.source.id === target || findParagraph(r, target));
choose(selected ? selected.source.id : all()[0].source.id, selected && target !== selected.source.id ? target : null, clock == null ? null : Number(clock));
