# 在本仓库里怎么读这一版

计算脚本仍从本目录的 `raw/`、`results/`、`logs/` 读取。这三个名字是指向 `data/raw`、`data/results`、`data/logs` 的相对符号链接。模型、参数和已交付结果没有重算。

本目录原来的说明写的是 `/workspace/casa-verilla/year-backtest`。在这个仓库里，进入 `casa-verilla-markov/03-annual-target-unmet-30d-test/` 再运行只读本地缓存的脚本。

`src/download.py` 里还有一段可选绝对路径 `/workspace/casa-verilla/month-backtest`。第一版和第二版目录已经不在本仓库，那段路径这里也不存在。不要运行下载脚本，也不要把缺这个缓存说成已交付结果无法复核。已交付结果就在 `data/results/`。

`src/coverage.py` 在 `data/raw/prior_research_index.json` 已存在时直接读它，不再去找已删除的前两版目录。这个索引是 33.05% 与 86.61% 的来源，不要删掉后假装可以重算覆盖率。

`src/build_html.py` 会写 `年度训练_月度回测.html`，并且需要未纳入仓库的 `results/dashboard_data.json`。这里不能靠它重建页面。对外发布的是已经内嵌数据的 `REPORT.html`。

打开页面时的默认筛选是大模型 6600 状态、BTC+ETH、3% 差值 + 87% 持续率 + 0.83 至 0.97 价格带、元数据费率。这只改第一次显示的组合，不改任何 CSV。其余模型、策略和成本仍可切换。两个审计 HTML 仍按原来的初始选项打开，它们不是 Pages 入口。
