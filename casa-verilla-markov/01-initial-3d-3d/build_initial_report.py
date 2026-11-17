"""Build the first-version REPORT.html from the delivered result CSVs.

Reads data/results only. Does not refit, download, or invent trades.
The equity polyline is a reconstruction: settlement-time net_pnl summed
from 10000, with same-second settlements batched. It does not replace
max_realized_drawdown in variant_results.csv.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))
from ticket_section import ticket_html  # noqa: E402

RESULTS = ROOT / "data" / "results"
OUT = ROOT / "REPORT.html"

VARIANTS = [
    ("terminal_e05_p87", "终局模型，5%差值+87%持续率"),
    ("terminal_e05_nofilter", "终局模型，5%差值，不加持续率"),
    ("terminal_e03_p87", "终局模型，3%差值+87%持续率"),
    ("terminal_e03_band", "终局模型，3%+87%+价格带"),
    ("terminal_e05_band", "终局模型，5%+87%+价格带"),
    ("literal_e05_p87", "一步概率字面版，5%+87%"),
    ("literal_e03_band", "一步概率字面版，3%+87%+价格带"),
    ("calibrated_e05", "经验终局校准基线，5%差值"),
    ("favorite_fixed", "固定第2分钟买热门边"),
    ("market_edge", "市场价作同边概率，无额外优势"),
]
SCENARIOS = [
    ("quote0", "原价、不扣费"),
    ("fee_only", "原价 + 元数据手续费"),
    ("stress1", "再加1分/份 + 手续费"),
    ("stress2_delay", "延迟1分钟、较差价+2分、手续费"),
    ("fee_double", "元数据费率翻倍"),
]
PRODUCTS = [
    ("15", "15分钟 · Chainlink规则"),
    ("60", "60分钟 · Binance规则"),
]
TRADE_FIELDS = [
    "market_id",
    "asset",
    "duration_min",
    "variant",
    "scenario",
    "side",
    "time_utc",
    "execution_utc",
    "settle_ts",
    "p_model",
    "persistent",
    "q_observed",
    "q_scenario",
    "shares",
    "fee",
    "gross_pnl",
    "net_pnl",
    "won",
    "y_up",
    "execution_limitation",
]
NUM_FIELDS = {
    "settle_ts",
    "p_model",
    "persistent",
    "q_observed",
    "q_scenario",
    "shares",
    "fee",
    "gross_pnl",
    "net_pnl",
}


def read_csv(name: str) -> list[dict]:
    with (RESULTS / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def num(value: str):
    if value is None or value == "":
        return None
    return float(value)


def build_payload() -> dict:
    variants = read_csv("variant_results.csv")
    trades = read_csv("trades.csv")
    folds = read_csv("folds.csv")
    if len(variants) != 100:
        raise SystemExit(f"expected 100 variant rows, got {len(variants)}")
    grouped: dict[tuple, list] = {}
    for row in trades:
        if not row["settle_ts"]:
            raise SystemExit(f"trade missing settle_ts: {row['market_id']}")
        key = (row["duration_min"], row["variant"], row["scenario"])
        item = {}
        for field in TRADE_FIELDS:
            raw = row[field]
            item[field] = num(raw) if field in NUM_FIELDS and raw != "" else raw
        grouped.setdefault(key, []).append(item)
    summaries = []
    for row in variants:
        key = (row["duration_min"], row["variant"], row["scenario"])
        book = grouped.get(key, [])
        pnl = sum(item["net_pnl"] for item in book)
        official = float(row["net_pnl"])
        if abs(pnl - official) > 1e-6:
            raise SystemExit(f"net_pnl mismatch {key}: csv {official} sum {pnl}")
        if int(row["trades"]) != len(book):
            raise SystemExit(f"trade count mismatch {key}")
        summaries.append(
            {
                "duration_min": row["duration_min"],
                "variant": row["variant"],
                "scenario": row["scenario"],
                "trades": int(row["trades"]),
                "wins": int(row["wins"]) if row["wins"] else 0,
                "win_rate": num(row["win_rate"]),
                "brier_on_trades": num(row["brier_on_trades"]),
                "gross_pnl": float(row["gross_pnl"]),
                "fees": float(row["fees"]),
                "net_pnl": official,
                "return_on_initial_pct": float(row["return_on_initial_pct"]),
                "max_realized_drawdown": float(row["max_realized_drawdown"]),
                "max_concurrent_capital": float(row["max_concurrent_capital"]),
                "initial_capital": float(row["initial_capital"]),
                "final_cash": float(row["final_cash"]),
                "executable_net_pnl": row["executable_net_pnl"],
                "missing_reason": row["missing_reason"],
            }
        )
    known = {(row["duration_min"], row["variant"], row["scenario"]): row for row in summaries}
    fee_15 = known[("15", "terminal_e05_p87", "fee_only")]
    fee_60 = known[("60", "terminal_e05_p87", "fee_only")]
    literal = known[("15", "literal_e05_p87", "fee_only")]
    if fee_15["trades"] != 35 or abs(fee_15["net_pnl"] + 60.73241) > 1e-6:
        raise SystemExit("15-minute headline figure drifted from variant_results.csv")
    if fee_60["trades"] != 15 or abs(fee_60["net_pnl"] + 27.1896) > 1e-6:
        raise SystemExit("60-minute headline figure drifted from variant_results.csv")
    if literal["trades"] != 0:
        raise SystemExit("literal diagnostic unexpectedly has trades")
    return {
        "products": PRODUCTS,
        "variants": VARIANTS,
        "scenarios": SCENARIOS,
        "summaries": summaries,
        "trades": [item for rows in grouped.values() for item in rows],
        "folds": folds,
        "notes": {
            "equity": "根据旧交易CSV重建的已实现权益",
            "equity_detail": "按原始逐笔 settle_ts 与 net_pnl，从10000美元累加；同一结算秒的净盈亏先加总再走一步。这不是旧程序按入场占款和结算释放逐事件更新的原曲线。最大回撤以 variant_results.csv 的 max_realized_drawdown 为准，图上的重建回撤不覆盖该值。",
        },
    }


PAGE = r"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>首次研究：初始3日训练、3日滚动测试</title><style>
:root{--bg:#f4f6f8;--paper:#fff;--ink:#162336;--muted:#69788a;--line:#e1e7ee;--teal:#087f83;--blue:#527ee0;--red:#ce5260;--nav:#142235}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.6 system-ui,-apple-system,'Noto Sans SC',sans-serif}button,select,input{font:inherit}header{background:var(--nav);color:white;padding:27px max(24px,calc((100vw - 1440px)/2));border-bottom:3px solid var(--teal)}.top{display:flex;justify-content:space-between;gap:20px;align-items:center}.brand{font-size:12px;letter-spacing:2px;color:#94abbf}.title{font-size:29px;font-weight:700;letter-spacing:1px;margin:4px 0}.subtitle{color:#b2c2d4;font-size:13px}.status{padding:8px 13px;border:1px solid #9c743e;border-radius:22px;color:#f2d6a6;background:#9c743e16;white-space:nowrap}.nav{margin-top:20px;display:flex;gap:22px;flex-wrap:wrap}.nav a{color:#c3d1df;text-decoration:none;font-size:13px}main{max-width:1488px;margin:auto;padding:24px}.warning{border:1px solid #edd8b8;background:#fff8ed;color:#805c29;padding:13px 17px;border-radius:10px;font-size:13px}.filters{position:sticky;top:0;z-index:3;display:grid;grid-template-columns:repeat(3,1fr);gap:14px;background:#f4f6f8f2;backdrop-filter:blur(8px);padding:17px 0}.field label{display:block;font-size:11px;color:var(--muted);margin-bottom:5px;font-weight:650;letter-spacing:.5px}select,input{border:1px solid #d7dfe8;border-radius:7px;padding:9px 11px;background:white;color:var(--ink);width:100%;min-width:0}select:focus,input:focus{outline:2px solid #087f8340;border-color:var(--teal)}.kpis{display:grid;grid-template-columns:repeat(6,1fr);gap:13px}.card{border:1px solid var(--line);background:var(--paper);border-radius:11px;padding:18px;box-shadow:0 2px 4px #17304903}.label{font-size:12px;color:var(--muted)}.metric{font-size:26px;font-weight:720;line-height:1.5;font-variant-numeric:tabular-nums;letter-spacing:-.6px}.tiny{font-size:11px;color:var(--muted)}.green{color:var(--teal)}.red{color:var(--red)}.section{margin-top:20px;scroll-margin-top:120px}.sectionhead{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-bottom:15px}.section h2{font-size:16px;margin:0}.badge{font-size:11px;background:#eaf2f2;color:var(--teal);padding:3px 8px;border-radius:5px}.chartwrap{width:100%;overflow:hidden}.chartwrap svg{width:100%;height:auto;display:block}.subnote{font-size:12px;color:var(--muted);margin:8px 0}.tablewrap{overflow:auto;border:1px solid var(--line);border-radius:8px}table{border-collapse:collapse;width:100%;font-size:12px;white-space:nowrap}th{background:#f6f8fa;color:#617084;font-size:11px;font-weight:650;text-align:left;position:sticky;top:0}th,td{padding:11px 13px;border-bottom:1px solid #eaf0f4}tr:last-child td{border:0}tbody tr:hover{background:#f7fafb}.num{text-align:right;font-variant-numeric:tabular-nums}.toolbar{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:13px}.toolbar input{max-width:330px}.toolbar select{max-width:150px}button{border:1px solid #cfd9e3;background:white;border-radius:6px;padding:8px 13px;cursor:pointer;color:#33465d}button.primary{background:var(--teal);border-color:var(--teal);color:#fff}button:disabled{opacity:.4;cursor:default}.pager{display:flex;justify-content:space-between;align-items:center;margin-top:13px;font-size:12px;color:var(--muted)}.empty{padding:65px 20px;text-align:center;color:var(--muted);border-radius:8px;background:#f8fafb}.method p,.method li{font-size:13px;color:#516277}.method h3{font-size:13px;margin:16px 0 7px}a{color:var(--teal)}.footer{margin-top:28px;text-align:center;color:#8795a5;font-size:11px;padding:20px}.mono{font-family:ui-monospace,monospace}tr.active{background:#e7f4f4}@media(max-width:1100px){.kpis{grid-template-columns:repeat(3,1fr)}.metric{font-size:24px}}@media(max-width:650px){main{padding:14px}header{padding:20px}.title{font-size:22px}.filters,.kpis{grid-template-columns:1fr 1fr}.status{display:none}}
</style></head><body>
<header><div class="top"><div><div class="brand">CASAVERILLA / MARKOV LAB</div><div class="title">首次研究：初始3日训练、3日滚动测试</div><div class="subtitle">真实合约历史报价 · 预先固定变体 · 不是可执行成交</div></div><div><div class="status">研究用价格代理模拟，非可执行收益</div></div></div>
<div class="nav"><a href="#ticket">用买票理解</a><a href="#overview">研究概览</a><a href="#capital">资金与回撤</a><a href="#ledger">逐笔记录</a><a href="#variants">全部变体</a></div></header>
<main>
<div class="warning"><b>先看边界：</b>只有真实历史显示价格，没有历史买卖盘或深度，不能保证100份能按该价格成交。金额来自已交付的 variant_results.csv 与 trades.csv，不是重新训练，也不是Bonereaper源码复刻。字面一步概率变体有意暴露概率语义问题，不是正确的到期概率模型。15分钟与1小时不是同一产品。</div>
__TICKET__
<div class="filters"><div class="field"><label>01 / 产品</label><select id="product"></select></div><div class="field"><label>02 / 预先固定变体</label><select id="variant"></select></div><div class="field"><label>03 / 成本情景</label><select id="scenario"></select></div></div>
<div id="literalnote" class="warning" style="display:none;margin-bottom:12px"></div>
<div class="kpis" id="kpis"></div>
<section id="overview" class="section card"><div class="sectionhead"><h2>研究概览</h2><span class="badge">权威数字来自原始CSV</span></div>
<p>窗口是2026-11-11 08:00至11-17 08:00台北。前3日初始训练，后3日每日扩展训练并测试当天。BTC与ETH在同一产品内共享模拟现金。1小时按实际Binance规则，15分钟按实际Chainlink规则。初始模拟现金10000美元，每市场100份、最多一笔、不杠杆。</p>
<div class="tablewrap"><table><thead><tr><th>产品</th><th>折</th><th>训练市场数</th><th>测试开始（台北）</th><th>测试结束（台北）</th><th class="num">测试市场</th></tr></thead><tbody id="folds"></tbody></table></div>
<p class="subnote">完整叙述、Brier全样本比较和审计以同目录 <a href="回测结果.md">回测结果.md</a> 为准。本页不改写那些结论。成交样本Brier只来自 variant_results.csv 的 brier_on_trades，不是全样本Brier。</p></section>
<section id="capital" class="section card"><div class="sectionhead"><h2>资金曲线</h2><span class="badge" id="equitybadge">根据旧交易CSV重建的已实现权益</span></div>
<div id="equitychart" class="chartwrap"></div>
<p class="subnote" id="equitynote"></p>
<div class="kpis" id="ddcards"></div></section>
<section id="ledger" class="section card"><div class="sectionhead"><h2>逐笔模拟交易记录 <span id="tradecount" class="badge"></span></h2><button id="export" class="primary">导出筛选后 CSV</button></div>
<div class="toolbar"><input id="search" placeholder="搜索市场ID、资产、方向或时间"><select id="pnlfilter"><option value="all">全部盈亏</option><option value="win">净盈利</option><option value="loss">净亏损</option><option value="flat">净盈亏为0</option></select><select id="pagesize"><option value="20">每页20笔</option><option value="50">每页50笔</option><option value="100">每页100笔</option></select></div>
<div class="tablewrap"><table><thead><tr><th>信号时间（台北）</th><th>市场</th><th>方向 / 赢家</th><th class="num">模型概率</th><th class="num">持续率</th><th class="num">假设入价</th><th class="num">费用</th><th class="num">净盈亏</th><th>结算时间（台北）</th></tr></thead><tbody id="tradebody"></tbody></table></div>
<div class="pager"><div id="paginationinfo"></div><div><button id="prev">上一页</button> <button id="next">下一页</button></div></div>
<p class="subnote">搜索和盈亏筛选只改明细，不改上方权威汇总。导出的是当前筛选后的原始逐笔字段，不是示例行。</p></section>
<section id="variants" class="section card"><div class="sectionhead"><h2>当前产品与成本下的全部变体</h2><span class="badge">variant_results.csv</span></div>
<div class="tablewrap"><table><thead><tr><th>变体</th><th class="num">笔数</th><th class="num">胜率</th><th class="num">净盈亏</th><th class="num">权威最大已实现回撤</th><th class="num">期末现金</th></tr></thead><tbody id="variantbody"></tbody></table></div>
<p class="subnote">对照文件：<a href="data/results/variant_results.csv">data/results/variant_results.csv</a> · <a href="data/results/trades.csv">data/results/trades.csv</a> · <a href="data/results/calibration.csv">data/results/calibration.csv</a> · <a href="src/">src/</a></p></section>
<div class="footer">单文件内嵌真实汇总与逐笔，无CDN、无自动联网、无密钥。GitHub不会把这个HTML渲染成网页；请下载后离线打开。本仓库未部署GitHub Pages。</div>
</main>
<script id="research-data" type="application/json">__DATA__</script>
<script>
'use strict';
const DATA=JSON.parse(document.getElementById('research-data').textContent);
const $=id=>document.getElementById(id);
let page=1;
const fmt=(n,d=2)=>n==null?'不适用':Number(n).toLocaleString('zh-CN',{minimumFractionDigits:d,maximumFractionDigits:d});
const money=n=>n==null?'不适用':(n<0?'-$':'$')+fmt(Math.abs(n));
const pct=n=>n==null?'不适用':fmt(n*100,2)+'%';
const escapeHtml=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const labelOf=(list,id)=>list.find(x=>x[0]===id)[1];
const date=t=>new Intl.DateTimeFormat('zh-CN',{timeZone:'Asia/Taipei',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hour12:false}).format(new Date(t*1000));
const cls=n=>n<0?'red':n>0?'green':'';
function selected(){return {d:$('product').value,v:$('variant').value,s:$('scenario').value}}
function summary(){const x=selected();return DATA.summaries.find(r=>r.duration_min===x.d&&r.variant===x.v&&r.scenario===x.s)}
function book(){const x=selected();return DATA.trades.filter(r=>r.duration_min===x.d&&r.variant===x.v&&r.scenario===x.s)}
function reconstruct(rows){
 const batches=new Map();
 rows.forEach(r=>{const k=r.settle_ts;batches.set(k,(batches.get(k)||0)+r.net_pnl)});
 const times=[...batches.keys()].sort((a,b)=>a-b);
 let equity=10000,peak=10000,dd=0;const curve=[{t:times[0]?times[0]-60:0,equity:10000,dd:0}];
 times.forEach(t=>{equity+=batches.get(t);peak=Math.max(peak,equity);dd=Math.max(dd,peak-equity);curve.push({t,equity,dd})});
 return {curve,reconstructedDrawdown:rows.length?dd:0,final:equity};
}
function lineChart(built){
 if(built.curve.length<2)return '<div class="empty">此组合在原始 trades.csv 中没有模拟交易，不绘制伪造曲线。权威汇总仍来自 variant_results.csv。</div>';
 const rows=built.curve,W=1150,H=280,L=78,T=16,R=24,B=36,iw=W-L-R,ih=H-T-B;
 const first=rows[0].t,last=rows[rows.length-1].t;
 let ymin=Math.min(...rows.map(r=>r.equity),10000),ymax=Math.max(...rows.map(r=>r.equity),10000);
 const span=ymax-ymin||10;ymin-=span*.12;ymax+=span*.12;
 const x=t=>L+(t-first)/(last-first||1)*iw,y=v=>T+(ymax-v)/(ymax-ymin)*ih;
 let d=`M${x(rows[0].t)},${y(rows[0].equity)}`;
 for(let i=1;i<rows.length;i++)d+=`H${x(rows[i].t)}V${y(rows[i].equity)}`;
 let svg=`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="根据旧交易CSV重建的已实现权益"><title>根据旧交易CSV重建的已实现权益</title>`;
 for(let j=0;j<=4;j++){const v=ymin+(ymax-ymin)*j/4;svg+=`<line x1="${L}" x2="${W-R}" y1="${y(v)}" y2="${y(v)}" stroke="#e8edf2"/><text x="${L-8}" y="${y(v)+4}" text-anchor="end" fill="#8391a1" font-size="11">$${fmt(v,0)}</text>`}
 svg+=`<path d="${d}" fill="none" stroke="#087f83" stroke-width="2.4"/><line x1="${L}" x2="${W-R}" y1="${y(10000)}" y2="${y(10000)}" stroke="#9aa7b4" stroke-dasharray="3 5"/></svg>`;
 return svg;
}
function filtered(){
 let list=book();const q=$('search').value.trim().toLowerCase(),f=$('pnlfilter').value;
 if(q)list=list.filter(r=>[r.market_id,r.asset,r.side,r.time_utc,r.execution_utc].join(' ').toLowerCase().includes(q));
 if(f!=='all')list=list.filter(r=>f==='win'?r.net_pnl>0:f==='loss'?r.net_pnl<0:r.net_pnl===0);
 return list.sort((a,b)=>a.settle_ts-b.settle_ts||String(a.market_id).localeCompare(String(b.market_id)));
}
function renderTrades(){
 const list=filtered(),n=Number($('pagesize').value),pages=Math.max(1,Math.ceil(list.length/n)||1);
 page=Math.max(1,Math.min(page,pages));
 $('tradecount').textContent=book().length+'笔原始记录';
 $('paginationinfo').textContent=list.length?`筛选后 ${list.length} 笔 / 第 ${page} 页，共 ${pages} 页`:'筛选后 0 笔';
 $('prev').disabled=page<=1;$('next').disabled=page>=pages;$('export').disabled=!list.length;
 const slice=list.slice((page-1)*n,page*n);
 $('tradebody').innerHTML=slice.map(r=>`<tr><td>${escapeHtml(date(Date.parse(r.time_utc)/1000))}</td><td class="mono">${escapeHtml(r.market_id)}<br><span class="tiny">${escapeHtml(r.asset.toUpperCase())}</span></td><td>${r.side}<br><span class="tiny">实际 ${r.y_up==='1'||r.y_up===1?'Up':'Down'} · ${r.won==='1'||r.won===1?'赢':'输'}</span></td><td class="num">${pct(r.p_model)}</td><td class="num">${pct(r.persistent)}</td><td class="num">${fmt(r.q_scenario,4)}</td><td class="num">${money(r.fee)}</td><td class="num ${cls(r.net_pnl)}"><b>${money(r.net_pnl)}</b></td><td>${escapeHtml(date(r.settle_ts))}</td></tr>`).join('')||'<tr><td colspan="9"><div class="empty">没有符合筛选条件的真实计算记录</div></td></tr>';
}
function csvCell(v){return '"'+String(v??'').replace(/"/g,'""')+'"'}
function exportCSV(){
 const rows=filtered();if(!rows.length)return;
 const cols=["market_id","asset","duration_min","variant","scenario","side","time_utc","execution_utc","settle_ts","p_model","persistent","q_observed","q_scenario","shares","fee","gross_pnl","net_pnl","won","y_up","execution_limitation"];
 const text='\ufeff'+cols.join(',')+'\r\n'+rows.map(r=>cols.map(c=>csvCell(r[c])).join(',')).join('\r\n');
 const blob=new Blob([text],{type:'text/csv;charset=utf-8'}),url=URL.createObjectURL(blob),a=document.createElement('a');
 a.href=url;a.download='initial_3d_filtered_trades.csv';document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),500);
}
function render(){
 page=1;const s=summary(),rows=book(),built=reconstruct(rows),x=selected();
 const literal=x.v.startsWith('literal_');
 $('literalnote').style.display=literal?'block':'none';
 $('literalnote').textContent=literal?'这是字面一步概率诊断变体。它的概率事件与到期结果并不一致，不要把它包装成正确的到期概率模型。零笔交易只说明这个诊断定义没有触发，不是把空表写成盈利。':'';
 const cards=[['净盈亏',money(s.net_pnl),cls(s.net_pnl),'variant_results.csv'],['模拟笔数',fmt(s.trades,0),'','与 trades.csv 行数一致'],['胜率',pct(s.win_rate),'','无交易时为不适用'],['权威最大已实现回撤',money(s.max_realized_drawdown),'red','原汇总，不是图上重建值'],['最高同时占款',money(s.max_concurrent_capital),'','未到期按成本保留'],['期末现金',money(s.final_cash),'','初始 '+money(s.initial_capital)]];
 $('kpis').innerHTML=cards.map(z=>`<div class="card"><div class="label">${z[0]}</div><div class="metric ${z[2]}">${z[1]}</div><div class="tiny">${z[3]}</div></div>`).join('');
 $('equitychart').innerHTML=lineChart(built);
 $('equitynote').textContent=DATA.notes.equity+'。'+DATA.notes.equity_detail+(s.executable_net_pnl?'':' 可执行净盈亏留空：'+s.missing_reason);
 $('ddcards').innerHTML=`<div class="card"><div class="label">权威最大已实现回撤</div><div class="metric red">${money(s.max_realized_drawdown)}</div><div class="tiny">variant_results.csv，不按本图改写</div></div><div class="card"><div class="label">重建曲线上的回撤</div><div class="metric">${money(built.reconstructedDrawdown)}</div><div class="tiny">同秒结算合并后的净盈亏口径，可能与旧程序逐事件回撤不同</div></div>`;
 $('variantbody').innerHTML=DATA.variants.map(([id,name])=>{const r=DATA.summaries.find(z=>z.duration_min===x.d&&z.variant===id&&z.scenario===x.s);return `<tr class="${id===x.v?'active':''}"><td>${name}</td><td class="num">${r.trades}</td><td class="num">${pct(r.win_rate)}</td><td class="num ${cls(r.net_pnl)}">${money(r.net_pnl)}</td><td class="num">${money(r.max_realized_drawdown)}</td><td class="num">${money(r.final_cash)}</td></tr>`}).join('');
 renderTrades();
}
function init(){
 $('product').innerHTML=DATA.products.map(([id,name])=>`<option value="${id}">${name}</option>`).join('');
 $('variant').innerHTML=DATA.variants.map(([id,name])=>`<option value="${id}">${name}</option>`).join('');
 $('scenario').innerHTML=DATA.scenarios.map(([id,name])=>`<option value="${id}">${name}</option>`).join('');
 $('product').value='15';$('variant').value='terminal_e05_p87';$('scenario').value='fee_only';
 $('folds').innerHTML=DATA.folds.map(r=>`<tr><td>${r.duration_min}分钟</td><td>${Number(r.fold)+1}</td><td>${r.train_markets}</td><td>${escapeHtml(new Intl.DateTimeFormat('zh-CN',{timeZone:'Asia/Taipei',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hour12:false}).format(new Date(r.test_start_utc)))}</td><td>${escapeHtml(new Intl.DateTimeFormat('zh-CN',{timeZone:'Asia/Taipei',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hour12:false}).format(new Date(r.test_end_utc)))}</td><td class="num">${r.test_markets}</td></tr>`).join('');
 ['product','variant','scenario'].forEach(id=>$(id).addEventListener('change',render));
 ['search','pnlfilter','pagesize'].forEach(id=>$(id).addEventListener(id==='search'?'input':'change',()=>{page=1;renderTrades()}));
 $('prev').onclick=()=>{page--;renderTrades()};$('next').onclick=()=>{page++;renderTrades()};$('export').onclick=exportCSV;render();
}
init();
</script></body></html>
"""


def main() -> None:
    payload = build_payload()
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    html = PAGE.replace("__TICKET__", ticket_html("v1")).replace("__DATA__", data)
    if html.count('id="ticket"') != 1 or "__DATA__" in html or "__TICKET__" in html:
        raise SystemExit("report template was not filled")
    OUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUT} bytes={OUT.stat().st_size} trades={len(payload['trades'])} summaries={len(payload['summaries'])}")


if __name__ == "__main__":
    main()
