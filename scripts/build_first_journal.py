#!/usr/bin/env python3
"""Build a deterministic, image-backed first ASStylist Journal issue.

This is a bootstrap issue: the stories are real fashion-industry pages selected
for the launch issue, while images are downloaded from each publisher page
(OG/Twitter/JSON-LD) into the repository. That makes the frontend independent
from hotlinking and prevents a broken remote image from becoming a blank card.
"""
from __future__ import annotations
import html, json, re, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

OUT=Path('frontend/public/journal.json')
IMAGE_DIR=Path('frontend/public/journal-images')
UA='Mozilla/5.0 (compatible; ASStylist-Journal/First-Issue; +https://github.com/karalik19-a11y/asstylist)'
PALETTE=['#F3B61F','#FF5A5F','#7B61FF','#18A999','#FF8A3D','#3A86FF','#C84BFF','#111111']

STORIES=[
 {'title':'NYFW SS27: главные темы сезона и новые имена','source':'Vogue','url':'https://www.vogue.com/article/new-york-fashion-weeks-show-stopping-season','category':'runway','weight':'hero','summary':'Неделя моды в Нью-Йорке завершила сезон показов SS27. В центре внимания оказались новые имена и возвращение крупных домов, а среди заметных направлений — функциональность, выразительная женственность, акцент на талии и переосмысление эстетики 1960-х. Ralph Lauren продолжил работать с американским культурным кодом, а Coach, Carolina Herrera и другие участники показали разные способы соединять коммерческую моду с авторским дизайном. Важная часть сезона — не только отдельные вещи, но и изменение формата самой недели: бренды ищут новые способы презентации коллекций, а календарь становится все плотнее.'},
 {'title':'Ralph Lauren открыл сезон в Нью-Йорке коллекцией SS27','source':'The Guardian','url':'https://www.theguardian.com/fashion/2026/sep/10/ralph-lauren-american-dream-new-york-fashion-week','category':'runway','weight':'major','summary':'Ralph Lauren открыл нью-йоркский fashion month показом SS27, построенным вокруг собственного американского визуального мифа. В коллекции соседствовали бархат, вечерние силуэты, потертый деним, богато обработанные ткани и элементы американской классики. Для бренда это продолжение стратегии, в которой узнаваемый код не отменяет эксперименты с материалами и пропорциями. Показ также показывает, как крупный американский дом продолжает разговаривать с молодой аудиторией через сочетание ностальгии, повседневности и роскоши.'},
 {'title':'CFDA объявил официальное расписание NYFW SS27','source':'CFDA','url':'https://cfda.com/news/view-the-preliminary-september-2026-official-nyfw-schedule/','category':'runway','weight':'major','summary':'Официальное расписание Нью-Йоркской недели моды SS27 включает 70 показов и презентаций. В календаре — Altuzarra, Anna Sui, Calvin Klein Collection, Carolina Herrera, Michael Kors Collection, Proenza Schouler, Tory Burch и другие бренды. Среди новых участников — Magda Butrym, Conner Ives, Sabyasachi и несколько финалистов CFDA/Vogue Fashion Fund. Отдельно важно изменение правил: заявленная CFDA fur-free policy начинает действовать для брендов официального расписания. Неделя проходит с 10 по 15 сентября, а Ralph Lauren показывает коллекцию накануне.'},
 {'title':'Московская неделя моды пройдет 26 сентября — 1 октября','source':'Московская неделя моды','url':'https://www.moscowfashion.ru/','category':'russia','weight':'major','summary':'Седьмая Московская неделя моды пройдет с 26 сентября по 1 октября в Москве. Главной площадкой станет ЦВЗ «Манеж», а программа объединит показы российских и зарубежных дизайнеров, маркет локальных брендов, шоурум, лекторий и фестиваль модных короткометражек World Fashion Shorts. Для локальной индустрии это не только серия дефиле: организаторы одновременно создают пространство для продаж, профессионального нетворкинга и контакта дизайнеров с байерами, прессой и аудиторией. Важный сигнал выпуска — российская мода все сильнее существует как экосистема, а не только как отдельные бренды.'},
 {'title':'В сентябре fashion-индустрия переключается на сезон запусков и коллабораций','source':'ELLE','url':'https://www.elle.com/fashion/a73580840/best-fashion-launches-september-2026/','category':'merch','weight':'standard','summary':'Сентябрь становится для fashion-рынка точкой перезапуска: одновременно стартуют новые коллекции, коллаборации, магазины и специальные продукты. Среди заметных запусков месяца — GapBag от Gap, обновленная версия Shark Pinch boots от Givenchy, совместная работа Celine и Reebok над Freestyle Lo, а также проекты других брендов. Такой календарь показывает, что сегодня модный сезон формируется не только подиумами: продуктовые релизы и коллаборации становятся самостоятельными новостными событиями и способом быстро переводить эстетику бренда в предметы, которые можно купить.'},
 {'title':'Уличный стиль NYFW: цвет, фактура и возвращение выразительных деталей','source':'InStyle','url':'https://www.instyle.com/nyfw-street-style-trends-12114210','category':'social-trends','weight':'standard','summary':'Стритстайл Нью-Йорка показал сезон, в котором базовый гардероб снова становится площадкой для заметных деталей. В подборках вокруг NYFW выделяются chartreuse, животные принты, насыщенный фиолетовый, color blocking, бахрома, пайетки днем, крупные ремни, перчатки и необычные сумки. Одновременно сохраняется интерес к замше, расслабленному тейлорингу и эстетике 1970-х. Для повседневного гардероба это означает не один обязательный тренд, а принцип: знакомый силуэт получает характер за счет цвета, фактуры или аксессуара.'},
 {'title':'Модный сентябрь: трикотаж, кожа, деним и новые расслабленные силуэты','source':'theDay','url':'https://the-day.ru/moda/modnyi-daidzhest-na-sentyabr-2026-obnovlennye-siluety-uyutnyi-trikotazh-i-drugie-trendy-v-kollekciyakh-brendov/','category':'social-trends','weight':'standard','summary':'Начало осеннего сезона заметно по материалам и пропорциям: в коллекциях становится больше шерсти, трикотажа, кожи и многослойности, а расслабленные формы соседствуют с более собранными и приталенными силуэтами. Бренды одновременно обращаются к прошлому — университетской эстетике, спортивной классике, ар-деко и винтажным аксессуарам — но адаптируют эти мотивы к повседневному гардеробу. Получается не буквальная ретро-мода, а переработанная ностальгия, которая работает через материалы, посадку и детали.'},
 {'title':'Главные модные новости сентября: коллаборации, коллекции и новые пространства','source':'Harper’s Bazaar India','url':'https://www.harpersbazaar.in/fashion/story/septembers-biggest-fashion-news-launches-and-collaborations-1445216-2026-09-04','category':'merch','weight':'standard','summary':'Сентябрьский календарь моды заполнен событиями за пределами подиумов: бренды запускают новые коллекции, открывают пространства и объединяются с компаниями из других индустрий. Один из заметных примеров — PUMA x Jaipur Rugs, где классический Suede получает новую цветовую и культурную трактовку через эстетику ремесла. Подобные коллаборации показывают, как спортивная обувь и streetwear продолжают расширять контекст: предмет становится одновременно продуктом, носителем истории и способом работать с локальной культурой.'},
 {'title':'London Fashion Week SS27 готовит следующий этап fashion month','source':'British Fashion Council','url':'https://www.britishfashioncouncil.co.uk/BFCNEWS/5094/THE-BRITISH-FASHION-COUNCIL-ANNOUNCES-PROVISIONAL-SCHEDULE-FOR-LONDON-FASHION-WEEK-SEPTEMBER-2026','category':'runway','weight':'brief','summary':'Лондонская неделя моды SS27 запланирована на 17–21 сентября. British Fashion Council описывает сезон как площадку для новых дизайнеров, возвращения известных британских брендов, коллабораций и коммерческих партнерств. После Нью-Йорка Лондон продолжает fashion month уже с другим набором акцентов: здесь важны молодые марки, экспериментальные форматы и связь между локальной сценой и международным рынком.'},
 {'title':'В Москве назвали даты седьмой Московской недели моды и программу события','source':'Московская неделя моды','url':'https://www.moscowfashion.ru/','category':'russia','weight':'brief','summary':'Российская fashion-сцена готовится к новому сезону Московской недели моды. В программе заявлены показы российских и зарубежных дизайнеров, маркет локальных марок, шоурум, лекции и World Fashion Shorts. Для аудитории ASStylist это особенно полезный формат: рядом с показами появляется место, где можно увидеть локальные бренды, узнать о новых именах и перейти от просмотра образов к реальному знакомству с вещами и дизайнерами.'},
]

def fetch(url,timeout=18):
 req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'text/html,application/xhtml+xml,image/avif,image/webp,*/*;q=0.8','Accept-Language':'ru,en;q=0.8'})
 return urllib.request.urlopen(req,timeout=timeout)

def image_from_page(url):
 try:
  with fetch(url) as r:
   final=r.geturl(); raw=r.read(900000).decode('utf-8','ignore')
 except Exception as e:
  print('[first-journal] page failed',url,e);return None,url
 candidates=[]
 pats=[r'<meta[^>]+(?:property|name)=["\'](?:og:image:secure_url|og:image|twitter:image|twitter:image:src)["\'][^>]+content=["\']([^"\']+)',r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\'](?:og:image:secure_url|og:image|twitter:image|twitter:image:src)["\']']
 for p in pats:
  for m in re.finditer(p,raw,re.I):candidates.append(urllib.parse.urljoin(final,html.unescape(m.group(1))))
 for m in re.finditer(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',raw,re.I|re.S):
  try:
   data=json.loads(html.unescape(m.group(1)));objs=data if isinstance(data,list) else [data]
   for o in objs:
    if isinstance(o,dict):
     img=o.get('image')
     if isinstance(img,str):candidates.append(urllib.parse.urljoin(final,img))
     elif isinstance(img,dict) and isinstance(img.get('url'),str):candidates.append(urllib.parse.urljoin(final,img['url']))
  except Exception:pass
 return (candidates[0] if candidates else None),final

def cache(url,slug):
 if not url:return None
 try:
  with fetch(url,15) as r:
   data=r.read(6000000);ctype=(r.headers.get('Content-Type') or '').lower()
  if len(data)<8000:return None
  if data.startswith(b'\xff\xd8\xff'):ext='.jpg'
  elif data.startswith(b'\x89PNG'):ext='.png'
  elif data[:4]==b'RIFF' and b'WEBP' in data[:16]:ext='.webp'
  elif b'ftypavif' in data[:64]:ext='.avif'
  else:return None
  p=IMAGE_DIR/(slug+ext);p.write_bytes(data);return '/journal-images/'+p.name
 except Exception as e:print('[first-journal] image failed',url,e);return None

def main():
 IMAGE_DIR.mkdir(parents=True,exist_ok=True);articles=[]
 for i,s in enumerate(STORIES):
  img,canonical=image_from_page(s['url']);slug=re.sub(r'[^a-z0-9]+','-',s['title'].lower()).strip('-')[:80] or f'article-{i}'
  local=cache(img,slug)
  a={k:s[k] for k in ('title','source','category','weight','summary')}
  a['id']=slug;a['url']=canonical;a['published_at']=datetime.now(timezone.utc).isoformat();a['tags']=[s['category']];a['editorial_color']=PALETTE[i%len(PALETTE)];a['editorial_weight']=s['weight'];a['editorial']=s['summary'];a['image_url']=local;a['image_fallback_url']=img if not local else None
  articles.append(a)
 payload={'issue':101,'week_start':'2026-09-10','week_end':'2026-09-16','generated_at':datetime.now(timezone.utc).isoformat(),'lead':articles[0]['title'],'trend_note':'Первый выпуск собран как полноценный fashion-дайджест: подиум, локальная сцена, street style, запуски и коллаборации.','articles':articles,'source_count':len(set(s['source'] for s in STORIES)),'russian_share':round(sum(a['category'] in {'russia'} for a in articles)/len(articles),2)}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('[first-journal] wrote',len(articles),'articles with',sum(bool(a['image_url']) for a in articles),'cached images')
if __name__=='__main__':main()
