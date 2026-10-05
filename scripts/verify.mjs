import assert from 'node:assert/strict';
import fs from 'node:fs';
import {initialFilters,matches,parseRequest,validateCatalog,proposal} from '../docs/logic.js';
const data=validateCatalog(JSON.parse(fs.readFileSync(new URL('../docs/catalog.json',import.meta.url),'utf8')));
assert.ok(data.products.length>=160);
const filters={...initialFilters(),size:'Евро',weave:'Сатин',bundle:'С одеялом без пододеяльника'};
const matching=data.products.filter(p=>matches(p,filters));
assert.ok(matching.length>=8);
assert.ok(matching.every(p=>p.brand==='Asabella'&&p.items.some(i=>i.type==='Одеяло')&&!p.items.some(i=>i.type==='Пододеяльник')));
assert.equal(data.products.filter(p=>matches(p,{...filters,maxPrice:'10000'})).length,0);
assert.ok(data.products.filter(p=>matches(p,{...initialFilters(),size:'Семейный'})).every(p=>p.items.find(i=>i.type==='Пододеяльник').count===2));
const parsed=parseRequest('Нужно постельное бельё евро-двушка из сатина с одеялом, которое не нужно заправлять, до 30 тысяч рублей');
assert.deepEqual(parsed,{size:'Евро',weave:'Сатин',bundle:'С одеялом без пододеяльника',maxPrice:'30000'});
assert.deepEqual(parseRequest('Постельное бельё'),{});
const p=matching[0];
assert.ok(proposal(p).includes('Стоимость уточняем.'));
assert.ok(!proposal(p).includes('13 470'));
assert.ok(proposal(p,{priceConfirmed:true,price:13470,stockConfirmed:true}).includes('Наличие подтверждено.'));
assert.throws(()=>validateCatalog({...data,products:[{...p,url:'javascript:alert(1)'}]}));
assert.throws(()=>validateCatalog({...data,products:[{...p,price:-1}]}));
assert.throws(()=>validateCatalog({...data,products:[{...p,items:[...p.items,{type:'Пододеяльник',size:'200 × 220',count:1}]}]}));
for(const p of data.products){assert.ok(fs.existsSync(new URL('../docs/'+p.image,import.meta.url)),p.image);assert.ok(p.price===null||p.price>0)}
const lux=data.products.filter(p=>p.brand==='Luxberry'&&p.sku==='L001265');
assert.equal(lux.find(p=>p.size==='Полуторный').price,14880);
assert.equal(lux.find(p=>p.size==='Семейный').price,15720);
assert.notEqual(lux.find(p=>p.size==='Евро').price,14880);
assert.equal(new Set(data.products.map(p=>p.id)).size,data.products.length);

assert.ok(data.products.some(p=>p.brand==='German Grass'&&p.sheetType==='На резинке'));
assert.ok(data.products.some(p=>p.weave==='Фланель'&&p.noDuvetCover));
assert.ok(data.products.some(p=>p.brand==='German Grass'&&!p.items.some(i=>i.type==='Простыня')));

const quadro=data.products.find(p=>p.id==='grass-GR200');
assert.ok(quadro,'Pallada Quadro should load from a model page');
assert.deepEqual(quadro.items.filter(i=>i.type==='Наволочка').map(i=>[i.size,i.count]),[['50 × 70',2],['70 × 70',2]]);
console.log(`Verified ${data.products.length} real variants, strict bundle/size/budget matching, request rules, price checks, import rejection, local photos.`);
