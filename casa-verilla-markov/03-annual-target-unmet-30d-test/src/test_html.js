// Static DOM stub + real-data JS logic tests. This is NOT a browser or visual test.
const fs=require('fs'),vm=require('vm'),path=require('path'),root=path.resolve(__dirname,'..');
const html=fs.readFileSync(path.join(root,'年度训练_月度回测.html'),'utf8');
const packed=html.match(/<script id="research-data" type="application\/json">([\s\S]*?)<\/script>/)[1];
const dataText=require("zlib").gunzipSync(Buffer.from(packed.trim(),"base64")).toString("utf8");
const script=html.match(/<script id="app-code" type="text\/plain">([\s\S]*?)<\/script>/)[1];
fs.writeFileSync(path.join(root,'logs/extracted_ui.js'),script);
if(/<script[^>]+src=|<link[^>]+href=|\bfetch\(|XMLHttpRequest|new WebSocket|url\(https?:/i.test(html))throw Error('unexpected external dependency/network');
class E {constructor(id){this.id=id;this.value=({asset:'all',cost:'fees',pnlfilter:'all',pagesize:'20',search:''})[id]||'';this.checked=false;this.disabled=false;this.innerHTML='';this.textContent=id==='research-data'?dataText:'';this.handlers={}}addEventListener(t,f){this.handlers[t]=f}appendChild(){}remove(){}click(){}}
const elements={};const document={getElementById:id=>elements[id]||(elements[id]=new E(id)),querySelectorAll:()=>[],createElement:()=>new E('created'),body:new E('body')};
const ctx=vm.createContext({document,console,Intl,Date,Blob,URL,setTimeout});new vm.Script(script);vm.runInContext(script,ctx);
const data=JSON.parse(dataText);let combinations=0,zero=0;
for(const key of Object.keys(data.groups)){
 const [m,a,s,c]=key.split('|');for(const [id,v] of Object.entries({model:m,asset:a,strategy:s,cost:c}))elements[id].value=v;
 vm.runInContext('render()',ctx);const summary=data.groups[key].summary;
 if(!elements.kpis.innerHTML.includes(Number(summary.trades).toLocaleString('zh-CN')))throw Error('KPI mismatch '+key);
 for(const id of ['equitychart','ddchart','calchart'])if(/NaN|undefined|Infinity/.test(elements[id].innerHTML))throw Error('nonfinite chart '+key);
 if(!summary.trades){zero++;if(!elements.equitychart.innerHTML.includes('没有模拟交易'))throw Error('fabricated zero-trade chart')}
 if(!elements.stabilitybody.innerHTML.includes('前15日'))throw Error('half table missing');combinations++;
}
for(const [id,v] of Object.entries({model:'large',asset:'all',strategy:'edge05_no_filter',cost:'fees',search:'',pnlfilter:'all',pagesize:'20'}))elements[id].value=v;
vm.runInContext('render()',ctx);const before=vm.runInContext('filtered().length',ctx);if(before!==data.groups['large|all|edge05_no_filter|fees'].summary.trades)throw Error('filter count');
vm.runInContext('page=2;renderTrades()',ctx);if(!elements.paginationinfo.textContent.includes('第 2 页'))throw Error('pagination');
vm.runInContext('sortKey="net_pnl";sortDir=1;renderTrades()',ctx);if(!vm.runInContext('filtered().every((r,i,a)=>!i||a[i-1].net_pnl<=r.net_pnl)',ctx))throw Error('sort');
elements.pnlfilter.value='win';if(!vm.runInContext('filtered().every(r=>r.net_pnl>0)',ctx))throw Error('profit filter');elements.pnlfilter.value='all';
const firstId=vm.runInContext('current.trades[0].market_id',ctx);elements.search.value=firstId;if(vm.runInContext('filtered().length',ctx)!==1)throw Error('search id');elements.search.value='';
const csv=vm.runInContext('toCSV(filtered())',ctx);fs.writeFileSync(path.join(root,'logs/html_export_test.csv'),csv);
if(!vm.runInContext('toCSV([])===""',ctx))throw Error('empty CSV');
const result={mode:'static_DOM_stub_not_browser',combinations,zero_trade_combinations:zero,checks:['syntax','no_external_assets','all_filter_combinations','finite_SVG_coordinates','no_fake_empty_curves','pagination','sorting','profit_filter','search','CSV_export_real_rows'],export_records:before};fs.writeFileSync(path.join(root,'logs/html_test.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result));
