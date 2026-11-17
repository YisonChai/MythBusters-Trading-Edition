# MythBusters: Trading Edition

[简体中文](README.zh-CN.md)

![MythBusters: Trading Edition. A hydraulic press bears down on a cracked phone running a quant strategy.](assets/banner.png)

**Your feed says it works. Does the backtest agree?**

We take trading methods circulating on social media, turn their claims into rules we can test, and publish the evidence so readers can rerun the backtest and see what drives the result.

Each case starts with the original post and a testable claim. We document how signals become trades, the data source and period, fees and slippage assumptions, and the pass criteria. The report shows the net result, drawdown, and benchmark when relevant. The verdict applies to the claim under the tested conditions.

## Backtest log

This repository now keeps one CasaVerilla study: the annual target was not met, and the actual run is 30 days of training plus 30 days of testing. The earlier 3-day and 7-day directories are not in the tree and are not published. Notes: [casa-verilla-markov](casa-verilla-markov/README.md).

The intended report address is [report.html](https://yisonchai.github.io/MythBusters-Trading-Edition/report.html). The same file is also named [REPORT.html](https://yisonchai.github.io/MythBusters-Trading-Edition/REPORT.html) and is copied to the site root. The workflow publishes only that static file, not `data/`.

On 2026-11-17 the deployment did not go live. `actions/deploy-pages` returned HTTP 404 because GitHub Pages is not enabled, and the API call that would enable it returned HTTP 403 with this token. Until an admin sets [Settings → Pages](https://github.com/YisonChai/MythBusters-Trading-Edition/settings/pages) to GitHub Actions, those addresses answer 404. The file in the repository is [REPORT.html](casa-verilla-markov/03-annual-target-unmet-30d-test/REPORT.html).

| Source | Backtest data and code | Backtest results | Verdict |
| --- | --- | --- | --- |
| [CasaVerilla](https://x.com/CasaVerilla/status/2122259548102656341): annual target unmet, actual 30-day train and 30-day test<br>Official embed screenshot, not the full post page. An unauthenticated request to that URL returned HTTP 403. Taken 2026-11-17T14:51:05Z from `platform.twitter.com/embed/Tweet.html?id=2122259548102656341`. The embed still shows Show more.<br><a href="assets/casa-verilla-source-embed.png"><img src="assets/casa-verilla-source-embed.png" width="240" alt="Official X embed of CasaVerilla status 2122259548102656341, not a full-page capture. 2026-11-17T14:51:05Z."></a> | [src](casa-verilla-markov/03-annual-target-unmet-30d-test/src) · [data](casa-verilla-markov/03-annual-target-unmet-30d-test/data) · [protocol](casa-verilla-markov/03-annual-target-unmet-30d-test/研究协议.md) | [Report](https://yisonchai.github.io/MythBusters-Trading-Edition/report.html) · [REPORT.html in the repo](casa-verilla-markov/03-annual-target-unmet-30d-test/REPORT.html)<br>Train 2026-09-17 08:00 to 2026-10-17 08:00 Taipei (1436/1440); test 2026-10-18 08:00 to 2026-11-17 08:00 (1434/1440). Default view: large 6,600-state model, BTC+ETH, 3% edge + 87% persistence + 0.83–0.97 band, metadata fees: 270 trades and +$865.76. Realized equity from $10,000, not mark-to-market. The same strategy after a 5-minute delay plus 2 cents: 131 trades and −$46.20. Quote proxy, not an executable fill. 33.05% of test markets were previously evaluated and 86.61% were previously downloaded. The market-price Brier is still better. `data/raw/alternatives/` was not a model input.<br><a href="assets/casa-verilla-equity-curve.png"><img src="assets/casa-verilla-equity-curve.png" width="460" alt="Realized equity curve for the large 6,600-state model, BTC+ETH, 3% edge plus 87% persistence and the 0.83 to 0.97 band, metadata fees, from $10,000. Screenshot 2026-11-17."></a> | <img src="assets/stamps/confirmed-en.png" width="145" alt="Confirmed"> |

The Confirmed stamp in this row means the study can be checked and the quoted quote-proxy figures match `results.csv`. It does not mean one year of training was completed, or that the original post's stable or monthly profit was verified. The legend below says a Confirmed stamp means the evidence supports the claim under the stated test conditions. That legend is wider than this row: the tested quote-proxy result is in the table, including the −$46.20 delay case, and the original claim is not treated as supported.

Each completed case gets a verdict stamp in the last column.

| Stamp | What it means |
| --- | --- |
| <img src="assets/stamps/confirmed-en.png" width="145" alt="Confirmed"> | The evidence supports the claim under the stated test conditions. |
| <img src="assets/stamps/busted-en.png" width="145" alt="Busted"> | The results contradict the claim under the stated test conditions. |
| <img src="assets/stamps/inconclusive-en.png" width="145" alt="Inconclusive"> | The available evidence cannot settle the claim. |
