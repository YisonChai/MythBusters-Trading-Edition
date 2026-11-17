# MythBusters: Trading Edition

[简体中文](README.zh-CN.md)

![MythBusters: Trading Edition. A hydraulic press bears down on a cracked phone running a quant strategy.](assets/banner.png)

**Your feed says it works. Does the backtest agree?**

We take trading methods circulating on social media, turn their claims into rules we can test, and publish the evidence so readers can rerun the backtest and see what drives the result.

Each case starts with the original post and a testable claim. We document how signals become trades, the data source and period, fees and slippage assumptions, and the pass criteria. The report shows the net result, drawdown, and benchmark when relevant. The verdict applies to the claim under the tested conditions.

## Backtest log

GitHub does not render the HTML reports below, and GitHub Pages is not deployed. Download each `REPORT.html` and open it offline. The three CasaVerilla rows are separate windows; do not add their results together. Index: [casa-verilla-markov](casa-verilla-markov/README.md).

| Source | Backtest data and code | Backtest results | Verdict |
| --- | --- | --- | --- |
| [CasaVerilla](https://x.com/CasaVerilla/status/2122259548102656341): initial 3-day train, 3-day rolling test | [src](casa-verilla-markov/01-initial-3d-3d/src) · [data](casa-verilla-markov/01-initial-3d-3d/data) · [protocol](casa-verilla-markov/01-initial-3d-3d/研究协议_预先固定.md) | [REPORT.html](casa-verilla-markov/01-initial-3d-3d/REPORT.html) (download and open offline). 2026-11-11 08:00 to 2026-11-17 08:00 Taipei; first 3 days train, next 3 days expanding daily tests. 15-minute Chainlink and 1-hour Binance stay separate. Fee-only quote proxy, terminal 5%+87%: 35 trades and −$60.73 (15-minute); 15 trades and −$27.19 (1-hour). The one-step literal variant is a diagnostic whose probability event does not match expiry. | <img src="assets/stamps/inconclusive-en.png" width="145" alt="Inconclusive"> |
| [CasaVerilla](https://x.com/CasaVerilla/status/2122259548102656341): 30-day train, 7-day test | [src](casa-verilla-markov/02-month-training-7d-test/src) · [data](casa-verilla-markov/02-month-training-7d-test/data) · [protocol](casa-verilla-markov/02-month-training-7d-test/研究协议.md) | [REPORT.html](casa-verilla-markov/02-month-training-7d-test/REPORT.html) (download and open offline). Train 2026-09-30 08:00 to 2026-10-30 08:00 Taipei (1438/1440); test 2026-10-31 08:00 to 2026-11-07 08:00 (330/336). BTC/ETH 1-hour only. Large model, metadata-fee quote proxy: 5%+87% is 34 trades and +$79.50; without persistence, 196 trades and −$511.86; chart band, 109 trades and +$286.32. A 5-minute delay plus 2 cents turns these negative. No 5-minute product replication. The market-price Brier still beats the model. | <img src="assets/stamps/inconclusive-en.png" width="145" alt="Inconclusive"> |
| [CasaVerilla](https://x.com/CasaVerilla/status/2122259548102656341): annual target unmet, actual 30-day train and 30-day test | [src](casa-verilla-markov/03-annual-target-unmet-30d-test/src) · [data](casa-verilla-markov/03-annual-target-unmet-30d-test/data) · [protocol](casa-verilla-markov/03-annual-target-unmet-30d-test/研究协议.md) | [REPORT.html](casa-verilla-markov/03-annual-target-unmet-30d-test/REPORT.html) (download and open offline). Annual target unmet: train 2026-09-17 08:00 to 2026-10-17 08:00 Taipei (1436/1440) and test 2026-10-18 08:00 to 2026-11-17 08:00 (1434/1440), not one year of training. 33.05% of test markets were previously evaluated and 86.61% were previously downloaded, so this is not a fresh blind test. Large model, metadata-fee quote proxy: 5%+87% is 146 trades and +$195.92; without persistence, 927 trades and −$230.62; chart band, 270 trades and +$865.76. After a 5-minute delay and 2 cents: −$282.08, −$6,837.91, and −$46.20. The market-price baseline still beats the large model. Files under `data/raw/alternatives/` were not model inputs. | <img src="assets/stamps/inconclusive-en.png" width="145" alt="Inconclusive"> |

Each completed case gets a verdict stamp in the last column.

| Stamp | What it means |
| --- | --- |
| <img src="assets/stamps/confirmed-en.png" width="145" alt="Confirmed"> | The evidence supports the claim under the stated test conditions. |
| <img src="assets/stamps/busted-en.png" width="145" alt="Busted"> | The results contradict the claim under the stated test conditions. |
| <img src="assets/stamps/inconclusive-en.png" width="145" alt="Inconclusive"> | The available evidence cannot settle the claim. |
