export const initialFilters=()=>({query:'',brands:[],size:'',weave:'',bundle:'',color:'',composition:'',sheetType:'',minPrice:'',maxPrice:'',availableOnly:false});
export function norm(s){return String(s??'').toLowerCase().replaceAll('ё','е').trim()}
export function matches(p,f){
 const q=norm(f.query);if(q&&!q.split(/\s+/).every(w=>norm([p.name,p.sku,p.brand,p.colorOriginal,p.composition,p.variantLabel].join(' ')).includes(w)))return false;
 if(f.brands.length&&!f.brands.includes(p.brand))return false;
 for(const key of ['size','weave','bundle','sheetType'])if(f[key]&&p[key]!==f[key])return false;
 if(f.color&&!p.colors.includes(f.color))return false;
 if(f.composition&&!norm(p.composition).includes(norm(f.composition)))return false;
 if(f.minPrice!==''&&(p.price===null||p.price<Number(f.minPrice)))return false;
 if(f.maxPrice!==''&&(p.price===null||p.price>Number(f.maxPrice)))return false;
 if(f.availableOnly&&p.availability!=='in_stock')return false;
 return true;
}
export function parseRequest(text){
 const s=norm(text),f={};
 if(/семейн/.test(s))f.size='Семейный';else if(/евро|евродвуш|евро-двуш/.test(s))f.size='Евро';else if(/полутор|1[,.]5/.test(s))f.size='Полуторный';
 if(/сатин/.test(s))f.weave='Сатин';else if(/перкал/.test(s))f.weave='Перкаль';
 if(/с одеял|не нужно заправ|без пододеяль|комфортер/.test(s))f.bundle='С одеялом без пододеяльника';else if(/с пододеяль/.test(s))f.bundle='С пододеяльником';
 const tokens=s.match(/[\p{L}]+/gu)||[];
 if(tokens.some(w=>w.startsWith('шелк')))f.composition='Шёлк';else if(tokens.some(w=>w.startsWith('хлоп')))f.composition='Хлопок';else if(tokens.some(w=>/^тенсел|^tencel/.test(w)))f.composition='Тенсел';else if(tokens.some(w=>w==='лен'||w.startsWith('льн')))f.composition='Лён';
 const colors=[[/^бел(?:ый|ая|ое|ые|ого|ом|ую|ых|ыми)$/,'Белый'],[/^беж/,'Бежевый'],[/^сер(?:ый|ая|ое|ые|ого|ом|ую|ых|ыми)$/,'Серый'],[/^зелен/,'Зеленый'],[/^голуб/,'Голубой'],[/^бирюз/,'Бирюзовый'],[/^коричнев/,'Коричневый'],[/^розов/,'Розовый'],[/^лилов/,'Лиловый'],[/^черн/,'Черный'],[/^син(?:ий|яя|ее|ие|его|ем|юю|их|ими)$/,'Синий'],[/^фиолет/,'Фиолетовый']];
 const found=colors.filter(([pattern])=>tokens.some(w=>pattern.test(w)));
 if(found.length===1)f.color=found[0][1];
 if(/на резинке/.test(s))f.sheetType='На резинке';
 const price=s.match(/(?:до|не дороже)\s*(\d[\d\s]*(?:[,.]\d+)?)\s*(тыс|тысяч|к\b|₽|руб)?/);
 if(price){const n=Number(price[1].replaceAll(' ','').replace(',','.'))*(price[2]&&/тыс|к/.test(price[2])?1000:1);if(Number.isFinite(n)&&n>0)f.maxPrice=String(n)}
 return f;
}
export function validateCatalog(data){
 if(!data||data.schemaVersion!==1||!Array.isArray(data.products)||!data.products.length||data.products.length>5000)throw Error('Нужен каталог версии 1 с 1–5000 вариантами.');
 if(typeof data.generatedAt!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(data.generatedAt)||!Array.isArray(data.sources)||!data.sources.every(s=>s&&typeof s.name==='string'&&typeof s.note==='string'))throw Error('Не указаны дата и источники каталога.');
 const ids=new Set();
 for(const p of data.products){
  for(const k of ['id','modelId','brand','name','size','weave','composition','bundle','url','image','checkedAt'])if(typeof p[k]!=='string'||!p[k].trim()||p[k].length>2500)throw Error('Неполная карточка товара.');
  if(ids.has(p.id))throw Error('В каталоге повторяются идентификаторы.');ids.add(p.id);
  if(!['German Grass','Luxberry','Asabella'].includes(p.brand)||!Array.isArray(p.items)||!Array.isArray(p.colors)||!p.colors.every(c=>typeof c==='string'))throw Error('Неверные характеристики.');
  if(p.price!==null&&(typeof p.price!=='number'||!Number.isFinite(p.price)||p.price<=0))throw Error('Неверная цена.');
  if(!['in_stock','out_of_stock','unknown','on_request','preorder'].includes(p.availability))throw Error('Неверный статус наличия.');
  const u=new URL(p.url);if(u.protocol!=='https:'||!['germangrass.com','luxberry.ru','asabella.ru','www.germangrass.com','www.luxberry.ru','www.asabella.ru'].includes(u.hostname))throw Error('Неизвестный источник товара.');
  if(!(/^assets\/[a-zA-Z0-9._-]+$/.test(p.image)||p.image.startsWith('https://')))throw Error('Неверный адрес фотографии.');
  for(const item of p.items)if(!item||typeof item.type!=='string'||typeof item.size!=='string'||!Number.isInteger(item.count)||item.count<1||item.count>10)throw Error('Неверная комплектация.');
  if(p.noDuvetCover!==true&&p.noDuvetCover!==false)throw Error('Не подтверждена комплектация.');
  if(p.bundle==='С одеялом без пододеяльника'&&(!p.noDuvetCover||!p.items.some(i=>i.type==='Одеяло')||p.items.some(i=>i.type==='Пододеяльник')))throw Error('Противоречивая комплектация.');
 }
 return data;
}
export const money=n=>new Intl.NumberFormat('ru-RU',{style:'currency',currency:'RUB',maximumFractionDigits:2}).format(n);
export const itemsText=p=>p.items.map(i=>`${i.type} ${i.size} см${i.count>1?` — ${i.count} шт.`:''}`).join('; ');
export function proposal(p,verification={}){
 const color=p.colorOriginal?` Цвет: ${p.colorOriginal.toLowerCase()}.`:'';
 const opening=p.noDuvetCover?'Готовое летнее одеяло используется без пододеяльника — его не нужно заправлять.':p.pattern==='Однотонный'?'Однотонное оформление для спокойной и лаконичной спальни.':'Комплект для оформления спальни.';
 const extra=p.noDuvetCover&&p.filling?` Наполнитель одеяла: ${p.filling}.`:'';
 const price=verification.priceConfirmed&&Number(verification.price)>0?`Стоимость: ${money(Number(verification.price))}.`:'Стоимость уточняем.';
 return `${p.brand} · ${p.displayName||p.name}\n${opening}${color}\nТкань: ${p.composition}; ${p.weave.toLowerCase()}.${extra}\nВ комплекте: ${itemsText(p)}.\n${price}${verification.stockConfirmed?' Наличие подтверждено.':' Наличие уточняем.'}\n${p.url}`;
}
