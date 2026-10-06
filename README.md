<div align="center">

# 🧭 CathayDir

**PDF 横排 / 竖排识别工具 · 一堆书摆在那儿，先摸清各自是横排还是竖排**

*开箱即用 · 双击即开 · 纯本地 · 不联网 · 绝不改动原件*

[![version](https://img.shields.io/github/v/release/zzhjim02/CathayDir?color=brightgreen)](https://github.com/zzhjim02/CathayDir/releases/latest)
[![license](https://img.shields.io/badge/license-GPLv3-blue.svg)](LICENSE)
[![platform](https://img.shields.io/badge/platform-Windows%2010%2B-brightgreen)]()
[![python](https://img.shields.io/badge/python-3.10%2B-blue)]()

**Cathay 系列 · 🔧 专项小工具**（碰上特定问题才用，用得少）

**拿到一批民国书、一批扫描件，不知道哪几本是竖排的？→ 每 10 页抽一页批量判，一目了然。**

结果能存成 CSV 留档，也能一键把文件分成「横排 / 竖排 / 未知」三个文件夹。

</div>

---

## 🔗 Cathay 人文社科工具链

这是一整套给人文社科研究者用的**本地**工具：从「找到一本书」，到「把它变成能搜、能读、能引用的 PDF」，再到「在上万本书里一秒检索」——**十来个小工具各自独立，不用全装，卡在哪一步就拿哪个**。

> ⭐ **主力软件**（日常用得最多，多数人装这五个就够了，按下面的顺序走）

| 顺序 | 我现在的情况 | 用这个 | 版本 |
|:--:|---|---|:--:|
| ① | 想找一本书，不知道去哪儿下 | [🔍 CathayFinder](https://github.com/zzhjim02/CathayFinder) —— 11 个渠道一起搜 | v1.1.0 |
| ② | 下下来是压缩包 / 一堆 `.pdg`，打不开 | [🧩 CathayPDG](https://github.com/zzhjim02/CathayPDG) —— 超星读秀压缩包转 PDF | v0.2.0 |
| ③ | 翻开是一页页影印图片，字选不中、复制不出来 | [🔤 CathayOCR](https://github.com/zzhjim02/CathayOCR) —— 让电脑看图认字 | v1.2.4 |
| ④ | 书攒了几百本，文件名乱、摆放乱 | [📚 CathayShelf](https://github.com/zzhjim02/CathayShelf) —— 批量建档归位、规范命名 | v0.4.8 |
| ⑤ | 书太多了，想一秒搜到某句话 | [🏛️ CathayHub](https://github.com/zzhjim02/CathayHub) —— 索引 · 检索 · 阅读 · 摘录 | v0.3.20（只有源码） |

> 🔧 **专项小工具**（碰上特定问题才用，用得少）

| 我现在的情况 | 用这个 | 版本 |
|---|:--:|:--:|
| PDF 打不开、一翻页就崩 | [🩺 CathayRepair](https://github.com/zzhjim02/CathayRepair) —— 先把坏 PDF 救回来 | v1.0.0 |
| 想把字「印」回 PDF（做成双层） | [📑 CathayRestore](https://github.com/zzhjim02/CathayRestore) —— 图还是原图，底下多一层字 | v1.0.0 |
| 想把 PDF 里的字**整批导出**成 TXT | [📤 CathayExtract](https://github.com/zzhjim02/CathayExtract) —— 文字层导出文本文件 | v1.2.3 |
| **一堆 PDF 摆在面前，想知道各自是横排还是竖排** | **🧭 CathayDir（你在这里）** —— 每 10 页抽一页批量判，能存 CSV / 分三个柜 | v0.1.1 |

整套**纯本地、不联网、不动你的原件**；每一步都能单独用，不强制串起来。
几个已停更的老项目收在文末的「📦 已停更项目」里，新用户不必理会。

---

## ❓ 这个仓库是什么？

一本 PDF 是横排还是竖排，你翻一页一眼就看出来了。
但**几百本、几千本**呢？没人干得动 —— 而这又偏偏是个绕不开的信息：

- 做 OCR 时，**竖排和横排要分开处理**，识别引擎的切分方向不一样，混在一起会整页认错字；
- 要挑 OCR 参数、要评估这批书好不好处理，**先得知道它们长什么样**；
- 建库之前想摸个底：这批里到底有几本竖排的老书？

CathayDir 就干这一件事：**批量判断一批 PDF 的文字排版方向**。
判定算法借自 **CathayPDG** 里的方向检测（`pdg_core.detect_orientation_pdf`），判定内核一行没改，只把抽样改密了。

## ✨ 功能特性

- **批量跑**：一次加几百个文件，或直接加整个文件夹（连子文件夹一起找）
- **抽样可调**：默认**每 10 页抽一页**（第 1、11、21 … 页），想要更准就调小（比如 5），想更快就调大
- **结果能排序**：**点任意一列的表头就按这一列排，再点一次掉个头**（表头挂 ▲ / ▼）
- **两种落地方式**：存成 CSV 留档；或按方向**复制 / 移动**成「横排 / 竖排 / 未知」三个文件夹
- **不硬猜**：判不出来的老实报「横竖混排 / 未知」，并给出票数让你自己判断
- **两个 exe**：窗口版给日常用，命令行版给批量脚本用
- **纯本地**：不联网、不上传、**只读不写**，你的原文件一个字节都不动

## 🚀 一分钟快速上手

1. 解压后双击 **`CathayDir PDF横竖排识别工具.exe`**
2. 点 **「加文件」** 或 **「加文件夹」**（加文件夹会连子文件夹一起找）
3. 「每几页抽一页」默认 **10** —— 一般不用改
4. 点 **「开始识别」**，等进度条走完
5. 要留档点 **「存成 CSV」**；要直接分类点 **「按方向分柜」**，选个目标文件夹即可

> 不用装 Python、不用装任何东西。**1000 页的书大约 3 秒判完**，几百本也就是抽杯茶的工夫。

## 📊 结果表怎么看

| 列 | 是什么意思 |
|:---|:---|
| **文件** | 文件名 |
| **总页** | 这本书一共多少页 |
| **抽了** | 实际抽了几页来判（每 10 页一页） |
| **跳过** | 抽到但**弃权**的页数 —— 空白页、满版插图页不参与投票，属正常 |
| **横票 / 竖票** | 抽到的页里，判成横排 / 竖排的各几票 |
| **结论** | 横排 / 竖排 / 横竖混排 / 未知 |
| **置信** | 多数派票数 ÷ 有效票数。**越接近 1 越笃定**，0.6 出头就说明这本书本身比较杂 |

**点表头排序**：

| 列 | 怎么排 |
|---|---|
| 文件 | 自然序 —— **第 2 册排在第 10 册前面**（纯字典序会反过来） |
| 总页 / 抽了 / 跳过 / 横票 / 竖票 / 置信 | 按数字大小 |
| 结论 | 横排 → 竖排 → 横竖混排 → 未知 |

排完之后，「存成 CSV」和「按方向分柜」都跟着**当前看到的顺序**走；
点「开始识别」重新认一遍会回到添加顺序。

## 📦 下载

> 发行包**自带运行环境**，解压即用，无需安装任何东西。

| 下载方式 | 链接 |
|:-------|:-----|
| 📥 **GitHub Releases** | [CathayDir v0.1.1](https://github.com/zzhjim02/CathayDir/releases/latest)（Assets 里下 `CathayDir-v0.1.1-windows-x64.zip`，约 56 MB） |
| 📥 **百度网盘**（密码 2026） | [CathayDir 0.1.1 —— 发行版 + 源码开发版 二合一](https://pan.baidu.com/s/1aU40yVsfcuvBp95bjqbDIg?pwd=2026) |
| 🔐 **校验** | 同页面 `sha256.txt`：`34fc6bfa8ed0b05131db7d7ecfc9b96eb2ad3b3a0da9955f52bbadb8f31a15e0` |
| 📄 **只有源码** | 本仓库 —— 单文件 `CathayDir.py`，装好三个依赖就能跑（见下） |

## 🖥️ 系统要求

| 项目 | 最低 | 推荐 |
|:----|:----|:----|
| 系统 | Windows 10 64 位 | Windows 10/11 64 位 |
| 内存 | 4 GB | 8 GB 以上 |
| 磁盘 | 200 MB | 500 MB 以上 |
| 其他 | 无需 Python、无需联网 | — |

## 🧑💻 命令行版 / 从源码运行

批量处理、要写进脚本时用 **`CathayDir命令行.exe`**（窗口版没有控制台，看不到输出）：

```bash
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

从源码跑（单文件，只依赖三个库）：

```bash
pip install pymupdf pillow numpy
python CathayDir.py                          # 图形界面
python CathayDir.py 书库 --step 10           # 命令行批量

# 打包（一次出两个 exe，共用一个 _internal，体积不翻倍）
pyinstaller --noconfirm CathayDir.spec
```

## 🔍 它凭什么判的（想抠细节再看）

<details>
<summary><b>投影法，一句话讲完</b></summary>

1. 页面灰度 → 缩到长边约 900 → 二值化（<128 算墨）
2. 算**行投影**和**列投影**的起伏（归一化标准差）
   - 横排文字：一行有字、一行没字 → **行**起伏大
   - 竖排文字：一列有字、一列没字 → **列**起伏大
3. 单页：`rs > cs × 1.12` 记横排一票；`cs > rs × 1.12` 记竖排一票；中间地带弃权
4. 全书：多数派票数要压过少数派 **1.5 倍**才下结论，否则报「横竖混排」
5. 墨占比 < 0.6%（空白页）或 > 50%（满版插图 / 底纹页）→ 该页跳过不算

**抽样**：每 10 页抽一页（第 1、11、21 … 页），`--step` 可调。
CathayPDG 原版只抽 6 页（第 5 页 + 20/40/60/80/90%），样本少了容易在「前半横后半竖」这类书上判错。
</details>

<details>
<summary><b>实测（真实书库）</b></summary>

| 书 | 页数 | 结果 | 耗时 |
|---|---|---|---|
| 人民周刊 1926（民国刊物） | 471 | 竖排 0.98（44/45 票） | 5.3 s |
| 东北通史（现代学术书） | 709 | 横排 0.99（70/71 票） | 2.3 s |
| 全国中文期刊联合目录 | 1316 | 横排 0.68（50 页弃权，目录表格杂，合理） | 3.0 s |
| 义和团的起源及其运动 | 834 | 横排 0.99 | 3.0 s |
</details>

<details>
<summary><b>顺手修掉的一个坑（CathayPDG 原版没有）</b></summary>

PyMuPDF 的行字节数按 4 字节对齐，页宽不是 4 的倍数时每行末尾会多几个字节。
直接 `Image.frombytes('L', (w, h), pm.samples)` 拼出来的图是**斜的**，投影全错。
CathayPDG 一直没炸，只是常见页宽刚好对齐。这里按 `pm.stride` 先切齐再转，换什么尺寸都不会静默判错。
</details>

## 📁 文件结构

```
CathayDir PDF横竖排识别工具\
├── CathayDir PDF横竖排识别工具.exe    # 窗口版（双击这个）
├── CathayDir命令行.exe                # 命令行版（批量 / 写脚本）
├── 使用说明.txt                       # 发行包里附的简明说明
├── _internal\                         # 运行环境（两个 exe 共用，别删）
└── sha256.txt                         # 校验值
```

本仓库中的源码：

```
├── CathayDir.py            # 全部逻辑都在这一个文件里（GUI + 命令行 + 算法）
├── CathayDir.spec          # PyInstaller 打包配置（一次出两个 exe）
├── app.ico                 # 图标
├── _probe_gui_sort.py      # 无窗口的排序自检（9 项）
├── LICENSE                 # GPL-3.0
└── README.md
```

## 📦 已停更项目

<details>
<summary><b>展开看四个已停更的项目（功能已并入后面的工具）</b></summary>

这些**代码都还在、也还能跑**，只是不再更新 —— 功能已经被上面某个工具收进去。
**如果你是新用户，直接去用右边那个替代品就行。**

| 停更项目 | 原本干什么 | 现在该用什么 |
|---|---|---|
| [CathaySimplify](https://github.com/zzhjim02/CathaySimplify) | 繁简转换 / 编码规范化 | **→ [CathayShelf](https://github.com/zzhjim02/CathayShelf)** |
| [CathayIndex](https://github.com/zzhjim02/CathayIndex) | 本地文件库索引 | **→ [CathayFinder](https://github.com/zzhjim02/CathayFinder)** 的「本地文件库索引」页签 ｜ **→ [CathayHub](https://github.com/zzhjim02/CathayHub)** Indexer |
| [CathayViewer](https://github.com/zzhjim02/CathayViewer) | 书库浏览 | **→ [CathayHub](https://github.com/zzhjim02/CathayHub)** Viewer |
| [CathayReader](https://github.com/zzhjim02/CathayReader) | 阅读 | **→ [CathayHub](https://github.com/zzhjim02/CathayHub)** Viewer |

</details>

---

## ❓ 常见问题

<details>
<summary><b>为什么有的书判成「未知」或「横竖混排」？</b></summary>

说明抽样页里横竖两派的票数没拉开 1.5 倍差距 —— 常见于表格多、插图满版、或者前后半本排版不一样的书。
这时看「横票 / 竖票」两列自己判断比硬猜靠谱，把「每几页抽一页」调小（比如 3）再跑一遍通常就清楚了。
</details>

<details>
<summary><b>「跳过」很多是不是有问题？</b></summary>

不是。空白页、版权页、满版插图页本来就没有正文墨迹，判了反而是噪声，程序主动弃权。
只要「抽了 − 跳过」剩下的票数还够（一般十来票），结论就可信。
</details>

<details>
<summary><b>会动我的原文件吗？</b></summary>

不会。默认**只读**。「按方向分柜」默认是**复制**到新文件夹；只有显式加 `--move`（或在界面里选移动）才会搬走原文件。
</details>

<details>
<summary><b>纯扫描件、没有文字层的 PDF 能判吗？</b></summary>

能。这个算法看的是**页面图像上的墨迹分布**（投影），不是 PDF 里的文字层，所以对纯扫描件同样有效 ——
这也是它比"看文字层坐标"类方法更通用的地方。
</details>

<details>
<summary><b>判完能拿来干什么？</b></summary>

最常见是**分流做 OCR**：竖排和横排分开跑，识别引擎的切分方向对上，错字率明显低。
也有人拿它建库前摸底、筛出馆里那批民国竖排刊物单独处理。
</details>

## 📝 更新日志

- **v0.1.1**（2026-10-04）— 结果列表支持**点表头排序**：文件名自然序、数值列按大小、结论按固定次序，再点一次反向；表头挂 ▲▼；CSV / 分柜跟随当前顺序。`--selftest` 顺带把排序也验了（9 项）。同日发布 Windows 发行包。
- **v0.1.0**（2026-10-04）— 首发。算法借自 CathayPDG，抽样改为每 10 页一页，修 pixmap 行对齐问题。

## 🧑🔧 开发说明

排序逻辑放在**模块级**（`sort_key` / `sort_rows`），不在 tkinter 闭包里 —— 这样
`_probe_gui_sort.py` 能用一套假的 tkinter 把「点表头」端到端跑一遍（9 项，含「存出来的 CSV 是不是界面上第一行」），
**验证时不必真的弹出窗口**。

## ⚖️ 许可

[GPL-3.0](LICENSE) © 2026
