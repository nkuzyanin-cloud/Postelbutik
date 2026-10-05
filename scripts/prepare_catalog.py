import concurrent.futures, hashlib, json, re, urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
raw_products=json.loads((ROOT/'docs/lux-data.json').read_text())+json.loads((ROOT/'docs/grass-data.json').read_text())
# A model URL and individual size URL may return the same supplier SKU.
unique={}
for p in sorted(raw_products,key=lambda p: ('900postelnoe' not in p['url'],p['url'])):
 old=unique.get(p['id'])
 if old and (old['size']!=p['size'] or old['items']!=p['items']):
  raise RuntimeError('Supplier SKU has conflicting dimensions: '+p['id'])
 if old and old['price']!=p['price']:
  p['warnings'].append('Цена размерного варианта отличается между страницами поставщика. Проверьте исходную карточку.')
 unique[p['id']]=p
products=list(unique.values())

asabella=[
 ('1617-OMP','Цветочный сатин',['Белый','Бирюзовый','Голубой'],'Цветы',13470,'https://asabella.ru/komplekt-s-lyetnim-odeyalom-iz-pechatnogo-satina-200kh220-sm-1617-omp/','https://asabella.ru/wa-data/public/shop/products/00/webp/77/62/146277/images/1315680/1315680.700.webp'),
 ('2224-OMP','Геометрия в тёплых оттенках',['Бежевый','Коричневый','Серый'],'Геометрия',13470,'https://asabella.ru/komplekt-s-letnim-odeyalom-evro-m-iz-pechatnogo-satina-200kh220-sm-2224-omp/','https://asabella.ru/wa-data/public/shop/products/00/webp/64/10/151064/images/1355448/1355448.700.webp'),
 ('2336-OMP','Сатин в клетку',['Бежевый','Зеленый','Серый'],'Геометрия, клетка',13470,'https://asabella.ru/komplekt-s-letnim-odeyalom-odeyalom-iz-satina-s-lazernoy-pechatyu-200kh220-sm-2336-omp/','https://asabella.ru/wa-data/public/shop/products/00/webp/51/34/153451/images/1363834/1363834.700.webp'),
 ('2225-OMP','Сатин в серую полоску',['Серый'],'Геометрия, полосы',14193,'https://asabella.ru/komplekt-s-letnim-odeyalom-evro-m-iz-pechatnogo-satina-200kh220-sm-2225-omp/','https://asabella.ru/wa-data/public/shop/products/00/webp/66/10/151066/images/1355473/1355473.700.webp')
]
asabella.extend([
 ('2111-OMP','Premium · серая геометрия',['Серый'],'Геометрия',18910,'https://asabella.ru/komplekt-s-letnim-odeyalom-iz-egipetskogo-khlopka-premium-200kh220-sm-2111-omp/','https://asabella.ru/wa-data/public/shop/products/00/webp/85/53/145385/images/1313223/1313223.700.webp'),
 ('1380-OMP','Premium · зелёные листья',['Зеленый','Молочный'],'Цветы, листья',17020,'https://asabella.ru/komplekt-s-letnim-odeyalom-evro-iz-egipetskogo-khlopka-premium-200kh220-sm-1380-omp/','https://asabella.ru/wa-data/public/shop/products/00/webp/80/53/145380/images/1313187/1313187.700.webp'),
 ('2400-OMP','Твил · цветочный рисунок',['Лиловый','Молочный'],'Цветы',13760,'https://asabella.ru/komplekt-s-lyetnim-odeyalom-iz-tvila-200kh220-sm-2400-omp/','https://asabella.ru/wa-data/public/shop/products/00/webp/60/36/153660/images/1365472/1365472.700.webp'),
 ('2181-OMP','Premium · бежевые цветы',['Белый','Бежевый'],'Цветы',17020,'https://asabella.ru/komplekt-s-letnim-odeyalom-evro-iz-egipetskogo-khlopka-premium-200kh220-sm-2181-omp/','https://asabella.ru/wa-data/public/shop/products/00/webp/53/00/150053/images/1352111/1352111.700.webp'),
 ('2306-OMP','Фланель · пионы',['Бежевый','Серый'],'Цветы, листья',13380,'https://asabella.ru/komplekt-s-letnim-odeyalom-iz-flaneli-egipetskiy-khlopok-200kh220-sm-2306-omp/','https://asabella.ru/wa-data/public/shop/products/00/webp/86/16/151686/images/1358333/1358333.700.webp'),
 ('2215-OMP','Фланель · орнамент',['Коричневый','Серый'],'Геометрия, орнамент',14382,'https://asabella.ru/komplekt-evro-s-letnim-odeyalom-iz-flaneli-200kh220-sm-2215-omp/','https://asabella.ru/wa-data/public/shop/products/00/webp/43/92/149243/images/1349778/1349778.700.webp'),
 ('2141-OMP','Печатный сатин · цветы',['Голубой','Розовый'],'Цветы',13470,'https://asabella.ru/komplekt-s-letnim-odeyalom-evro-iz-pechatnogo-satina-200kh220-sm-2141-omp/','https://asabella.ru/wa-data/public/shop/products/00/webp/05/54/145405/images/1313377/1313377.700.webp')
])

for sku,title,colors,pattern,price,url,image in asabella:
 products.append({'id':'asabella-'+sku,'modelId':url,'brand':'Asabella','name':'Комплект с летним одеялом '+sku,'displayName':title,'sku':sku,'size':'Евро','variantLabel':'Евро с одеялом 200 × 220','items':[{'type':'Одеяло','size':'200 × 220','count':1},{'type':'Простыня','size':'240 × 260','count':1},{'type':'Наволочка','size':'50 × 70','count':2}],'weave':{'2400-OMP':'Твил','2306-OMP':'Фланель','2215-OMP':'Фланель'}.get(sku,'Сатин'),'composition':'100% хлопок','colors':colors,'colorOriginal':', '.join(colors),'bundle':'С одеялом без пододеяльника','noDuvetCover':True,'season':'Летнее','sheetType':'Прямая','pattern':pattern,'filling':'50% тенсел, 50% искусственный шёлк','price':price,'availability':'unknown','url':url,'imageRemote':image,'checkedAt':'2026-10-05','priceSource':'Публичная карточка поставщика через веб-источник; требуется подтверждение','descriptionFacts':[],'warnings':['В публичной странице есть противоречивые сведения о наличии. Уточните у поставщика.','Комплект с летним одеялом. Для холодного сезона нужно уточнить пожелания клиента.']})

# Keep the supplier's original colour, add consistent tags for filter choices.
def colour_tags(value):
 parts=re.split(r'[,;/]',value or '')
 aliases={'шоколад':'Коричневый','молочный шоколад':'Коричневый','графит':'Серый','серебристый':'Серый','пурпурный':'Фиолетовый','терракотовый':'Терракотовый'}
 tags=[]
 for part in parts:
  v=part.lower().replace('ё','е').strip()
  tag=aliases.get(v)
  if not tag:
   for stem,base in [('бел','Белый'),('сер','Серый'),('беж','Бежевый'),('коричнев','Коричневый'),('розов','Розовый'),('лилов','Лиловый'),('голуб','Голубой'),('зелен','Зеленый'),('син','Синий'),('черн','Черный'),('бирюз','Бирюзовый'),('оливков','Оливковый'),('фиолет','Фиолетовый')]:
    if re.search(r'(?<![а-я])'+stem,v):tag=base;break
  if tag is None:tag=part.strip().capitalize()
  if tag and tag not in tags:tags.append(tag)
 return tags

for p in products:
 p['colors']=colour_tags(p.get('colorOriginal'))
 if not p.get('displayName'):
  if p['brand']=='Luxberry':
   m=re.search(r'"([^"]+)"',p['name']);p['displayName']=m.group(1).title() if m else p['name']
  else:p['displayName']=p['name']
 p['compositionOriginal']=p['composition']
 p['composition']=p['composition'].replace('Хлопок 100%, сатин 300 ТС','100% хлопок').replace('Хлопок 100%, перкаль 210ТС','100% хлопок').replace('Хлопок 100%, stone washed','100% хлопок').replace('Хлопок 70%, лён 30%','70% хлопок, 30% лён').replace('100% Tencel® (тенсель)','100% тенсел')
 if p['weave']=='Не указано':p['weave']='Не указано'
 p['image']='assets/'+hashlib.sha256(p['imageRemote'].encode()).hexdigest()[:16]+'.'+('webp' if '.webp' in p['imageRemote'] else 'jpg')

def download(pair):
 image,url=pair;f=ROOT/'docs'/image
 if f.exists():return image,'cached'
 try:
  with urllib.request.urlopen(url,timeout=20) as r:
   if not r.headers.get('content-type','').startswith('image/'):raise ValueError('Not an image')
   f.write_bytes(r.read())
  return image,'ok'
 except Exception as e:return image,str(e)

images=list(dict.fromkeys((p['image'],p['imageRemote']) for p in products))
for result in concurrent.futures.ThreadPoolExecutor(max_workers=4).map(download,images):print(result,flush=True)
missing=[p for p in products if not (ROOT/'docs'/p['image']).exists()]
if missing:raise RuntimeError('Missing real product photos: '+', '.join(p['id'] for p in missing))
sources=[{'name':'Luxberry','note':'Размеры и цены получены из вариантов публичных карточек. Наличие — снимок данных сайта, перед отправкой проверьте.'},{'name':'German Grass','note':'Размеры, состав и цены получены из публичных данных карточек. Остатки не подтверждены. Часть ассортимента пока не загружена.'},{'name':'Asabella','note':'Комплекты с готовым летним одеялом из сатина, твила и фланели. Данные проверены по публичным карточкам через веб-источник. Автоматическое обновление не подключено; наличие требует уточнения.'}]
catalog={'schemaVersion':1,'generatedAt':'2026-10-05','catalogVersion':'2026-10-05.2','sources':sources,'products':products}
(ROOT/'docs/catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2))
print('CATALOG',len(products),'variants',len(set(p['modelId'] for p in products)),'models',flush=True)
