from pathlib import Path
import csv,json,gzip,base64,html,hashlib
R=Path(__file__).resolve().parents[1]
def rows(name):
 out=[]
 for row in csv.DictReader((R/'results'/name).open()):
  for k,v in row.items():
   if k in ['model','asset','strategy','cost','half','skips','equity_basis']:continue
   try:row[k]=float(v) if v else None
   except (ValueError,TypeError):pass
  out.append(row)
 return out

data=json.loads((R/'results/dashboard_data.json').read_text());availability=json.loads((R/'results/availability.json').read_text());missing=json.loads((R/'raw/missing.json').read_text())
data['meta'].update(missing_count=len(missing),missing_markets=missing,reuse=availability['reuse'],annual_training_completed=False,requested_training_days=365,actual_training_days=30)
learned=[x for x in data['validation'] if x['model']!='market'];data['meta']['default_trained_model']=min(learned,key=lambda x:x['brier'])['model']
states=list(csv.DictReader((R/'results/training_states.csv').open()))
for d in data['diagnostics']:
 vals=[int(x['sample_count']) for x in states if x['model']==d['model']];d['histogram']=[sum(lo<=n<hi for n in vals) for lo,hi in [(1,2),(2,5),(5,10),(10,20),(20,10**9)]]
data['halves']=rows('half_results.csv');data['half_metrics']=rows('half_prediction_metrics.csv');data['half_cohorts']=rows('half_actual_cohorts.csv')
cols=next(list(g['trades'][0]) for g in data['groups'].values() if g['trades']);data['trade_columns']=cols
for g in data['groups'].values():g['trades']=[[t.get(c) for c in cols] for t in g['trades']]
blob=json.dumps(data,ensure_ascii=False,separators=(',',':'),allow_nan=False);packed=base64.b64encode(gzip.compress(blob.encode(),compresslevel=9,mtime=0)).decode()
cover=availability['coverage'];ct=[]
for x in cover:
 target=x['requested_year_training_markets'];actual=x['usable_training_markets'];pct=100*actual/target if target else 0
 bar=f'<div style="height:8px;background:#edf1f4;width:100px"><div style="height:8px;background:#087f83;width:{pct:.3f}%"></div></div>' if target else '不属于训练目标'
 ct.append(f'<tr><td>{x["month"]}</td><td class="num">{target}</td><td class="num">{actual}</td><td>{bar}</td><td class="num">{x["usable_testing_markets"]}</td><td class="num">{x["probe_with_300s"]} / {x["probe_markets_tested"]}</td><td>{html.escape(x["probe_fee_snapshots"])}</td><td>{html.escape(x["actual_fee_rate_snapshots"] or "未完整抓取")}</td></tr>')
reuse=availability['reuse'];dtrows=[]
for x in reuse['daily']:
 dtrows.append(f'<tr><td>{html.escape(x["day_start_taipei"].replace("T"," ").replace("+08:00"," 台北"))}</td><td class="num">{x["markets"]}</td><td class="num">{x["prior_evaluated"]}</td><td class="num">{x["prior_downloaded"]}</td></tr>')
coverage=f'''<section id="coverage" class="section card"><div class="sectionhead"><h2>365日目标的数据缺口</h2><span class="badge">实际可用训练 {availability['actual_training_markets']} / 年度目标 {availability['requested_training_markets']} 个市场</span></div><p>一年训练没有完成。目标2025-10-17 08:00至2026-10-17 08:00，实际采用2026-09-17 08:00至10-17 08:00，均为台北时间。更早市场元信息确实存在，但所测300秒报价已为空；永久3小时粒度不能冒充一小时市场的5分钟特征。</p><div class="tablewrap"><table><thead><tr><th>月份</th><th>年度目标市场数</th><th>可用训练市场</th><th>已取得训练覆盖</th><th>可用测试市场</th><th>有300秒点的探针 / 探针数</th><th>历史探针费率快照</th><th>实际下载费率</th></tr></thead><tbody>{''.join(ct)}</tbody></table></div><div class="subnote">月份按每月1日08:00台北划分。探针不是全月普查，0/2只表示所测两个合约无300秒点，不证明整月不存在市场。费率未知不能当作零费用。所有实际回测市场均逐合约保留规则、标签和费用快照。覆盖数据为全品种，不随交易组合筛选改变。</div><h3>已见日期告警</h3><p>测试1434个市场中，{reuse['prior_evaluated']}个（{100*reuse['evaluated_ratio']:.2f}%）此前用于收益评估，{reuse['prior_downloaded']}个（{100*reuse['downloaded_ratio']:.2f}%）此前已经下载。日历跨度分别涉及{reuse['evaluated_days']}/30与{reuse['downloaded_days']}/30个研究日。不能称全新盲测。</p><details><summary>逐日查看已评估与已下载数量</summary><div class="tablewrap"><table><thead><tr><th>研究日开始，之后24小时</th><th>真实市场</th><th>此前已评估</th><th>此前已下载</th></tr></thead><tbody>{''.join(dtrows)}</tbody></table></div></details><h3>公开替代源核查</h3><p>两份免费HF小时市场价格文件实际最早到2025年12月末、最晚到2026年4月26日，无法补齐全年连续窗口，且没有resolution_seconds供本模型同口径核对，因此未混入主回测。SII有更久的链上成交档案，但不是现成300秒双边报价，未冒充已完成重建。详情、版本、Parquet日期范围和原文均随包保存。</p></section>'''
text=(R/'src/dashboard.template.html').read_text().replace('__DATA__',packed).replace('__COVERAGE_SECTION__',coverage)
assert '—' not in text
out=R/'年度训练_月度回测.html';out.write_text(text)
meta={'html_bytes':out.stat().st_size,'json_sha256':hashlib.sha256(blob.encode()).hexdigest(),'uncompressed_embedded_bytes':len(blob.encode()),'compression':'gzip_base64_native_DecompressionStream','groups':len(data['groups']),'default_model':data['meta']['default_trained_model'],'overall_validation_best':data['meta']['champion_from_validation'],'annual_training_completed':False}
(R/'logs/html_meta.json').write_text(json.dumps(meta,indent=2));print(json.dumps(meta,indent=2))
