# 流言终结者-交易版

[English](README.md)

![流言终结者-交易版。液压机下是一部屏幕碎裂、仍在运行量化策略的手机。](assets/banner.png)

**社交媒体上都说这招有效。放进回测里，还成立吗？**

我们把社交媒体上流传的交易方法写成可以执行和检验的规则，公开原帖、回测数据来源、代码和结果，让读者能自己复跑，看看结论是怎么得出的。

每个案例从原帖和一条可检验的主张出发，记录信号何时触发、交易如何执行、数据来源与样本区间、费用和滑点假设，以及预先设定的判定标准。报告给出扣除交易成本后的结果、回撤，并在适用时提供对照基准。结论适用于该次回测所列的条件。

## 回测记录

GitHub 不直接渲染下面的 HTML，本仓库也没有部署 GitHub Pages。请下载各版 `REPORT.html` 后离线打开。CasaVerilla 的三行是三次分开的窗口，收益不能加总。目录说明见 [casa-verilla-markov](casa-verilla-markov/README.md)。

| 来源 | 回测数据和代码 | 回测结果 | 最终结论 |
| --- | --- | --- | --- |
| [CasaVerilla](https://x.com/CasaVerilla/status/2122259548102656341)：首次研究，初始3日训练、3日滚动测试 | [src](casa-verilla-markov/01-initial-3d-3d/src) · [data](casa-verilla-markov/01-initial-3d-3d/data) · [协议](casa-verilla-markov/01-initial-3d-3d/研究协议_预先固定.md) | [REPORT.html](casa-verilla-markov/01-initial-3d-3d/REPORT.html)（下载后离线打开）。2026-11-11 08:00至2026-11-17 08:00台北，前3日初始训练，后3日每日扩展测试。15分钟 Chainlink 与1小时 Binance 分开。终局模型、元数据费、5%+87%：15分钟35笔、−60.73美元；1小时15笔、−27.19美元。字面一步概率是诊断变体，概率事件与到期结果不一致。报价代理，不是可执行收益。 | <img src="assets/stamps/inconclusive-zh.png" width="145" alt="尚无定论"> |
| [CasaVerilla](https://x.com/CasaVerilla/status/2122259548102656341)：30日训练、7日测试 | [src](casa-verilla-markov/02-month-training-7d-test/src) · [data](casa-verilla-markov/02-month-training-7d-test/data) · [协议](casa-verilla-markov/02-month-training-7d-test/研究协议.md) | [REPORT.html](casa-verilla-markov/02-month-training-7d-test/REPORT.html)（下载后离线打开）。训练2026-09-30 08:00至2026-10-30 08:00台北（1438/1440），测试2026-10-31 08:00至2026-11-07 08:00（330/336）。BTC/ETH 一小时。大模型元数据费率：5%+87%为34笔、+79.50美元；去持续率196笔、−511.86美元；配图价带109笔、+286.32美元。加入5分钟延迟及2美分后转亏。没有完成账户5分钟产品复刻。市场价 Brier 仍优于模型。 | <img src="assets/stamps/inconclusive-zh.png" width="145" alt="尚无定论"> |
| [CasaVerilla](https://x.com/CasaVerilla/status/2122259548102656341)：年度目标未达，实际30日训练、30日测试 | [src](casa-verilla-markov/03-annual-target-unmet-30d-test/src) · [data](casa-verilla-markov/03-annual-target-unmet-30d-test/data) · [协议](casa-verilla-markov/03-annual-target-unmet-30d-test/研究协议.md) | [REPORT.html](casa-verilla-markov/03-annual-target-unmet-30d-test/REPORT.html)（下载后离线打开）。年度目标未达：训练2026-09-17 08:00至2026-10-17 08:00台北（1436/1440），测试2026-10-18 08:00至2026-11-17 08:00（1434/1440），不是一年训练。测试市场33.05%此前已评估，86.61%此前已下载，不是全新盲测。大模型元数据费率：5%+87%为146笔、+195.92美元；去持续率927笔、−230.62美元；配图价带270笔、+865.76美元。延迟5分钟及2美分后分别为−282.08、−6837.91、−46.20美元。市场价概率基线仍优于大模型。`data/raw/alternatives/` 未入模。 | <img src="assets/stamps/inconclusive-zh.png" width="145" alt="尚无定论"> |

完成的案例会在最后一列盖上判定章。

| 印章 | 含义 |
| --- | --- |
| <img src="assets/stamps/confirmed-zh.png" width="145" alt="验证为真"> | 在所列回测条件下，证据支持原主张。 |
| <img src="assets/stamps/busted-zh.png" width="145" alt="已证伪"> | 在所列回测条件下，结果与原主张相矛盾。 |
| <img src="assets/stamps/inconclusive-zh.png" width="145" alt="尚无定论"> | 现有证据不足以判定真假。 |
