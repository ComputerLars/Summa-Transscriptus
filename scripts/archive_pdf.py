"""A5 archive books: linked contents, embedded fonts, whole images and source anchors."""
from pathlib import Path
from xml.sax.saxutils import escape
import re
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.platypus import BaseDocTemplate,PageTemplate,Frame,Paragraph,Spacer,PageBreak,KeepTogether,Image,CondPageBreak
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT,TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from PIL import Image as PILImage

W,H=419.528,595.276
M,T,B=43,47,43
WIDTH=W-2*M

def E(t):return escape(str(t).replace('\u200b','').replace('\ufeff',''),{'"':'&quot;'})
def link(url,text):return '<a href="'+E(url)+'" color="#000000">'+E(text)+'</a>'

class BookDoc(BaseDocTemplate):
 def __init__(self,path,title,author,short,**kwargs):
  super().__init__(str(path),pagesize=(W,H),leftMargin=M,rightMargin=M,topMargin=T,bottomMargin=B,title=title,author=author,**kwargs)
  self.short=short;self.outline_keys=set();self.pass_number=0
  self.addPageTemplates(PageTemplate(id='book',frames=Frame(M,B,WIDTH,H-T-B,id='body',leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0),onPage=self.folio))
 def beforeDocument(self):
  self.outline_keys=set();self.pass_number+=1;self.canv.setCreator(self.author)
 def folio(self,c,d):
  c.saveState();c.setFillColor(HexColor('#444444'));c.setFont('BookMeta',6.4)
  if d.page>1:c.drawString(M,H-27,self.short)
  c.setFillColor(HexColor('#000000'));c.setFont('BookMeta',7.5);c.drawCentredString(W/2,23,str(d.page));c.restoreState()
 def afterFlowable(self,f):
  key=getattr(f,'book_anchor',None)
  if key:
   if hasattr(f,'toc_level'):
    title=getattr(f,'plain_title',f.getPlainText())
    self.notify('TOCEntry',(f.toc_level,E(title),self.page,key))
    if key not in self.outline_keys:
     self.canv.addOutlineEntry(title,key,level=f.toc_level,closed=False);self.outline_keys.add(key)

class Book:
 def __init__(self,root,body='DejaVuSansMono.ttf',italic='DejaVuSansMono-Oblique.ttf',bold='DejaVuSansMono-Bold.ttf',body_size=9,leading=12.3,serif=False):
  self.root=Path(root);self.story=[];self.images=0;self.anchors=set();self.internal_links=[]
  fonts=self.root/'assets/fonts'
  for key,file in [('BookBody',body),('BookItalic',italic),('BookBold',bold),('BookMeta','DejaVuSansMono.ttf')]:pdfmetrics.registerFont(TTFont(key,str(fonts/file)))
  pdfmetrics.registerFontFamily('BookBody',normal='BookBody',italic='BookItalic',bold='BookBold',boldItalic='BookItalic')
  pdfmetrics.registerFontFamily('BookMeta',normal='BookMeta',italic='BookMeta',bold='BookMeta',boldItalic='BookMeta')
  self.styles={
   'body':ParagraphStyle('body',fontName='BookBody',fontSize=body_size,leading=leading,spaceAfter=7,allowWidows=0,allowOrphans=0,splitLongWords=True),
   'meta':ParagraphStyle('meta',fontName='BookMeta',fontSize=7.1,leading=10.5,spaceBefore=9,spaceAfter=5,keepWithNext=True,splitLongWords=True),
   'source':ParagraphStyle('source',fontName='BookMeta',fontSize=7.4,leading=10.5,spaceAfter=6,allowWidows=0,allowOrphans=0,splitLongWords=True),
   'caption':ParagraphStyle('caption',fontName='BookItalic',fontSize=8 if not serif else 9.2,leading=11,spaceBefore=7,spaceAfter=15,alignment=TA_CENTER,allowWidows=0,allowOrphans=0),
   'h1':ParagraphStyle('h1',fontName='BookItalic'if serif else'BookBold',fontSize=17 if serif else 13.3,leading=20 if serif else 18,spaceBefore=0,spaceAfter=17,keepWithNext=True),
   'h2':ParagraphStyle('h2',fontName='BookItalic'if serif else'BookBold',fontSize=13 if serif else 10.5,leading=16 if serif else 14,spaceBefore=17,spaceAfter=10,keepWithNext=True),
   'h3':ParagraphStyle('h3',fontName='BookItalic',fontSize=11 if serif else 9.2,leading=14,spaceBefore=13,spaceAfter=7,keepWithNext=True),
   'cover':ParagraphStyle('cover',fontName='BookItalic'if serif else'BookBody',fontSize=26 if serif else 20,leading=31 if serif else 27,spaceAfter=22,alignment=TA_CENTER),
   'centre':ParagraphStyle('centre',fontName='BookMeta',fontSize=8,leading=12,spaceAfter=12,alignment=TA_CENTER)
  }
 def p(self,text,style='body',raw=False,anchor=None):
  if not str(text).strip():return
  value=text if raw else E(text)
  self.internal_links+=re.findall(r'href=[\'"]#([^\'"]+)',value)
  for alias in re.findall(r'<a\s+name=[\'\"]([^\'\"]+)',value):
   if alias in self.anchors:raise ValueError('Duplicate anchor: '+alias)
   self.anchors.add(alias)
  if anchor:
   if anchor in self.anchors:raise ValueError('Duplicate anchor: '+anchor)
   self.anchors.add(anchor);value='<a name="'+anchor+'"/>'+value
  obj=Paragraph(value,self.styles[style]);self.story.append(obj);return obj
 def heading(self,text,key,level=0,new=False):
  if new and self.story and not isinstance(self.story[-1],PageBreak):self.story.append(PageBreak())
  if level>0:self.story.append(CondPageBreak(130))
  p=self.p(text,'h1'if level==0 else'h2',anchor=key)
  p.book_anchor=key;p.toc_level=level;p.plain_title=text
  return p
 def contents(self,label='Indhold'):
  self.story.append(PageBreak());self.p(label,'h1')
  toc=TableOfContents();toc.levelStyles=[ParagraphStyle('toc0',fontName='BookBody',fontSize=9,leading=13,spaceBefore=9,rightIndent=22),ParagraphStyle('toc1',fontName='BookBody',fontSize=8.2,leading=11.5,leftIndent=12,rightIndent=22,spaceBefore=4)]
  self.story.extend([toc,PageBreak()])
 def image(self,path,caption='',url=None,maxheight=360,anchor=None):
  path=self.root/path
  with PILImage.open(path)as source:
   iw,ih=source.size
   if path.suffix.lower()in('.jpg','.jpeg')and max(iw,ih)>1800:
    source=source.convert('RGB');source.thumbnail((1600,2000),PILImage.Resampling.LANCZOS);encoded=BytesIO();source.save(encoded,format='JPEG',quality=92,optimize=True);encoded.seek(0);image_input=encoded
   else:image_input=str(path)
  scale=min(WIDTH/iw,maxheight/ih);im=Image(image_input,width=iw*scale,height=ih*scale);im.hAlign='CENTER'
  blocks=[]
  if anchor:
   if anchor in self.anchors:raise ValueError(anchor)
   self.anchors.add(anchor);blocks.append(Paragraph('<a name="'+anchor+'"/>',self.styles['source']))
  blocks.append(im)
  if caption:
   lines=str(caption).splitlines()
   blocks.append(Paragraph('<br/>'.join(link(url,line)if url else E(line)for line in lines),self.styles['caption']))
  self.story.append(KeepTogether(blocks));self.images+=1
 def build(self,path,title,author,short):
  missing=set(self.internal_links)-self.anchors
  if missing:raise ValueError('Unresolved internal links: '+repr(missing))
  doc=BookDoc(path,title,author,short,pageCompression=1)
  doc.multiBuild(self.story,maxPasses=8)
  return {'pages':doc.page,'images':self.images,'internal_links':len(self.internal_links),'anchors':len(self.anchors)}
