#let book = json("/" + sys.inputs.at("data", default: ".book-build/book.json"))
#let serif = book.mode == "defence"
#let body-font = if serif { ("Garamond", "EB Garamond") } else { "DejaVu Sans Mono" }
#let mono = if serif { ("Consolas", "DejaVu Sans Mono") } else { "DejaVu Sans Mono" }
#let body-size = if serif { 10.6pt } else { 8.5pt }
#let accent = if serif { rgb("d60000") } else { black }
#set document(title: book.title, author: book.author, description: book.subtitle)
#set text(font: body-font, size: body-size, lang: book.language, top-edge: 0.8em, bottom-edge: -0.2em, hyphenate: serif)
#set page(paper: "a5", margin: (inside: 20mm, outside: 16mm, top: 18mm, bottom: 20mm), fill: white)
#set par(justify: serif, leading: if serif { 0.25em } else { 0.4em }, spacing: 0.32em, first-line-indent: 1.15em, linebreaks: "optimized")
#set heading(numbering: none)
#let anchor(id) = if id != none { [#metadata(none)#label(id)] }
#let rich(xs) = {
  for x in xs {
    if type(x) == str { x } else if x.t == "link" {
      let dest = if x.url.starts-with("#") { label(x.url.slice(1)) } else { x.url }
      link(dest, rich(x.body))
    } else if x.t == "italic" { emph(rich(x.body))
    } else if x.t == "sup" { super(rich(x.body))
    } else if x.t == "formal" { text(font: mono, fill: accent, rich(x.body))
    } else if x.t == "anchor" { anchor(x.id)
    } else if x.t == "br" { linebreak()
    } else { x.at("text", default: "") }
  }
}
#let quiet(body, size: 7pt) = text(font: mono, size: size, fill: rgb("333333"), body)
#let rule() = line(length: 100%, stroke: 0.35pt + rgb("777777"))
#let meta(body) = block(above: 3.2mm, below: 1.6mm, sticky: true)[
  #set par(first-line-indent: 0pt, justify: false)
  #quiet(body, size: 6.8pt)
]
#let prose(xs, id: none, first: false, role: "body") = {
  let small = role in ("source", "written")
  block(above: 0pt, below: if small { 1.5mm } else { 0.6mm })[
    #set text(font: if small { mono } else { body-font }, size: if small { 7.1pt } else { body-size }, hyphenate: if small { false } else { serif })
    #set par(first-line-indent: (amount: if first or small { 0pt } else { 1.15em }, all: true), justify: if small { false } else { serif })
    #anchor(id)#rich(xs)#parbreak()
  ]
}
#let picture(b) = {
  let max-w = 112mm
  let max-h = b.at("height", default: 120) * 1mm
  let h = calc.min(max-h, max-w * b.pixel-height / b.pixel-width)
  let w = h * b.pixel-width / b.pixel-height
  block(width: 100%, breakable: false, above: 3mm, below: 4mm)[
    #anchor(b.at("id", default: none))
    #align(center, image("/" + b.src, width: w, height: h, alt: b.caption))
    #if b.caption != "" {
      v(1.8mm)
      align(center)[
        #set par(first-line-indent: 0pt, justify: false, leading: 0.35em)
        #text(size: if serif { 8.2pt } else { 7pt }, style: "italic", rich(b.caption-rich))
      ]
    }
  ]
}
#show heading.where(level: 1): it => block(above: 0pt, below: 6mm, sticky: true)[
  #rule()
  #v(5mm)
  #text(size: if serif { 21pt } else { 15pt }, style: if serif { "italic" } else { "normal" }, weight: if serif { "regular" } else { "bold" }, it.body)
]
#show heading.where(level: 2): it => block(above: 6mm, below: 3mm, sticky: true)[
  #text(size: if serif { 14pt } else { 10.1pt }, style: if serif { "italic" } else { "normal" }, weight: if serif { "regular" } else { "bold" }, it.body)
]
#[
  #set par(first-line-indent: 0pt, justify: false)
  #text(font: mono, size: 7pt, fill: accent, book.cover-label)
  #v(if serif { 13mm } else { 29mm })
  #rule()
  #v(7mm)
  #text(font: body-font, size: if serif { 33pt } else { 25pt }, style: if serif { "italic" } else { "normal" }, book.cover-title)
  #v(4mm)
  #text(size: if serif { 22pt } else { 11pt }, style: if serif { "italic" } else { "normal" }, book.cover-subtitle)
  #v(6mm)
  #if serif { quiet(book.author, size: 8pt) }
  #if book.cover-image != none { v(7mm); picture(book.cover-image) }
  #v(1fr)
  #rule()
  #v(3mm)
  #quiet(book.event, size: 7pt)
]
#pagebreak(to: "odd")
#[
  #set par(first-line-indent: 0pt, justify: false)
  #v(25mm)
  #quiet(book.author, size: 8pt)
  #v(13mm)
  #text(size: if serif { 27pt } else { 21pt }, style: if serif { "italic" } else { "normal" }, book.title)
  #v(7mm)
  #text(size: if serif { 13pt } else { 9pt }, hyphenate: false, book.subtitle)
  #v(1fr)
  #quiet(book.event)
  #v(4mm)
  #quiet(book.edition)
]
#pagebreak()
#[
  #set par(first-line-indent: 0pt, justify: false)
  #v(1fr)
  #rule()
  #v(4mm)
  #for p in book.imprint { prose(p, first: true, role: "source") }
  #v(3mm)
  #quiet(link(book.site, book.site))
]
#pagebreak()
#set page(numbering: "i", header: none, footer: context {
  if query(outline.entry).any(e => e.location().page() == here().page()) {
    align(center, quiet(numbering("i", ..counter(page).get()), size: 7pt))
  }
})
#counter(page).update(3)
#outline(title: if serif { "Contents" } else { "Indhold" }, depth: 2)
#pagebreak(to: "odd")
#counter(page).update(1)
#let running-head() = context {
  let physical = here().page()
  let roots = query(heading.where(level: 1)).filter(h => h.location().page() <= physical)
  let subs = query(heading.where(level: 2)).filter(h => h.location().page() <= physical)
  let section-at-top = subs.len() > 0 and subs.last().location().page() == physical and subs.last().location().position().y < 85pt
  if roots.len() > 0 and roots.last().location().page() != physical and not section-at-top {
    let body = if calc.even(counter(page).get().first()) or subs.len() == 0 or subs.last().location().page() < roots.last().location().page() { roots.last().body } else { subs.last().body }
    let name = body.text
    let short = if name.len() > 72 { name.clusters().slice(0, 65).join() + "…" } else { name }
    block(below: 2mm)[
      #quiet(short, size: 6.1pt)
      #v(1.8mm)
      #line(length: 100%, stroke: 0.25pt + rgb("aaaaaa"))
    ]
  }
}
#set page(numbering: "1", header: running-head(), footer: context align(if calc.even(counter(page).get().first()) { left } else { right }, quiet(str(counter(page).get().first()), size: 7.3pt)))
#for b in book.blocks {
  if b.kind == "chapter" {
    pagebreak(weak: true)
    [#heading(level: 1, b.title)#label(b.id)]
    if b.subtitle != "" { prose((b.subtitle,), first: true, role: "source") }
  } else if b.kind == "section" {
    [#heading(level: 2, b.title)#label(b.id)]
    if b.subtitle != "" { prose((b.subtitle,), first: true, role: "source") }
  } else if b.kind == "p" { prose(b.body, id: b.id, first: b.first, role: b.role)
  } else if b.kind == "meta" { meta(rich(b.body))
  } else if b.kind == "turn" {
    meta([#text(weight: "bold", b.speaker) #h(0.6em) #quiet(link(b.url, b.clock), size: 6.6pt)])
    for (i, p) in b.paragraphs.enumerate() { prose(p.body, id: p.id, first: i == 0) }
  } else if b.kind == "written" {
    block(inset: (left: 4mm), above: 2mm, below: 3mm)[
      #meta(rich(b.label))
      #for p in b.paragraphs { prose(p.body, id: p.id, first: true, role: "written") }
    ]
  } else if b.kind == "synthesis" {
    block(above: 4mm, below: 2mm)[
      #block(breakable: false, sticky: true)[
        #line(length: 18mm, stroke: 0.35pt)
        #meta(b.title)
      ]
      #prose((b.text,), id: b.id, first: true)
      #prose(b.source, first: true, role: "source")
    ]
  } else if b.kind == "image" { picture(b)
  } else if b.kind == "break" { pagebreak(weak: true)
  } else if b.kind == "bibliography" {
    block(breakable: false, above: 2mm, below: 2.5mm)[
      #set par(first-line-indent: 0pt, hanging-indent: 1.8em, justify: false)
      #anchor(b.id)
      #text(font: mono, size: 7.1pt, hyphenate: false)[#rich(b.citation)]#parbreak()
      #if b.note != "" { v(1.2mm); prose((b.note,), first: true, role: "source") }
      #if b.backlinks.len() > 0 { prose(b.backlinks, first: true, role: "source") }
    ]
  } else if b.kind == "article" {
    block(breakable: false, above: 3mm, below: 3mm)[
      #meta(text(fill: accent, b.label))
      #text(size: 12pt, style: "italic", link(b.url, b.title))
      #v(2mm)
      #prose(b.body, first: true, role: "source")
    ]
  }
}
