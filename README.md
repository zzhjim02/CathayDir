# CathayDir —— PDF 横排 / 竖排识别工具

一本 PDF 到底是横排还是竖排，肉眼扫一眼就知道，但几千本就没人干得动了。
CathayDir 干的就是这一件事：**批量判断一批 PDF 的文字排版方向**，
结果可以存成 CSV，也可以直接按「横排 / 竖排 / 未知」分成三个文件夹。

> 算法借自 **CathayPDG**（超星 PDG 批量转换工具）的 `pdg_core.detect_orientation_pdf`，
> 判定内核一行没改，只把抽样改密了。

[![version](https://img.shields.io/badge/version-v0.1.1-brightgreen)](https://github.com/zzhjim02/CathayDir/releases/latest)
![license](https://img.shields.io/badge/license-GPL--3.0-blue)
![platform](https://img.shields.io/badge/platform-Windows--x64-lightgrey)

## 📥 下载

**不用装 Python**：到 [Releases 页面](https://github.com/zzhjim02/CathayDir/releases/latest) 下 `CathayDir-v0.1.1-windows-x64.zip`，
解压后双击 `CathayDir PDF横竖排识别工具.exe` 就能用 —— 包里有 `sha256.txt` 可校验。
纯本地运行，不联网、不动原文件。

## 怎么用

### 窗口版（推荐）

双击 **`CathayDir PDF横竖排识别工具.exe`**：

1. 「加文件」或「加文件夹」（文件夹会连子文件夹一起找）
2. 「每几页抽一页」默认 **10** —— 想要更准就调小（比如 5），想更快就调大
3. 「开始识别」
4. 需要留档就点「存成 CSV」；要直接分类就点「按方向分柜」

### 排序（认完之后）

**点任意一列的表头就按这一列排序，再点一次掉个头**（表头会挂 ▲ 从小到大 / ▼ 从大到小）：

| 列 | 怎么排 |
|---|---|
| 文件 | 自然序 —— **第 2 册排在第 10 册前面**（纯字典序会反过来） |
| 总页 / 抽了 / 跳过 / 横票 / 竖票 / 置信 | 按数字大小 |
| 结论 | 横排 → 竖排 → 横竖混排 → 未知 |

排完之后「存成 CSV」和「按方向分柜」都跟着**当前看到的顺序**走；
点「开始识别」重新认一遍会回到添加顺序。

### 命令行版

批量处理时用 **`CathayDir命令行.exe`**（窗口版没有控制台，看不到输出）：

```
CathayDir命令行.exe 甲.pdf 乙.pdf                 # 直接打结果表
CathayDir命令行.exe D:\书库 --step 5              # 整个目录递归，每 5 页抽一页
CathayDir命令行.exe 书库 --csv 报告.csv           # 结果存成 CSV
CathayDir命令行.exe 甲.pdf --per-page             # 连每一页的行/列起伏一起看
CathayDir命令行.exe 书库 --split-out D:\分好类     # 按方向复制成 横排/ 竖排/ 未知/
CathayDir命令行.exe 书库 --split-out D:\分好类 --move   # 移动而不是复制
CathayDir命令行.exe --selftest                    # 自己造样本验证算法和排序
CathayDir命令行.exe --version
CathayDir命令行.exe --gui 甲.pdf                  # 带着几个文件直接开窗口
```

退出码：`0` 正常；`2` 有文件读不动；`3` `--selftest` 没过。

## 算法怎么判的

投影法，一句话讲完：

1. 页面灰度 → 缩到长边约 900 → 二值化（<128 算墨）
2. 算**行投影**和**列投影**的起伏（归一化标准差）
   - 横排文字：一行有字、一行没字 → **行**起伏大
   - 竖排文字：一列有字、一列没字 → **列**起伏大
3. 单页：`rs > cs × 1.12` 记横排一票；`cs > rs × 1.12` 记竖排一票；中间地带弃权
4. 全书：多数派票数要压过少数派 **1.5 倍**才下结论，否则报「横竖混排」
5. 墨占比 < 0.6%（空白页）或 > 50%（满版插图/底纹页）→ 该页跳过不算

**抽样**：每 10 页抽一页（第 1、11、21 … 页），`--step` 可调。
CathayPDG 原版只抽 6 页（第 5 页 + 20/40/60/80/90%），样本少了容易在
「前半横后半竖」这类书上判错。

### 实测（真实书库）

| 书 | 页数 | 结果 | 耗时 |
|---|---|---|---|
| 人民周刊 1926（民国刊物） | 471 | 竖排 0.98（44/45 票） | 5.3 s |
| 东北通史（现代学术书） | 709 | 横排 0.99（70/71 票） | 2.3 s |
| 全国中文期刊联合目录 | 1316 | 横排 0.68（50 页弃权，目录表格杂，合理） | 3.0 s |
| 义和团的起源及其运动 | 834 | 横排 0.99 | 3.0 s |

## 两个要说明的地方

**一、pixmap 转图片的坑（已修，CathayPDG 原版没有）**
PyMuPDF 的行字节数按 4 字节对齐，页宽不是 4 的倍数时每行末尾会多几个字节。
直接 `Image.frombytes('L', (w, h), pm.samples)` 拼出来的图是**斜的**，投影全错。
CathayPDG 一直没炸只是常见页宽刚好对齐。这里按 `pm.stride` 先切齐再转，
换什么尺寸都不会静默判错。

**二、判不出来的书会老实说「未知」**
表格多、插图满版、纯扫描无文字层的书，抽样页可能大量弃权，票数凑不够 1.5 倍
差距 —— 这时宁可报「横竖混排 / 未知」，也不硬猜。

## 目录结构

```
CathayDir PDF横竖排识别工具\
  CathayDir-DEV\         开发源码（CathayDir.py / CathayDir.spec / app.ico / README.md）
  CathayDir-REPO\        发行版（两个 exe + _internal）
```

单文件源码 `CathayDir.py`，只依赖 **PyMuPDF(fitz)、Pillow、numpy** 三个库，
外加标准库的 tkinter —— 单独拷走就能用，不绑任何别的软件。

## 版本

- **v0.1.1**（2026-10-04）— 结果列表支持**点表头排序**：文件名自然序、
  数值列按大小、结论按固定次序，再点一次反向；表头挂 ▲▼；CSV / 分柜跟随当前顺序。
  `--selftest` 顺带把排序也验了（9 项）。
- **v0.1.0** — 首发。算法借自 CathayPDG，抽样改为每 10 页一页，修 pixmap 对齐问题。

### 开发

排序逻辑放在**模块级**（`sort_key` / `sort_rows`），不在 tkinter 闭包里 ——
这样 `_probe_gui_sort.py` 能用一套假的 tkinter 把"点表头"端到端跑一遍
（9 项，含"存出来的 CSV 是不是界面上第一行"），**验证时不必真的弹出窗口**。
