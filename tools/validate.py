#!/usr/bin/env python3
"""Local structural validation; not a substitute for EPUBCheck or visual QA."""
from pathlib import Path
from zipfile import ZipFile, ZIP_STORED
import json,sys,posixpath,re
from urllib.parse import urlsplit,unquote
from xml.etree import ElementTree as ET
import fitz
ROOT=Path(__file__).resolve().parents[1]; DIST=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'dist'
epub=next(DIST.glob('*读者版.epub')); pdf=next(DIST.glob('*读者版.pdf'))
errors=[]; checks={};ns={'o':'http://www.idpf.org/2007/opf','x':'http://www.w3.org/1999/xhtml','c':'urn:oasis:names:tc:opendocument:xmlns:container'}
with ZipFile(epub) as z:
 names=set(z.namelist()); infos=z.infolist(); assert infos[0].filename=='mimetype' and infos[0].compress_type==ZIP_STORED; assert z.read('mimetype')==b'application/epub+zip'; assert z.testzip() is None
 container=ET.fromstring(z.read('META-INF/container.xml')); opfpath=container.find('c:rootfiles/c:rootfile',ns).get('full-path'); opf=ET.fromstring(z.read(opfpath)); base=posixpath.dirname(opfpath)
 manifest={i.get('id'):i for i in opf.findall('o:manifest/o:item',ns)}; spine=[i.get('idref') for i in opf.findall('o:spine/o:itemref',ns)]
 for idref in spine: assert idref in manifest
 resources={posixpath.join(base,i.get('href')) for i in manifest.values()}; assert resources<=names
 navs=[i for i in manifest.values() if 'nav' in i.get('properties','').split()]; assert len(navs)==1
 docs={}; ids={}
 for name in names:
  if name.endswith(('.xhtml','.opf','.ncx','.xml')):
   try: docs[name]=ET.fromstring(z.read(name))
   except ET.ParseError as e: errors.append(f'Invalid XML {name}: {e}')
 for name,doc in docs.items():
  arr=[e.get('id') for e in doc.iter() if e.get('id')]; ids[name]=set(arr)
  if len(arr)!=len(set(arr)): errors.append('Duplicate ids: '+name)
 links=0
 for name,doc in docs.items():
  if not name.endswith(('.xhtml','.ncx')): continue
  for e in doc.iter():
   for attr in ['href','src']:
    value=e.get(attr)
    if not value: continue
    u=urlsplit(value)
    if u.scheme or value.startswith('//'): continue
    target=posixpath.normpath(posixpath.join(posixpath.dirname(name),unquote(u.path))) if u.path else name
    if target not in names: errors.append(f'Missing resource {name} -> {value}')
    if u.fragment and unquote(u.fragment) not in ids.get(target,set()): errors.append(f'Missing fragment {name} -> {value}')
    links+=1
 checks.update(zip_integrity=True,xml_documents=len(docs),manifest_items=len(manifest),spine_items=len(spine),internal_links_checked=links,epubcheck='not-run')
 epub_text='\n'.join(''.join(d.itertext()) for n,d in docs.items() if n.endswith('.xhtml'))
 for token in ['Sentinel_', '稳定ID：','待用户验收','../../learning/','原样章归档','修订授权及基线映射']:
  if token in epub_text: errors.append('Production token in EPUB: '+token)
 assert len([x for x in resources if re.search(r'/chapter-\d+\.xhtml$',x)])==17
 assert len([x for x in resources if re.search(r'/part-.*\.xhtml$',x)])==6
pd=fitz.open(pdf); checks['pdf_pages']=len(pd); checks['pdf_bookmarks']=len(pd.get_toc()); checks['pdf_internal_links']=sum(sum(l['kind'] in [fitz.LINK_GOTO,fitz.LINK_NAMED] and l.get('page',-1)>=0 for l in p.get_links()) for p in pd); checks['pdf_external_links']=sum(sum(l['kind']==fitz.LINK_URI for l in p.get_links()) for p in pd)
# PDF text inspection supplements but does not replace page-image review.
texts=[p.get_text() for p in pd]
checks['pdf_empty_pages']=[n+1 for n,t in enumerate(texts) if not t.strip()]
if checks['pdf_empty_pages']: errors.append('Blank PDF pages')
checks['pdf_fonts']=sorted({tuple(f[3:6]) for p in pd for f in p.get_fonts()})
for n,p in enumerate(pd):
 for link in p.get_links():
  if link['kind'] in [fitz.LINK_GOTO,fitz.LINK_NAMED] and link.get('page',-1)<0: errors.append(f'Unresolved PDF destination on page {n+1}: {link}')
 for b in p.get_text('blocks'):
  if b[0]<-1 or b[1]<-1 or b[2]>p.rect.width+1 or b[3]>p.rect.height+1: errors.append(f'Out-of-page text on PDF page {n+1}')
e=fitz.open(epub); e.layout(width=420,height=700,fontsize=12); checks['mupdf_epub_open']=True; checks['mupdf_epub_reflow_pages']=len(e); checks['mupdf_epub_toc_entries']=len(e.get_toc())
checks['errors']=errors
print(json.dumps(checks,ensure_ascii=False,indent=2)); sys.exit(bool(errors))
