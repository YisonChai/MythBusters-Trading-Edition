# SOURCE_MANIFEST 的范围

`SOURCE_MANIFEST.csv` 仍是 2026-11-17 交接时的历史指纹。它的路径、字节数和 SHA256 没有改写。

这份清单同时记录了三个原始版本。当前仓库树只保留 `03-annual-target-unmet-30d-test/`。`01-initial-3d-3d/` 与 `02-month-training-7d-test/` 已从树中删除，不再参与页面发布。清单里这两版的行是历史记录，不是当前文件缺失。

`EXCLUSIONS.json` 与 `handoff.md` 同样保持交接时的原文。它们提到的缓存、嵌套压缩包和可重建 `dashboard_data.json` 仍然没有进入仓库。

各版 `ORIGINAL_FILES_SHA256.csv` 里的历史哈希也没有改。第三版 `REPORT.html` 后来为教学说明和打开时的默认筛选项改过；改动后的哈希记在 `EDIT_SHA256.csv`。两个旧 HTML 文件名仍是同一份未改默认项的审计副本，不是另一次实验，也不会被 GitHub Pages 发布。
