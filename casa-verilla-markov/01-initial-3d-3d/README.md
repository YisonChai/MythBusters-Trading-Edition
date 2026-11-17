# CasaVerilla Polymarket 公开数据离线代理回测

先读 [回测结果.md](回测结果.md)。这是实际跑过的价格序列代理研究，不是可执行收益回测，不是Bonereaper源码复刻。

## 复现

已提供完整原始数据，收益运算不联网。需要Python3和requirements.txt所列numpy版本（本机已有，没有为此次任务安装依赖）。

```bash
cd /workspace/casa-verilla/backtest
python3 -m unittest discover -s src -p 'test_*.py' -v
python3 src/backtest.py
python3 src/audit.py
python3 src/report.py
```

重新获取原始数据的可选步骤：`python3 src/download.py`。它只访问公开GET接口，有缓存、限速和退避，不读取任何凭证、不访问钱包、不提交订单；已经下载的文件会直接复用，严谨复现应先使用交付快照而不是把新抓数据混入旧结果。

## 文件

- 研究协议_预先固定.md：首次结果前固定的样本、模型、变体和成本规则。
- src/download.py：公开数据下载，UTC请求区间固定。
- src/backtest.py：只有本地文件读写，无网络。
- src/test_core.py、src/audit.py：单元测试与真实数据审计。
- src/report.py：从结果CSV生成中文说明与按入场日分组账本。
- raw/markets.json：1440个真实市场及完整规则、结算标签。
- raw/events/：官方批量原始回复。
- raw/prices/：两边分钟价格原始回复。
- raw/reference/：288根Binance1小时K线，仅对应Binance结算市场；没有替换Chainlink结果。
- raw/trades/：20个市场的官方成交覆盖样本，不用它假装模拟订单成交。
- raw/*probe*、discovery*：探索与错误排查快照，不参与计算；有一份2025年同名slug探针，研究白名单仅由requested_markets.json和markets.json决定。
- docs/：官方分钟历史、费用、盘口接口文档。
- results/market_manifest.csv：每个合约的来源、规则、赢家、交叉核对、观察数与排除原因。
- results/exclusions.csv：本次无排除，只有列名。
- results/folds.csv：实际训练/测试市场数及最后可用标签时间。CSV时间为带时区UTC，中文报告已换台北时间。
- results/all_predictions.csv：每分钟特征及各模型预测，含原始时间和可用时间。
- results/signals.csv：每个变体首次入场信号。
- results/trades.csv：在明确成本假设下的模拟逐笔账本，不是真实fill。
- results/variant_results.csv：100行预先声明的策略/产品/场景组合。
- results/calibration.csv：Brier及校准分箱；一步概率版明确标为非终局概率。
- results/bootstrap_diagnostic.csv：描述性市场簇重采样，非严格显著性检验。
- results/daily_entry_cohorts.csv：按台北入场日分组的最终结算损益，不是当日盯市利润。
- logs/：抓取来源时间与hash、协议hash冻结、两次运行和审计、环境及重现一致性。

## 关键边界

没有历史bid/ask或深度，executable_net_pnl始终NA。quote0/fee_only/stress价格都是公开价格序列上的情景成本，绝不保证当时100份可成交。无交易时胜率和Brier空白表示没有样本，不是0胜率；有交易且全输时才是0。所有真实市场收益结算使用官方0/1结果，不生成虚假历史行情。单元测试中的手写数据仅用于函数测试，从不进入研究结果。

每市场每变体一笔，100份，初始模拟现金10000美元，不杠杆、不叠加同一市场。不把周转成交额当本金；最大回撤仅为已实现权益，不是盯市。

## 来源

- https://x.com/CasaVerilla/status/2122259548102656341
- https://gamma-api.polymarket.com/events
- https://docs.polymarket.com/api-reference/markets/get-a-tokens-price-history
- https://docs.polymarket.com/api-reference/feeds/list-account-activity.md
- https://docs.polymarket.com/trading/fees.md
- https://docs.polymarket.com/api-reference/market-data/get-order-book.md
- https://docs.polymarket.com/api-reference/geoblock
- https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints

原始请求的完整查询URL与时间逐条见logs/download_manifest.jsonl，不在README列2880条URL。使用标准curl可读取官方公开历史；Python urllib探针曾收到Cloudflare1010，未伪造浏览器身份或导入cookies。官方公开网页下载方式成功后保持请求节流。
