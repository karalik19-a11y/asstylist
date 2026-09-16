#!/usr/bin/env python3
"""Build ASStylist's weekly fashion editorial.

The journal intentionally prioritizes Russian fashion and local streetwear.
Images are resolved through RSS media, OpenGraph/Twitter metadata and JSON-LD,
then cached into frontend/public/journal-images so the frontend does not depend
on fragile third-party image URLs at render time.
"""
from __future__ import annotations
import html, json, re, urllib.parse, urllib.request, xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

OUT=Path('frontend/public/journal.json'); IMAGE_DIR=Path('frontend/public/journal-images')
USER_AGENT='ASStylist-Journal/3.0 (+https://github.com/karalik19-a11y/asstylist)'

FEEDS=[
 ('russia','российская мода бренды дизайнеры коллекция 2026','Россия'),
 ('russia','российские fashion бренды streetwear релиз коллаборация','Россия'),
 ('russia','мода Москва дизайнеры показ fashion week Россия','Россия'),
 ('russia','РБК Стиль мода бренды дизайнеры','РБК Стиль'),
 ('russia','The Blueprint Россия мода дизайнеры бренды','The Blueprint'),
 ('russia','BURO мода Россия бренды дизайнеры','BURO.'),
 ('russian-streetwear','российский streetwear стритвир бренды дроп','Русский streetwear'),
 ('russian-streetwear','российский кроссовочный рынок streetwear sneaker','Русский streetwear'),
 ('runway','Москва показ коллекция российский дизайнер 2026','Показы'),
 ('merch','российский бренд дроп коллаборация капсула мерч','Мерчи'),
 ('social-trends','TikTok российская мода тренд streetwear','TikTok'),
 ('social-trends','Instagram российские fashion бренды тренды','Instagram'),
 ('world','fashion industry runway designers brands 2026','Мир'),
 ('world','global streetwear fashion trend 2026','Мир'),
]
TRUST={'Vogue':1,'WWD':1,'Hypebeast':.95,'Highsnobiety':.95,'The Blueprint':.98,'BURO.':.95,'РБК Стиль':.92,'РБК':.9,'Коммерсантъ':.9,'Афиша Daily':.85,'Собака.ru':.85,'FashionNetwork':.9,'GQ':.9,'Dazed':.95,'i-D':.9,'Complex':.9}
PALETTE=['#F3B61F','#FF5A5F','#7B61FF','#18A999','#FF8A3D','#3A86FF','#C84BFF','#111111']
RUSSIA_HINTS=['росси','россий','русск','москва','петербург','питер','russia','moscow','st petersburg','локаль','отечествен']
KEYWORDS=['drop','collaboration','capsule','runway','collection','streetwear','trend','sneaker','denim','leather','vintage','archive','silhouette','показ','коллекц','стритвир','мерч','дроп','тренд','бренд','дизайнер']

def clean(s:str)->str:
 s=re.sub(r'<[^>]+>',' ',html.unescape(s or ''));return re.sub(r'\s+',' ',s).strip()
def fetch(url:str,timeout=15,accept='text/html,application/rss+xml,application/xml;q=0.9,*/*;q=0.5'):
 req=urllib.request.Request(url,headers={'User-Agent':USER_AGENT,'Accept':accept});return urllib.request.urlopen(req,timeout=timeout).read()
def parse_date(v:str)->datetime:
 try:
  from email.utils import parsedate_to_datetime
  return parsedate_to_datetime(v).astimezone(timezone.utc)
 except Exception:return datetime.now(timezone.utc)
def text(node,default='')->str:return clean(node.text if node is not None else default)
def google_news_url(q:str)->str:return 'https://news.google.com/rss/search?q='+urllib.parse.quote(q)+'&hl=ru&gl=RU&ceid=RU:ru'

def first_image(item:ET.Element)->str|None:
 for child in item.iter():
  tag=child.tag.rsplit('}',1)[-1]
  if tag in {'content','thumbnail','image'}:
   u=child.attrib.get('url') or child.attrib.get('href')
   if u and u.startswith('http'):return u
  if tag=='enclosure':
   u=child.attrib.get('url','');kind=child.attrib.get('type','')
   if u.startswith('http') and (kind.startswith('image/') or re.search(r'\.(jpg|jpeg|png|webp|avif)(?:$|\?)',u,re.I)):return u
 return None

def page_metadata(url:str)->tuple[str|None,str|None]:
 try:raw=fetch(url,8).decode('utf-8','ignore')[:500000]
 except Exception:return None,None
 candidates=[]
 patterns=[
  r'<meta[^>]+(?:property|name)=["\'](?:og:image:secure_url|og:image|twitter:image)["\'][^>]+content=["\']([^"\']+)',
  r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\'](?:og:image:secure_url|og:image|twitter:image)["\']',
  r'<link[^>]+rel=["\']image_src["\'][^>]+href=["\']([^"\']+)',
  r'<link[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\']image_src["\']',
 ]
 for p in patterns:
  for m in re.finditer(p,raw,re.I):
   u=html.unescape(m.group(1).strip());u=urllib.parse.urljoin(url,u)
   if u.startswith('http'):candidates.append(u)
 for m in re.finditer(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',raw,re.I|re.S):
  try:
   data=json.loads(html.unescape(m.group(1)));stack=data if isinstance(data,list) else [data]
   for obj in stack:
    if isinstance(obj,dict):
     img=obj.get('image')
     if isinstance(img,str):candidates.append(urllib.parse.urljoin(url,img))
     elif isinstance(img,dict) and isinstance(img.get('url'),str):candidates.append(urllib.parse.urljoin(url,img['url']))
     elif isinstance(img,list):candidates.extend([urllib.parse.urljoin(url,x) for x in img if isinstance(x,str)])
  except Exception:pass
 return (candidates[0] if candidates else None),url

def page_article_text(url:str)->str:
 """Extract readable article paragraphs so the journal is a real digest, not an RSS teaser."""
 try:raw=fetch(url,10).decode('utf-8','ignore')[:900000]
 except Exception:return ''
 raw=re.sub(r'<(script|style|noscript|svg|template)[^>]*>.*?</\1>',' ',raw,flags=re.I|re.S)
 blocks=re.findall(r'<(?:article|main)[^>]*>(.*?)</(?:article|main)>',raw,flags=re.I|re.S)
 scope=max(blocks,key=len) if blocks else raw
 paragraphs=[clean(x) for x in re.findall(r'<p\b[^>]*>(.*?)</p>',scope,flags=re.I|re.S)]
 paragraphs=[p for p in paragraphs if len(p)>=45 and not re.search(r'cookie|subscribe|sign in|подписк|реклама|all rights reserved|читать далее',p,re.I)]
 seen=set();out=[]
 for p in paragraphs:
  key=re.sub(r'\W+',' ',p.lower()).strip()
  if key and key not in seen:
   seen.add(key);out.append(p)
 return ' '.join(out[:24])[:9000]

def editorial_brief(title:str,desc:str,source:str,category:str,body:str='')->str:
 """Create a substantially detailed 1.8–2.8k character editorial digest."""
 desc=clean(desc); body=clean(body)
 desc=re.sub(r'\b(read more|continue reading|читать далее)\b.*$','',desc,flags=re.I).strip(' .—–')
 source_text=' '.join(x for x in [desc,body] if x)
 sentences=[s.strip() for s in re.split(r'(?<=[.!?])\s+',source_text) if len(s.strip())>35]
 # Keep enough source material to explain what happened, who is involved and why it matters.
 unique=[];seen=set()
 for s in sentences:
  key=re.sub(r'\W+',' ',s.lower()).strip()
  if key not in seen:
   seen.add(key);unique.append(s)
 base=' '.join(unique[:18]).strip()
 if len(base)<700:
  base=f'{title}. Материал {source} рассматривает эту историю в контексте текущей fashion-сцены. '+base
 lead={'russia':'Что происходит в российской моде: ','russian-streetwear':'Что происходит на локальной streetwear-сцене: ','runway':'Что показали российские дизайнеры: ','merch':'Что вышло у локальных брендов: ','social-trends':'Что набирает внимание в соцсетях: ','world':'Что происходит в мировой моде: '}.get(category,'Что происходит: ')
 # Add an editorially useful closing when the source text itself is short, without inventing facts.
 if len(base)<1300:
  base+='\n\nКонтекст: в этой выжимке собраны только сведения, которые удалось извлечь из открытого материала и его метаданных. Формулировки сохранены максимально близко к фактам первоисточника; детали, которых в публикации нет, не додумываются.'
 if len(base)>2800:base=base[:2800].rsplit(' ',1)[0].rstrip(' ,;:—–')+'…'
 return lead+base

def score(a:dict)->float:
 age=max(0,(datetime.now(timezone.utc)-parse_date(a['published_at'])).total_seconds()/86400);fresh=max(0,1-age/8);words=(a['title']+' '+a['summary']).lower();rel=min(1,sum(k in words for k in KEYWORDS)/5);rus=min(1,sum(k in words for k in RUSSIA_HINTS)/2);source=TRUST.get(a['source'],.62)
 if a['category'] in {'russia','russian-streetwear','runway','merch'}:rus=max(rus,.65)
 return fresh*.38+source*.18+rel*.16+rus*.28

def weight(a:dict,i:int)->str:
 s=score(a);return 'hero' if i==0 or s>=.88 else 'major' if s>=.76 else 'standard' if s>=.62 else 'brief'

def cache_image(url:str|None,article_id:str)->str|None:
 if not url:return None
 try:
  req=urllib.request.Request(url,headers={'User-Agent':USER_AGENT,'Accept':'image/avif,image/webp,image/apng,image/*,*/*;q=0.7'})
  with urllib.request.urlopen(req,timeout=12) as r:
   data=r.read(5_000_000);ctype=(r.headers.get('Content-Type') or '').lower()
  if len(data)<8000:return None
  ext='.jpg' if 'jpeg' in ctype or 'jpg' in ctype else '.png' if 'png' in ctype else '.webp' if 'webp' in ctype else '.avif' if 'avif' in ctype else '.jpg'
  target=IMAGE_DIR/f'{article_id}{ext}';target.write_bytes(data);return f'/journal-images/{target.name}'
 except Exception as e:print(f'[journal] image cache failed: {url}: {e}');return None

def main():
 now=datetime.now(timezone.utc);end=now.date();start=end-timedelta(days=6);raw=[];seen=set()
 IMAGE_DIR.mkdir(parents=True,exist_ok=True)
 for category,q,label in FEEDS:
  try:root=ET.fromstring(fetch(google_news_url(q)))
  except Exception as e:print('[journal] feed failed',label,e);continue
  for item in root.findall('.//item'):
   title=text(item.find('title'));url=text(item.find('link'));published=parse_date(text(item.find('pubDate')))
   if not title or not url or published.date()<start:continue
   source=text(item.find('source')) or 'Открытый источник';key=re.sub(r'[^a-zа-я0-9]','',title.lower())[:180]
   if key in seen:continue
   seen.add(key);summary=text(item.find('description'));img=first_image(item)
   if not img:img,_=page_metadata(url)
   body=page_article_text(url)
   raw.append({'id':key or str(len(raw)),'title':title,'summary':summary[:900],'editorial':editorial_brief(title,summary,source,category,body),'url':url,'source':source,'published_at':published.isoformat(),'category':category,'image_candidate':img,'tags':[label]})
 raw.sort(key=score,reverse=True)
 selected=[];counts=Counter();russian_count=0
 for a in raw:
  cat=a['category']
  if counts[cat]>=6:continue
  selected.append(a);counts[cat]+=1
  if cat in {'russia','russian-streetwear','runway','merch'}:russian_count+=1
  if len(selected)>=32:break
 selected.sort(key=score,reverse=True)
 for i,a in enumerate(selected):
  a['editorial_weight']=weight(a,i);a['editorial_color']=PALETTE[i%len(PALETTE)];candidate=a.pop('image_candidate',None);cached=cache_image(candidate,a['id']);a['image_url']=cached;a['image_fallback_url']=candidate if not cached else None
 corpus=' '.join(a['title']+' '+a['summary'] for a in selected).lower();terms=['oversized','baggy','red','brown','denim','vintage','archive','sneaker','leather','layering','оверсайз','деним','винтаж','архив'];hits=Counter(t for t in terms if t in corpus);trend=hits.most_common(1)[0][0] if hits else 'смешение архивных и новых силуэтов'
 payload={'issue':int(f'{now.isocalendar().year%100:02d}{now.isocalendar().week:02d}'),'week_start':start.isoformat(),'week_end':end.isoformat(),'generated_at':now.isoformat(),'lead':selected[0]['title'] if selected else 'Новый выпуск уже собирается.','trend_note':f'Главный сигнал недели: {trend}. Это частота упоминаний в открытых источниках, а не прогноз.','articles':selected,'source_count':len(FEEDS),'russian_share':round(russian_count/max(1,len(selected)),2)}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(f'[journal] wrote {len(selected)} articles; Russian/local share={payload["russian_share"]:.0%}')
if __name__=='__main__':main()
