# CasaVerilla Markov quote-proxy studies

三个目录是三次分开的研究。训练窗、测试窗和产品不同，收益不能相加，也不能把辅助档案算进模型。

English notes are in the root [README](../README.md). GitHub does not render `REPORT.html`, and GitHub Pages is not deployed. Download a report and open it offline in a browser.

| 目录 | 实际范围 | 报告 |
| --- | --- | --- |
| [01-initial-3d-3d](01-initial-3d-3d/) | 2026-11-11 08:00至11-17 08:00台北。前3日初始训练，后3日每日扩展测试。BTC/ETH 的15分钟与1小时分开。 | [REPORT.html](01-initial-3d-3d/REPORT.html) 由真实 `variant_results.csv` 与 `trades.csv` 生成。本版原先没有 HTML。 |
| [02-month-training-7d-test](02-month-training-7d-test/) | 训练2026-09-30 08:00至10-30 08:00（1438/1440）；测试10-31 08:00至11-07 08:00（330/336）。 | [REPORT.html](02-month-training-7d-test/REPORT.html) 在原月度 HTML 上增加教学说明。[月度马尔可夫回测.html](02-month-training-7d-test/月度马尔可夫回测.html) 是未改字节的审计副本。 |
| [03-annual-target-unmet-30d-test](03-annual-target-unmet-30d-test/) | 年度目标未达。实际训练2026-09-17 08:00至10-17 08:00（1436/1440），测试10-18 08:00至11-17 08:00（1434/1440）。 | [REPORT.html](03-annual-target-unmet-30d-test/REPORT.html) 增加教学说明。[30日训练_30日回测.html](03-annual-target-unmet-30d-test/30日训练_30日回测.html) 与 [年度训练_月度回测.html](03-annual-target-unmet-30d-test/年度训练_月度回测.html) 字节相同，是同一份审计副本，不是两次实验。 |

## 打开方式

从版本目录用浏览器打开 `REPORT.html`，或在仓库根目录执行：

```bash
python3 -m http.server 8877 --bind 127.0.0.1
```

然后打开对应文件的本地地址。页面不请求行情、不读取密钥。第三版报告用浏览器原生 `DecompressionStream` 解压内嵌 gzip，需要较新的 Chrome、Edge 或 Firefox。

## 代码怎么找到数据

各版 `src/` 仍按版本目录下的 `raw/`、`results/`、`logs/` 读取。这三个名字是指向 `data/raw`、`data/results`、`data/logs` 的相对符号链接，用来兼容原来的路径。本次没有改模型、参数或结论，也没有把代码改写成另一套数据目录。

原说明里的 `/workspace/casa-verilla/backtest`、`month-backtest`、`year-backtest` 是当时的工作目录。在本仓库中，请进入对应版本目录再运行 `src/` 里的计算脚本。第三版 `src/download.py` 仍保留一段可选的旧绝对路径，只在重新下载时尝试复用月度缓存。本次没有运行任何下载脚本。主实验只读已交付的 `data/`。

## 什么没有进入模型

第三版 `data/raw/alternatives/ywf1112` 与 `data/raw/alternatives/aliplayer1` 是未入模的公开核查原文，用来审计覆盖范围。它们不是全年训练数据。

`SOURCE_MANIFEST.csv` 是交接时的原始指纹，12948 个文件的路径、大小和 SHA256 都按交付核对过，本文件不改。各版 `ORIGINAL_FILES_SHA256.csv` 是更早的历史清单，其中列出、但本次有意不带的缓存、嵌套压缩包和可重建 `dashboard_data.json` 见 `EXCLUSIONS.json`。那些缺项不是数据丢失。年版 `dashboard_data.json` 约 109MB，超过普通单文件限制，且已有 HTML 内嵌同一份图表数据，所以没有提交。

`EDIT_SHA256.csv` 只记录这次为教学章节、首版报告和仓库入口新增或改动的文件。第二、三版 `REPORT.html` 的旧指纹等于对应审计副本；改动后的新指纹写在这里。
