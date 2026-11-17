# 离线月度马尔可夫回测包

先打开 `月度马尔可夫回测.html`，再读 `回测结果.md`。HTML已内嵌全部CSS、JavaScript和真实计算数据，可断网直接打开，不依赖CDN或服务器，无密钥输入。

## 重要边界

真实30日训练窗口和独立7日历史测试已经跑完，但训练剔除2份仲裁未最终确认合约，测试缺6个公开请求窗口。产品是BTC/ETH一小时市场，300秒真实报价采样。不是5分钟合约，不是Bonereaper算法复刻，不是实盘或可执行收益。

初始本金10000美元，每市场100份最多一笔，共享现金。曲线是已实现权益，未到期按入场全成本保留，不是盯市。所有CSV数值来自本次实际计算。单元测试中的人工小例子仅测试算法，不会进入任何历史收益、HTML或交易CSV。

240个组合是独立账户实验，每组合本金10000美元。汇总全量CSV前必须按模型、产品、策略、成本过滤，不能把跨组合的同市场记录当重复下单或累加利润。小模型是旧架构的300秒统一口径重建，不是旧逐分钟配置原样复跑。

全部报告时间使用Asia/Taipei。原始API与CSV保留Unix秒/毫秒和带时区ISO时间便于审计，代码统一转换，不能直接把UTC当台北时间。Binance请求为毫秒，Polymarket价格和内部运算为秒。

## 文件目录

- `月度马尔可夫回测.html`：交互看板，模型/产品/策略/成本切换，SVG权益/回撤，逐笔搜索排序筛选分页和CSV导出。
- `回测结果.md`：中文完整结论、数据缺口、模型与成本比较。
- `研究协议.md`：首次收益计算前冻结的研究假设。
- `前次方法审计.md`：报价时间、补值、费用与标签可用性审计。
- `src/download.py`：官方公开数据缓存抓取，含429退避，无鉴权。
- `src/run.py`：固定训练、验证、终局概率预测、信号、并发现金模拟和结果生成。
- `src/audit.py`：实际数据与全部240组合审计。
- `src/test_core.py`：8项最小算法测试。
- `src/build_html.py`、`src/dashboard.template.html`：离线HTML生成器与模板。
- `src/test_html.js`：Node静态DOM桩测试，不是浏览器自动化。
- `raw/events/`、`raw/markets.json`：市场原始规则、结算、token与费率快照。
- `raw/prices/`：Up/Down原始300秒报价。
- `raw/reference/`：Binance官方BTC/ETH小时K线。
- `raw/requested.json`、`raw/missing.json`：全部请求窗口和缺失窗口。
- `raw/five_minute_coverage*`：旧5分钟产品的分钟历史覆盖探测与原文。
- `docs/`：官方历史价格、费用文档抓取副本。
- `logs/requests.jsonl`：3733条主抓取请求、时间、HTTP结果和SHA256。
- `logs/freeze.json`：计算前协议和脚本冻结指纹。
- `logs/run*.log`、`unit.log`、`audit.log`、`html_test*`、`reproduction.json`：运行与测试证据。
- `results/markets.csv`、`exclusions.csv`、`splits.csv`、`observations.csv`：清洗、排除、窗口与观测。
- `results/training_states.csv`、`state_diagnostics.csv`：状态样本、覆盖、回退。
- `results/validation_candidates.csv`：所有预定义参数的验证分数。
- `results/predictions.csv`、`prediction_metrics.csv`、`calibration.csv`：到期Up概率及校准。
- `results/signals.csv`、`trades.csv`：逐笔信号与交易账本，含真实ID/URL、方向、时间、价格假设、预测/持续率、份数、费用、真实结算标签、损益和现金。
- `results/equity_curves.csv`、`results/results.csv`：完整资金曲线和240组合汇总。
- `results/dashboard_data.json`：与HTML同源的完整数据。
- `FILES_SHA256.csv`：交付文件校验表，不含该表本身和ZIP。

## 复现

需要Python3、numpy、Node.js。下载步骤另需curl；不需要账号、浏览器、钱包或API密钥。依赖的实际版本见 `logs/environment.json`。

```bash
cd /workspace/casa-verilla/month-backtest
python3 -m unittest discover -s src -p 'test_*.py' -v
python3 src/run.py
python3 src/audit.py
python3 src/build_html.py
node src/test_html.js
node --check logs/extracted_ui.js
```

默认训练和回测只读本包raw缓存，不联网。重新下载可运行 `python3 src/download.py`，但未来接口保留窗口和结算状态可能改变，不能保证日后重下载得到相同内容；审计复现应使用交付的原始文件。

`executable_net_pnl`留空并附缺失原因，不得当0。0笔组合不是亏损0风险策略，而是没有信号。延迟场景和其他成本场景可能跳过不同交易，不能机械作同一笔交易的可成交上下界。

## 尚需真实浏览器验收

尚未运行真实浏览器，不保证所有浏览器视觉效果都经过测试。可由主代理另派computerUse直接打开本地HTML。若浏览器不支持file协议，使用：

```bash
python3 -m http.server 8877 --bind 127.0.0.1 --directory /workspace/casa-verilla/month-backtest
```

然后在本机浏览器打开 `http://127.0.0.1:8877/` 并点击HTML。无需外网。此处未启动服务，未通过Shell驱动无头浏览器。
