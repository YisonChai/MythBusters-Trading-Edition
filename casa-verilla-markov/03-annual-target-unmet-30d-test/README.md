# 年度目标核查与30日回测

请先打开 `年度训练_月度回测.html`，再读 `年度目标核查与回测结果.md`。

## 先说未完成的部分

没有完成一年训练。官方同口径300秒历史最早核实到2026-09-17 08:00台北，本次实际训练09-17 08:00至10-17 08:00，测试10-18 08:00至11-17 08:00，各30日。训练1436/1440个市场，测试1434/1440个市场。

这是BTC/ETH一小时合约的历史报价代理，不是5分钟合约，不是Bonereaper算法复刻，不是可执行或实盘收益。没有历史bid/ask和深度，不保证100份可以买到。没有注册、付费、钱包或交易。

测试月中474/1434份市场此前用于收益评估，1242/1434此前已下载，不是全新盲测。全部比例按真实历史市场ID计算。

## HTML使用

单文件，CSS、JS、图表数据和逐笔均内嵌，无CDN和自动联网。为了不把约61MB明文数据塞成大文件，内部使用gzip+base64，打开时由现代浏览器原生DecompressionStream解压。浏览器不支持时会显示明确错误，需要新版Chrome/Edge/Firefox。无需API密钥。

可以切换模型、BTC/ETH/共享组合、策略和成本；查看年度逐月缺口、已见研究日、资金/回撤、校准、状态稀疏性及半月稳定性；逐笔可搜索、排序、盈亏筛选、分页并导出筛选后的CSV。原始行情没有塞入HTML。

曲线是已实现盈亏加未结算全成本，不是盯市。初始10000美元，每市场100份最多一次，共享现金。240组合是独立账户，不可相加收益。资金释放按官方closedTime与到期较晚者代理，未证明同刻可赎回到账。

前后半月单独从10000开始；若现金受限，二者加总不必等于整月。另提供整月实际模拟成交按信号入场时间分组的队列损益，二者严格加总回整月。不要把队列损益误当该半月已实现权益变化。

## 主要文件

- `研究协议.md`：首次收益计算前冻结的目标、实际替代窗口及模型/策略/成本。
- `年度目标核查与回测结果.md`：完整结论和精确数字。
- `docs/解阻研究记录.md`：免费公开数据来源研究、证据限制与未采用原因。
- `docs/prior_model_baseline.py`：上次核心模型的审计副本，不会导入执行。
- `raw/markets.json`：逐合约官方规则、结算、token、费用快照及复用来源。
- `raw/prices/`：5844份Up/Down真实300秒价格原文。
- `raw/reference/`：Binance官方小时K线，仅核对标签。
- `raw/probes/`、`probe_summary.json`：跨年逐月及保留边界探针。
- `raw/alternatives/`、`alternative_coverage.json`：实际下载的免费HF快照、Parquet日期和schema审计，未混入模型。
- `raw/requested.json`、`missing.json`：计划格点与缺失请求，不代表所有计划市场都实际存在。
- `raw/prior_research_index.json`：此前下载/评估市场ID、来源文件和指纹。
- `logs/requests.jsonl`：新公开请求时间、HTTP状态、URL、指纹；`alternative_requests.jsonl`是Parquet等下载日志。
- `logs/reused_files.json`、`reused_month_requests.jsonl`：3636份复用价格原文的来源和原始抓取日志。
- `results/markets.csv`、`exclusions.csv`、`splits.csv`、`observations.csv`：清洗、剔除、窗口与实际观测。
- `monthly_coverage.csv`、`test_reuse.csv`、`test_reuse_daily.csv`：年度覆盖与已见日期，均位于results。
- `training_states.csv`、`state_diagnostics.csv`、`validation_candidates.csv`：状态稀疏、回退和全部预定义验证候选。
- `predictions.csv`、`prediction_metrics.csv`、`calibration.csv`：终局Up概率与校准。
- `signals.csv`、`trades.csv`、`equity_curves.csv`、`results.csv`：全部240组合信号、逐笔账本、曲线和汇总。
- `half_results.csv`、`half_prediction_metrics.csv`、`half_actual_cohorts.csv`：独立半月和整月真实模拟成交队列两种口径。
- `audit_checks.json`、`logs/reproduction.json`、`unit.log`、`html_test.json`、`loader_test.json`：自检证据。
- `FILES_SHA256.csv`：所有交付文件校验，不含该表本身和ZIP。

原始API和技术CSV保留带时区ISO及Unix时间以便核对。Polymarket为秒，Binance为毫秒，报告及HTML人类可读时间均转换成Asia/Taipei。不能把原始UTC时间直接当台北。

## 离线复现

需要Python3和numpy。Node.js用于静态UI和原生gzip测试，不是浏览器自动化。pyarrow只用于重新检查免费Parquet来源，不参与主模型。实际版本见logs/environment.json与requirements.txt。

```bash
cd /workspace/casa-verilla/year-backtest
python3 -m unittest discover -s src -p 'test_*.py' -v
python3 src/run.py
python3 src/coverage.py
python3 src/stability.py
python3 src/audit.py
python3 src/build_html.py
node src/test_html.js
node src/test_loader.js
node --check logs/extracted_ui.js
python3 src/write_report.py
python3 src/package.py
```

这些回测步骤只读交付原始缓存，不联网。重新抓取可运行src/download.py，跨年覆盖探测用src/probe.py，免费集检查用src/inspect_alternatives.py。后者需pyarrow。下载器会在存在上次月度缓存时复用，不存在则调用公开接口。未来重抓可能因保留期、状态更新而不同，不用于“复现同一输入”；精确复现应使用包内原文。

executable_net_pnl留空表示不可得，不是0。成本情景的交易集合可能不同，不是保证可成交的上下界。不要年化或把本次实际30日训练改称一年。

## 验收边界

已有实际数据审计、确定性重跑、Node静态DOM与原生gzip测试。尚未真实浏览器视觉验收，请主代理另派computerUse直接打开HTML。

没有启动本地服务。如果浏览器需要HTTP而非file，可自行运行：

```bash
python3 -m http.server 8878 --bind 127.0.0.1 --directory /workspace/casa-verilla/year-backtest
```

然后在本机浏览器打开http://127.0.0.1:8878/并点击HTML。无需外网，不用用户电脑。
