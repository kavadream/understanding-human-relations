#!/usr/bin/env python3
"""Build only the English translation preview, without changing Chinese artifacts.
Run from the repository root: python3 tools/build_en.py
"""
from pathlib import Path
import json,re,html,hashlib,subprocess,zipfile,shutil,os,sys
from xml.etree import ElementTree as ET
from weasyprint import HTML
import fitz
from fontTools.ttLib import TTFont
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'dist/en'; BUILD=ROOT/'.build/en'; FONT=ROOT/'assets/en/fonts'
OUT.mkdir(parents=True,exist_ok=True); BUILD.mkdir(parents=True,exist_ok=True)
shutil.copytree(FONT,OUT/'fonts',dirs_exist_ok=True)
book=json.loads((ROOT/'translations/en/book.json').read_text());TITLE=book['title'];DATE=book['date'];STEM='English_Understanding_Human_Nature_preview'
chapters=sorted(book['chapters'],key=lambda c:c['display_order'])
PART_IDS={p:f'{n:02}' for n,p in enumerate(dict.fromkeys(c['part'] for c in chapters),1)}
def part_number_title(part):
 a=part.split(' ',2);return ' '.join(a[:2]),a[2]
def readclean(path):
 return path.read_text().replace('〔','[').replace('〕',']').replace('DOI：','DOI:')
clean=[(c,readclean(ROOT/c['file'])) for c in chapters]
MS=ROOT/'translations/en';rights=readclean(MS/'copyright.md');preface=readclean(MS/'preface.md');refs=readclean(MS/'references.md')
text=rights+preface+refs+''.join(t for c,t in clean)
cmap=TTFont(FONT/'ReaderLatin-Regular.ttf').getBestCmap(); missing=sorted({x for x in text if not x.isspace() and ord(x) not in cmap})
if missing:raise RuntimeError('Embedded font update required for: '+repr(missing))
def mdhtml(t):
 return subprocess.run(['pandoc','--from=markdown','--to=html5','--wrap=none'],input=t,text=True,capture_output=True,check=True).stdout

def reference_html(text):
 fragment=mdhtml(text)
 return re.sub(r'(<h2\b.*?)(?=<h2\b|$)',r'<div class="reference-entry">\1</div>',fragment,flags=re.S)

def linkfix(fragment, epub=False):
 fragment=fragment.replace('href="#references"','href="references.xhtml"' if epub else 'href="#references"')
 fragment=re.sub(r'href="#chapter-(\d+)"',lambda m:f'href="chapter-{m.group(1)}.xhtml"' if epub else m.group(0),fragment)
 return fragment

def annotate_notes(fragment,cid):
 fragment=re.sub(r'(<h1[^>]*>)(Chapter \d+) (.*?)(</h1>)',r'\1<span class="chapter-number">\2</span> \3\4',fragment,count=1)
 marker='<p class="notes">'
 if marker not in fragment: return fragment
 a,b=fragment.split(marker,1)
 a=re.sub(r'\[(\d+)\]',lambda m:f'<a class="noteref" href="#note-{cid:02}-{m.group(1)}">[{m.group(1)}]</a>',a)
 seen=set()
 def mark(m):
  n=m.group(1)
  if n in seen: return m.group()
  seen.add(n); return f'<span id="note-{cid:02}-{n}">[{n}]</span>'
 b=re.sub(r'\[(\d+)\]',mark,b)
 return a+marker+b

css=(ROOT/'assets/en/reader.css').read_text()
(BUILD/'reader-en.css').write_text(css)
cover='<section class="cover"><p class="eyebrow">ENGLISH TRANSLATION PREVIEW</p><h1>Understanding<br /> Human Nature</h1><h2>Relationships, Boundaries,<br /> and Cooperation</h2><p class="author">KK</p><p class="edition">2026 · Human language review pending</p></section>'

nav=['<h1>Contents</h1><ul>','<li><a href="#copyright">Copyright and Reading Notice</a></li>','<li><a href="#preface">Preface</a></li>']; last=None
for c in chapters:
 if last!=c['part']:
  pnum=c['part'].split(' ')[0]; nav.append(f'<li class="tocpart"><a href="#part-{PART_IDS[c["part"]]}">{html.escape(c["part"])}</a></li>'); last=c['part']
 nav.append(f'<li class="tocchapter"><a href="#chapter-{c["id"]:02}">Chapter {c["display_order"]}: {html.escape(c["display_title"])}</a></li>')
nav+=['<li class="tocpart"><a href="#references">References and Reading Scope</a></li>','</ul>']; toc=''.join(nav)
sections=[cover,f'<section class="copyright" id="copyright">{mdhtml(rights)}</section>',f'<section class="preface" id="preface">{mdhtml(preface)}</section>',f'<section class="toc" id="toc">{toc}</section>']; last=None
for c,t in clean:
 if c['part']!=last:
  pn,pt=part_number_title(c['part']); sections.append(f'<section class="part" id="part-{PART_IDS[c["part"]]}"><h1><span class="part-number">{pn}</span> {pt}</h1></section>'); last=c['part']
 frag=linkfix(mdhtml(t)); frag=re.sub(r'<p>(<strong>Source notes|Source notes)',r'<p class="notes">\1',frag)
 frag=annotate_notes(frag,c['id'])
 sections.append(f'<section class="chapter" id="chapter-{c["id"]:02}">{frag}</section>')
sections.append(f'<section class="references" id="references">{reference_html(refs)}</section>')
fullhtml='<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>'+TITLE+'</title><meta name="author" content="KK"><style>'+css+'</style></head><body>'+''.join(sections)+'</body></html>'
# Relative font URLs resolve from output/.
(OUT/'reader-en.html').write_text(fullhtml)
os.environ['XDG_CACHE_HOME']=str(BUILD/'cache')
(BUILD/'cache').mkdir(exist_ok=True)
HTML(filename=str(OUT/'reader-en.html')).write_pdf(str(OUT/(STEM+'.pdf')),full_fonts=True)
pdf=fitz.open(OUT/(STEM+'.pdf')); pdf[0].get_pixmap(matrix=fitz.Matrix(2,2),alpha=False).save(str(BUILD/'cover.png')); pdf.close()
# Build EPUB 3 with reading-order spine and hierarchy nav. XHTML pieces come from the same clean text.
EPUB=BUILD/'epub'; shutil.rmtree(EPUB,ignore_errors=True); (EPUB/'META-INF').mkdir(parents=True); (EPUB/'OEBPS/fonts').mkdir(parents=True)
(EPUB/'mimetype').write_text('application/epub+zip'); (EPUB/'META-INF/container.xml').write_text('<?xml version="1.0" encoding="utf-8"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="OEBPS/package.opf" media-type="application/oebps-package+xml"/></rootfiles></container>')
EPUBCSS=css.split('*{box-sizing')[0]+"""body{font-family:ReaderSerif,serif;margin:5%;font-size:1em;line-height:1.6;color:#111}h1,h2,h3{font-weight:700;line-height:1.45;page-break-after:avoid}h1{font-size:1.65em;margin:1em 0}h2{font-size:1.2em;margin:1.6em 0 .7em}h3{font-size:1.05em;margin:1.3em 0 .6em}p{margin:0 0 .7em;orphans:2;widows:2;text-align:left}a{color:inherit;text-decoration:underline}em{font-style:italic}blockquote{margin:0 0 1em;font-size:.9em}hr{border:0;margin:1.3em 0}.cover img{width:100%;height:auto}.part{padding-top:25%}.part h1{font-size:2em}.part-number{display:block;font-size:.55em;margin-bottom:1em}.references p,.copyright p{font-size:.9em}.chapter p.notes{font-size:.85em}.chapter h1{margin-top:1em}.chapter-number{display:block;font-size:.55em;margin-bottom:.8em}nav ol{padding-left:1.5em}nav li{margin-bottom:.5em}nav a{text-decoration:none}"""
(EPUB/'OEBPS/style.css').write_text(EPUBCSS)
for f in FONT.iterdir(): shutil.copy2(f,EPUB/'OEBPS/fonts'/f.name)
shutil.copy2(BUILD/'cover.png',EPUB/'OEBPS/cover.png')
manifest=[]; spine=[]; files=[]
def xhtml(name,title,fragment,properties=None,typ=None):
 fragment=fragment.replace('<hr>', '<hr />').replace('<br>', '<br />')
 content='<?xml version="1.0" encoding="utf-8"?><!DOCTYPE html><html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="en" lang="en"><head><title>'+html.escape(title)+'</title><meta charset="utf-8"/><link rel="stylesheet" type="text/css" href="style.css"/></head><body'+(f' epub:type="{typ}"' if typ else '')+'>'+fragment+'</body></html>'
 (EPUB/'OEBPS'/name).write_text(content); files.append(name); ident=name[:-6]; manifest.append((ident,name,'application/xhtml+xml',properties)); spine.append(ident)
xhtml('cover.xhtml',TITLE,'<section class="cover"><img src="cover.png" alt="Understanding Human Nature: Relationships, Boundaries, and Cooperation. KK. English translation preview, 2026." /></section>',typ='cover')
xhtml('copyright.xhtml','Copyright and Reading Notice','<section class="copyright">'+mdhtml(rights)+'</section>',typ='copyright-page')
xhtml('preface.xhtml','Preface','<section>'+mdhtml(preface)+'</section>',typ='preface')
navxml='<nav epub:type="toc" id="toc"><h1>Contents</h1><ol><li><a href="copyright.xhtml">Copyright and Reading Notice</a></li><li><a href="preface.xhtml">Preface</a></li>'; last=None
for c in chapters:
 if c['part']!=last:
  if last: navxml+='</ol></li>'
  pn=c['part'].split(' ')[0]; navxml+=f'<li><a href="part-{PART_IDS[c["part"]]}.xhtml">{html.escape(c["part"])}</a><ol>'; last=c['part']
 navxml+=f'<li><a href="chapter-{c["id"]:02}.xhtml">Chapter {c["display_order"]} {html.escape(c["display_title"])}</a></li>'
navxml+='</ol></li><li><a href="references.xhtml">References and Reading Scope</a></li></ol></nav><nav epub:type="landmarks" hidden="hidden"><h2>Reading locations</h2><ol><li><a epub:type="bodymatter" href="chapter-01.xhtml">Chapters</a></li><li><a epub:type="bibliography" href="references.xhtml">References</a></li></ol></nav>'
xhtml('nav.xhtml','Contents',navxml,'nav',typ='frontmatter')
last=None
for c,t in clean:
 if c['part']!=last:
  pn,pt=part_number_title(c['part']); xhtml(f'part-{PART_IDS[c["part"]]}.xhtml',c['part'],f'<section class="part"><h1><span class="part-number">{pn}</span> {pt}</h1></section>',typ='part'); last=c['part']
 frag=linkfix(mdhtml(t),True); frag=re.sub(r'<p>(<strong>Source notes|Source notes)',r'<p class="notes">\1',frag)
 frag=annotate_notes(frag,c['id'])
 xhtml(f'chapter-{c["id"]:02}.xhtml',f'Chapter {c["display_order"]} {c["display_title"]}','<section class="chapter">'+frag+'</section>',typ='chapter')
xhtml('references.xhtml','References and Reading Scope','<section class="references">'+reference_html(refs)+'</section>',typ='bibliography')
manifest += [('css','style.css','text/css',None),('cover-image','cover.png','image/png','cover-image'),('font-regular','fonts/ReaderLatin-Regular.ttf','font/ttf',None),('font-bold','fonts/ReaderLatin-Bold.ttf','font/ttf',None),('font-italic','fonts/ReaderLatin-Italic.ttf','font/ttf',None),('font-license','fonts/Noto-Serif-LICENSE.txt','text/plain',None)]
# Include NCX as a compatibility navigation file alongside the normative EPUB3 nav.
ncx='<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1"><head><meta name="dtb:uid" content="urn:uuid:157f3a7b-f1b5-478e-8fe4-532ee09d9f6a"/></head><docTitle><text>'+TITLE+'</text></docTitle><navMap>'
for n,(ident,name,media,prop) in enumerate([m for m in manifest if m[2]=='application/xhtml+xml'],1): ncx+=f'<navPoint id="np{n}" playOrder="{n}"><navLabel><text>{html.escape(ET.parse(EPUB/'OEBPS'/name).find('{http://www.w3.org/1999/xhtml}head/{http://www.w3.org/1999/xhtml}title').text)}</text></navLabel><content src="{name}"/></navPoint>'
ncx+='</navMap></ncx>'; (EPUB/'OEBPS/toc.ncx').write_text(ncx); manifest.append(('ncx','toc.ncx','application/x-dtbncx+xml',None))
opf='<?xml version="1.0" encoding="utf-8"?><package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="book-id" xml:lang="en"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="book-id">urn:uuid:157f3a7b-f1b5-478e-8fe4-532ee09d9f6a</dc:identifier><dc:title>'+TITLE+'</dc:title><dc:creator>KK</dc:creator><dc:language>zh-CN</dc:language><dc:date>'+DATE+'</dc:date><dc:rights>© 2026 KK, to the extent of rights lawfully held. Free reading and noncommercial redistribution of complete unchanged files are permitted. English translation preview; human target-language review pending.</dc:rights><meta property="dcterms:modified">2026-11-02T00:00:00Z</meta><meta name="cover" content="cover-image"/><meta property="schema:accessMode">textual</meta><meta property="schema:accessibilityFeature">tableOfContents</meta></metadata><manifest>'
for ident,name,media,prop in manifest: opf+=f'<item id="{ident}" href="{name}" media-type="{media}"'+(f' properties="{prop}"' if prop else '')+'/>'
opf+='</manifest><spine toc="ncx">'+''.join(f'<itemref idref="{i}"/>' for i in spine)+'</spine></package>'; (EPUB/'OEBPS/package.opf').write_text(opf)
with zipfile.ZipFile(OUT/(STEM+'.epub'),'w') as z:
 zi=zipfile.ZipInfo('mimetype',(2026,11,2,0,0,0)); z.writestr(zi,'application/epub+zip',compress_type=zipfile.ZIP_STORED)
 for f in sorted(EPUB.rglob('*')):
  if f.is_file() and f.name!='mimetype':
   zi=zipfile.ZipInfo(str(f.relative_to(EPUB)),(2026,11,2,0,0,0)); z.writestr(zi,f.read_bytes(),compress_type=zipfile.ZIP_DEFLATED)



for ext in ['epub','pdf']:
 f=OUT/(STEM+'.'+ext);print(f,f.stat().st_size,'bytes',hashlib.sha256(f.read_bytes()).hexdigest())
