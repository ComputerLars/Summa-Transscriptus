/* Source observations remain separate from the recorded speech. */
const text = value => document.createTextNode(value);
const paragraph = (parent, value) => { const p = document.createElement('p'); p.textContent = value; parent.append(p); return p; };
const link = (parent, url, label) => { const a = document.createElement('a'); a.href = url; a.textContent = label; parent.append(a); };
for (const entry of window.COLLATION.entries) {
  const section = document.createElement('section'); section.id = entry.id;
  const heading = document.createElement('h2'); heading.textContent = entry.title; section.append(heading);
  const time = [Math.floor(entry.start / 3600), Math.floor(entry.start / 60) % 60, Math.floor(entry.start) % 60].map(n => String(n).padStart(2, '0')).join(':');
  link(paragraph(section, ''), 'index.html#' + entry.unit_id, entry.source_id + ' · ' + time);
  paragraph(section, entry.note);
  for (const variant of entry.variants || []) {
    const label = document.createElement('b'); label.textContent = variant.label; paragraph(section, '').append(label);
    const quote = document.createElement('blockquote'); quote.textContent = variant.text; section.append(quote);
  }
  for (const id of entry.references || []) {
    const reference = window.COLLATION.references.find(r => r.id === id);
    if (reference) link(paragraph(section, ''), reference.url, reference.citation);
  }
  document.getElementById('entries').append(section);
}
