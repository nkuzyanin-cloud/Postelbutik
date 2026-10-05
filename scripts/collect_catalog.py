"""Build a catalogue from public supplier pages, without login or bypasses.
Run locally; browser search uses the saved catalogue, not live cross-origin fetch.
"""
import concurrent.futures, hashlib, html, json, re, urllib.request, urllib.parse, urllib.error, threading
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / '.supplier-cache'
CACHE.mkdir(exist_ok=True)
STOPPED_HOSTS=set()
HOST_LOCK=threading.Lock()

class Text(HTMLParser):
    def __init__(self): super().__init__(); self.parts=[]; self.skip=0
    def handle_starttag(self,t,a):
        if t in ('script','style'): self.skip+=1
    def handle_endtag(self,t):
        if t in ('script','style'): self.skip=max(0,self.skip-1)
    def handle_data(self,d):
        if not self.skip and d.strip(): self.parts.append(d.strip())

def plain(s):
    p=Text();p.feed(s);return '\n'.join(p.parts)

def fetch(url):
    key=hashlib.sha256(url.encode()).hexdigest()[:16]
    f=CACHE/(key+'.html')
    if f.exists():return f.read_text()
    host=urllib.parse.urlparse(url).hostname
    with HOST_LOCK:
        if host in STOPPED_HOSTS:raise RuntimeError('Supplier rate limit reached; further requests stopped')
    try:
        with urllib.request.urlopen(url,timeout=20) as r:
            s=r.read().decode('utf-8');f.write_text(s);return s
    except urllib.error.HTTPError as e:
        if e.code==429:
            with HOST_LOCK:STOPPED_HOSTS.add(host)
        raise

def attrs(tag):return dict(re.findall(r'([\w-]+)="([^"]*)"',tag))
def value(text,key):
    m=re.search(r'(?:^|\n)'+re.escape(key)+r':?\s*\n([^\n]+)',text)
    return m.group(1).strip() if m else None

def lux(url):
    s=fetch(url);t=plain(s)
    ld=[]
    for v in re.findall(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',s,re.S):
        try: ld.append(json.loads(v))
        except ValueError: pass
    d=next(x for x in ld if x.get('@type')=='Product')
    name=html.unescape(d['name']);color=value(t,'Цвет');fabric=value(t,'Состав') or 'Не указан'
    if 'хлопок' in name.lower() and '100%' in name and 'хлопок' not in fabric.lower():fabric='100% хлопок'
    # Read exactly the size radio's price; JSON-LD prices differ from visible prices.
    records=[]
    for tag in re.findall(r'<input\b[^>]*name="select_size"[^>]*>',s):
        a=attrs(tag);label=re.search(r'<label[^>]*for="'+re.escape(a['id'])+r'"[^>]*>(.*?)</label>',s,re.S)
        if not label:continue
        label=plain(label.group(1));dims=re.findall(r'(\d+)\s*[xх×]\s*(\d+)',label)
        if len(dims)!=3 or not any(k in label for k in ['Семей','Полутор','Двуспаль','Евро']):continue
        group='Семейный' if 'Семей' in label else ('Полуторный' if 'Полутор' in label else 'Евро')
        duvet_count=2 if group=='Семейный' else 1
        cases_count=2 if re.search(r'2\s*\(',label.split('+')[-1]) else 1
        items=[{'type':'Пододеяльник','size':' × '.join(dims[0]),'count':duvet_count},{'type':'Простыня','size':' × '.join(dims[1]),'count':1},{'type':'Наволочка','size':' × '.join(dims[2]),'count':cases_count}]
        weave='Сатин' if 'сатин' in (name+' '+fabric).lower() else ('Перкаль' if 'перкаль' in (name+' '+fabric).lower() else 'Не указано')
        desc=[]
        for line in t.split('\n'):
            if any(line.startswith(k) for k in ['Тип рисунка','Тип ткани','Тип застежки','Упаковка']):desc.append(line)
        records.append({'id':'lux-'+a['value'],'modelId':url,'brand':'Luxberry','name':name,'sku':value(t,'Артикул'),'size':group,'variantLabel':label,'items':items,'weave':weave,'composition':fabric,'colors':[color] if color else [],'colorOriginal':color,'bundle':'С пододеяльником','noDuvetCover':False,'season':None,'sheetType':'Прямая' if 'простыня прямая' in t.lower() else 'Не указано','pattern':'Однотонный' if 'Тип рисунка - однотонный' in t else ('Рисунок' if 'Тип рисунка' in t else 'Не указано'),'price':float(a['price']) if a.get('price') else None,'availability':'in_stock' if a.get('available')=='Y' else 'out_of_stock','url':url,'imageRemote':urllib.parse.urljoin(url,d['image']),'checkedAt':'2026-10-05','priceSource':'Размерный вариант в карточке поставщика','descriptionFacts':desc,'warnings':[]})
    return records

def collect_lux():
    urls=json.loads((ROOT/'sources.json').read_text())['luxberry']
    urls=['https://luxberry.ru'+u if u.startswith('/') else u for u in urls]
    urls=list(dict.fromkeys(urls+['https://luxberry.ru/catalog/komplekty_postelnogo_belya/komplekt_postelnogo_belya_daily_bedding_satin_telesnyy/']))
    results=[];errors=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures={pool.submit(lux,u):u for u in urls}
        for f in concurrent.futures.as_completed(futures):
            try:r=f.result();results.extend(r);print('OK',len(r),futures[f],flush=True)
            except Exception as e:errors.append({'url':futures[f],'error':str(e)});print('ERROR',str(e),flush=True)
    (ROOT/'docs/lux-data.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
    (ROOT/'source-errors.json').write_text(json.dumps(errors,ensure_ascii=False,indent=2))

def grass(url):
    s=fetch(url)
    raw=json.loads(re.search(r'<script[^>]*id="__NUXT_DATA__"[^>]*>(.*?)</script>',s,re.S).group(1))
    def resolve(i,depth=0):
        if i<0 or depth>25:return None
        v=raw[i]
        if isinstance(v,dict):return {k:resolve(n,depth+1) for k,n in v.items()}
        if isinstance(v,list):
            if v and isinstance(v[0],str):return resolve(v[1],depth+1) if len(v)==2 and isinstance(v[1],int) else v
            return [resolve(n,depth+1) for n in v]
        return v
    index=next(i for i,v in enumerate(raw) if isinstance(v,dict) and all(k in v for k in ['name','attributes','variants','sku','price']))
    d=resolve(index);a={v['name']:v['value'] for v in d['attributes']}
    result=[]
    for v in d.get('variants') or [d]:
        va={x['name']:x['value'] for x in v['attributes']}; merged={**a,**va};original_size=va.get('Размер','');size=next((x for x in ['Евро','Полуторный','Семейный'] if original_size.startswith(x)),original_size)
        if size not in ['Евро','Полуторный','Семейный']:continue
        comp=merged.get('Состав комплекта','');m=re.search(re.escape(size)+r':\s*(.*?)(?=\.\s|$)',comp)
        part=m.group(1) if m else comp
        # Do not assign a different size's dimensions to a variant.
        if not m and any(k+':' in comp for k in ['Евро','Полуторный','Семейный']):continue
        items=[]
        item_pattern=r'(Пододеяльники?|Простын[ья]|Наволочки?)[^\d,•]*?(\d+)\s*[xх×]\s*(\d+)(?:\s*[xх×]\s*(\d+))?\s*(?:см)?\s*(?:[-–—(]?\s*(\d+)\s*шт\.?)?'
        for match in re.finditer(item_pattern,part,re.I):
            label=match[1].lower();kind='Пододеяльник' if label.startswith('подод') else ('Простыня' if label.startswith('простын') else 'Наволочка')
            count=int(match[5]) if match[5] else 1
            if not match[5] and label in ['пододеяльники','наволочки']:continue
            dims=[match[2],match[3]]+([match[4]] if match[4] else [])
            items.append({'type':kind,'size':' × '.join(dims),'count':count})
        if len(items)<2 or not any(i['type']=='Пододеяльник' for i in items) or not any(i['type']=='Наволочка' for i in items):continue
        if 'простын' in part.lower() and not any(i['type']=='Простыня' for i in items):continue
        color=merged.get('Цвет');sheet='На резинке' if 'на резинке' in (v['name']+' '+comp).lower() else ('Прямая' if any(i['type']=='Простыня' for i in items) else 'Без простыни')
        collection=merged.get('Коллекция') or merged.get('Коллекция РУ') or d['name']
        design=re.sub(r'\([^)]*\)|\b(?:Евро|Семейный|Полуторный)\b|,?\s*GERMAN GRASS', '', d['name'],flags=re.I)
        design=re.sub(r'\b\d+\s*[xх×]\s*\d+\b','',design)
        design=re.sub(r'\s+', ' ',design).strip(' ,').replace(chr(34),'').lower()
        trim=re.search(r'\bс (.+?)(?:\bЕвро\b|,\s*GERMAN|$)',d['name'],re.I)
        display=(merged.get('Коллекция РУ') or collection).title()+' · '+(color or 'цвет не указан').lower()+((' · '+trim[1].strip(' ,')) if trim else '')
        pattern=merged.get('Рисунок','Не указано')
        sheet_item=next((i for i in items if i['type']=='Простыня'),None)
        main_size=('простыня '+sheet_item['size']) if sheet=='На резинке' else ('подод. '+items[0]['size'])
        variant_label=original_size+' · '+main_size+' · нав. '+' + '.join(i['size']+' ('+str(i['count'])+')' for i in items if i['type']=='Наволочка')
        result.append({'id':'grass-'+v['sku'],'modelId':'grass:'+collection+':'+str(color)+':'+sheet+':'+design,'brand':'German Grass','name':v['name'],'displayName':display,'sku':v['sku'],'size':size,'variantLabel':variant_label,'items':items,'weave':merged.get('Тип ткани','Не указано'),'composition':merged.get('Состав ткани','Не указан'),'colors':[color] if color else [],'colorOriginal':color,'bundle':'С пододеяльником','noDuvetCover':False,'season':None,'sheetType':sheet,'pattern':pattern,'price':v['price'] if v['price']>0 else None,'availability':'unknown','url':url,'imageRemote':(v.get('images') or d['images'])[0]['url'],'checkedAt':'2026-10-05','priceSource':'Вариант в публичных данных карточки поставщика','descriptionFacts':[],'warnings':['Наличие поставщик не подтвердил']})

    return result

def collect_grass():
    urls=json.loads((ROOT/'sources.json').read_text())['germanGrass']
    results=[];errors=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures={pool.submit(grass,u):u for u in urls}
        for f in concurrent.futures.as_completed(futures):
            try:r=f.result();results.extend(r);print('GRASS',len(r),futures[f],flush=True)
            except Exception as e:errors.append({'url':futures[f],'error':str(e)});print('ERROR',str(e),flush=True)
    (ROOT/'docs/grass-data.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
    (ROOT/'grass-errors.json').write_text(json.dumps(errors,ensure_ascii=False,indent=2))

if __name__=='__main__':
    import sys
    if '--grass' in sys.argv:collect_grass()
    else:collect_lux()
