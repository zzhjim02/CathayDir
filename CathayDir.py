# -*- coding: utf-8 -*-
"""CathayDir —— PDF 横排 / 竖排识别工具。

独立软件，不属于 CathayHub，可单独拷走使用。

算法借自 **CathayPDG**（超星 PDG 批量转换工具）的 `pdg_core.detect_orientation_pdf`，
一行没改地搬过来，只把"抽几页"改得更密：

    投影法 —— 页面二值化后算「行投影」和「列投影」的起伏（归一化标准差）。
    横排文字：一行有字、一行没字 → 行起伏大。
    竖排文字：一列有字、一列没字 → 列起伏大。
    单页：rs > cs * 1.12 记横排一票；cs > rs * 1.12 记竖排一票；中间地带弃权。
    全书：票数相差 1.5 倍才下结论，否则报「横竖混排」。

CathayPDG 原版只抽 6 页（第 5 页 + 20/40/60/80/90%），本工具默认**每 10 页抽一页**
（第 1、11、21 … 页），样本多了，混排书和"前半横后半竖"的书更不容易判错。

依赖：PyMuPDF(fitz)、Pillow、numpy —— 就这三个，跟 CathayPDG 一样。

用法（命令行）：
    CathayDir.exe 甲.pdf 乙.pdf                    # 直接打结果表
    CathayDir.exe D:\\书库 --step 5                # 整个目录递归，每 5 页抽一页
    CathayDir.exe 书库 --csv report.csv            # 结果存成 CSV
    CathayDir.exe 甲.pdf --per-page                # 连每一页的分数一起打出来
    CathayDir.exe 甲.pdf --split-out D:\\分好类     # 按方向复制成 横排/ 竖排/ 未知/
    CathayDir.exe --selftest                       # 自己造样本验证算法

用法（窗口）：
    直接双击 CathayDir.exe                          # 不带参数就开窗口，拖文件进去就行

退出码：0 正常；2 有文件读不动；3 --selftest 没过。
"""
import argparse
import csv
import os
import re
import shutil
import sys

APP_NAME = 'CathayDir'
APP_VERSION = 'v0.1.1'
APP_TITLE = 'CathayDir PDF 横排 / 竖排识别工具'

# ---- CathayPDG 原版参数（改这两个数之前先看说明） -----------------------------
RATIO = 1.12      # 单页：行起伏要压过列起伏这么多倍才记一票
VOTE = 1.5        # 全书：多数派要压过少数派这么多倍才下结论
INK_MIN = 0.006   # 墨太少 = 空白页，跳过
INK_MAX = 0.5     # 墨太多 = 满版插图/底纹页，跳过
RENDER = 1.6      # 渲染放大倍数（PDG 实测值，再小就分不出笔画了）

LABEL_H = '横排'
LABEL_V = '竖排'
LABEL_U = '未知'


# ---------------------------------------------------------------- 判定内核
def _page_scores(im):
    """单页 → (行起伏, 列起伏)；空白页/满版页返回 None。

    借自 CathayPDG `pdg_core._page_scores`，原文不动。
    """
    import numpy as np
    g = im.convert('L')
    w, h = g.size
    k = max(1, int(max(w, h) / 900))
    if k > 1:
        g = g.resize((max(1, w // k), max(1, h // k)))
    a = np.asarray(g, dtype=np.float32)
    ink = (a < 128).astype(np.float32)
    m = ink.mean()
    if m < INK_MIN or m > INK_MAX:      # 空白页 / 满版插图页：跳过
        return None
    rows = ink.sum(axis=1)
    cols = ink.sum(axis=0)
    return (float(rows.std() / (rows.mean() + 1e-6)),
            float(cols.std() / (cols.mean() + 1e-6)))


def sample_indices(n, step=10, start=0):
    """抽样页号：从第 start 页起，每隔 step 页抽一页。

    CathayPDG 原版是『<10 页逐页，否则第 5 页 + 20/40/60/80/90%』（最多 6 页）。
    这里改成等距抽样，样本密得多；step 想调随便调。
    保证至少抽 1 页（再薄的书也有第 1 页）。
    """
    step = max(1, int(step))
    start = max(0, min(int(start), max(0, n - 1)))
    idx = list(range(start, max(n, 1), step))
    return idx or [0]


def _pixmap_to_image(pm):
    """pixmap → PIL 灰度图。

    ⚠️ 不能直接 `Image.frombytes('L', (w,h), pm.samples)`：PyMuPDF 的行字节数
    （stride）会对齐到 4 的倍数，宽度不是 4 的倍数时每行末尾会多几个字节，
    拼出来的图是斜的、后面算出来的投影全是错的。按 stride 先切整齐再用。
    """
    import numpy as np
    from PIL import Image
    stride = getattr(pm, 'stride', None) or pm.width
    buf = pm.samples
    if stride != pm.width:
        arr = np.frombuffer(buf, dtype=np.uint8)
        arr = arr.reshape(pm.height, stride)[:, :pm.width]
        return Image.fromarray(arr, mode='L')
    return Image.frombytes('L', (pm.width, pm.height), buf)


def detect_pdf(path, step=10, start=0, render=RENDER, progress=None):
    """判一本。返回 dict，字段见文件末尾 REPORT_FIELDS。

    progress(cur, total) 会被回调用来报进度（窗口模式用，命令行可以不管）。
    """
    import fitz
    out = {
        'path': path,
        'name': os.path.basename(path),
        'pages': 0, 'sampled': 0, 'used': 0, 'skipped': 0,
        'votes_h': 0, 'votes_v': 0, 'neutral': 0,
        'label': LABEL_U, 'confidence': 0.0, 'detail': '',
        'error': '', 'per_page': [],
    }
    try:
        doc = fitz.open(path)
    except Exception as e:
        out['error'] = '打不开：%s' % e
        out['detail'] = out['error']
        return out
    try:
        n = doc.page_count
        out['pages'] = n
        pages = sample_indices(n, step, start)
        out['sampled'] = len(pages)
        mat = fitz.Matrix(render, render)
        for k, i in enumerate(pages):
            if progress:
                progress(k + 1, len(pages))
            try:
                pm = doc[i].get_pixmap(matrix=mat, colorspace=fitz.csGRAY)
                s = _page_scores(_pixmap_to_image(pm))
            except Exception as e:
                out['skipped'] += 1
                out['per_page'].append((i + 1, '', '', '渲染失败：%s' % e))
                continue
            if not s:
                out['skipped'] += 1
                out['per_page'].append((i + 1, '', '', '空白页/满版插图页，跳过'))
                continue
            rs, cs = s
            out['used'] += 1
            if rs > cs * RATIO:
                tag = LABEL_H
                out['votes_h'] += 1
            elif cs > rs * RATIO:
                tag = LABEL_V
                out['votes_v'] += 1
            else:
                tag = '弃权'
                out['neutral'] += 1
            out['per_page'].append((i + 1, round(rs, 3), round(cs, 3), tag))
    finally:
        doc.close()

    hs, vs, tot = out['votes_h'], out['votes_v'], out['votes_h'] + out['votes_v']
    if tot == 0:
        out['label'] = LABEL_U
        out['confidence'] = 0.0
        out['detail'] = '没有能下判断的正文页（抽 %d 页，跳过 %d）' % (
            out['sampled'], out['skipped'])
    elif hs > vs * VOTE:
        out['label'] = LABEL_H
        out['confidence'] = round(hs / tot, 2)
        out['detail'] = '%d/%d 页判为横排（抽 %d 页，跳过 %d，弃权 %d）' % (
            hs, tot, out['sampled'], out['skipped'], out['neutral'])
    elif vs > hs * VOTE:
        out['label'] = LABEL_V
        out['confidence'] = round(vs / tot, 2)
        out['detail'] = '%d/%d 页判为竖排（抽 %d 页，跳过 %d，弃权 %d）' % (
            vs, tot, out['sampled'], out['skipped'], out['neutral'])
    else:
        out['label'] = LABEL_U
        out['confidence'] = round(max(hs, vs) / tot, 2)
        out['detail'] = '横竖混排：横 %d / 竖 %d（抽 %d 页，跳过 %d，弃权 %d）' % (
            hs, vs, out['sampled'], out['skipped'], out['neutral'])
    return out


REPORT_FIELDS = [
    ('name', '文件名'), ('pages', '总页数'), ('sampled', '抽了'),
    ('used', '有效'), ('skipped', '跳过'), ('votes_h', '横票'),
    ('votes_v', '竖票'), ('label', '结论'), ('confidence', '置信'),
    ('detail', '说明'),
]


# ---------------------------------------------------------------- 输出
def _width(s):
    """中文按 2 格宽算，命令行表格才对得齐。"""
    return sum(2 if ord(c) > 0x2E80 else 1 for c in s)


def _pad(s, n):
    s = str(s)
    return s + ' ' * max(0, n - _width(s))


def print_table(rows):
    cols = [(k, t) for k, t in REPORT_FIELDS if k != 'detail']
    widths = []
    for k, t in cols:
        w = _width(t)
        for r in rows:
            w = max(w, _width(str(r.get(k, ''))))
        widths.append(w + 2)
    line = ' '.join(_pad(t, widths[i]) for i, (k, t) in enumerate(cols))
    print(line)
    print('-' * min(120, _width(line)))
    for r in rows:
        print(' '.join(_pad(r.get(k, ''), widths[i]) for i, (k, t) in enumerate(cols)))
        if r.get('error'):
            print('     !! %s' % r['error'])
    print()
    for r in rows:
        print('  %s  %s' % (_pad(r.get('name', ''), 28), r.get('detail', '')))


def write_csv(rows, path, per_page=False):
    with open(path, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow([t for k, t in REPORT_FIELDS])
        for r in rows:
            w.writerow([r.get(k, '') for k, t in REPORT_FIELDS])
        if per_page:
            w.writerow([])
            w.writerow(['— 逐页明细 —'])
            w.writerow(['文件名', '页码', '行起伏', '列起伏', '该页判定'])
            for r in rows:
                for pno, rs, cs, tag in r.get('per_page') or []:
                    w.writerow([r.get('name', ''), pno, rs, cs, tag])


def split_out(rows, dest, move=False):
    """按结论把书复制（或移动）到「横排」「竖排」「未知」三个子文件夹里。"""
    done = 0
    for r in rows:
        if r.get('error') or not os.path.isfile(r['path']):
            continue
        sub = {LABEL_H: LABEL_H, LABEL_V: LABEL_V}.get(r['label'], LABEL_U)
        d = os.path.join(dest, sub)
        os.makedirs(d, exist_ok=True)
        tgt = os.path.join(d, r['name'])
        if os.path.abspath(tgt) == os.path.abspath(r['path']):
            continue
        n = 1
        stem, ext = os.path.splitext(r['name'])
        while os.path.exists(tgt):
            tgt = os.path.join(d, '%s(%d)%s' % (stem, n, ext))
            n += 1
        (shutil.move if move else shutil.copy2)(r['path'], tgt)
        done += 1
    return done


# ---------------------------------------------------------------- 找文件
def collect(paths, recursive=True):
    out = []
    for p in paths:
        if os.path.isdir(p):
            if recursive:
                for r, ds, fs in os.walk(p):
                    for f in fs:
                        if f.lower().endswith('.pdf'):
                            out.append(os.path.join(r, f))
            else:
                for f in os.listdir(p):
                    fp = os.path.join(p, f)
                    if f.lower().endswith('.pdf') and os.path.isfile(fp):
                        out.append(fp)
        elif os.path.isfile(p):
            out.append(p)
    seen = set()
    uniq = []
    for p in out:
        k = os.path.abspath(p).lower()
        if k not in seen:
            seen.add(k)
            uniq.append(p)
    return uniq


# ---------------------------------------------------------------- 窗口
def _natkey(s):
    """文件名自然序：第 2 册排在**第 10 册**前面（纯字典序会排反）。"""
    out = []
    for p in re.split(r'(\d+)', s or ''):
        if p.isdigit():
            out.append((1, int(p), ''))
        elif p:
            out.append((0, 0, p))
    return out


# ---- 排序（点表头那套逻辑放在模块级，好让 --selftest 直接验） ----------------
COLS = ('文件', '总页', '抽了', '跳过', '横票', '竖票', '结论', '置信')

COL_NUM = {'总页': 'pages', '抽了': 'sampled', '跳过': 'skipped',
           '横票': 'votes_h', '竖票': 'votes_v', '置信': 'confidence'}
LABEL_ORDER = {'横排': 0, '竖排': 1, '横竖混排': 2, '未知': 3}


def sort_key(row, col):
    """一列怎么比大小：文件名走自然序，结论走固定次序，其余按数字。"""
    if col == '文件':
        return _natkey(row.get('name', ''))
    if col == '结论':
        return [LABEL_ORDER.get(row.get('label', ''), 9)]
    v = row.get(COL_NUM.get(col, ''), 0)
    try:
        return [float(v)]
    except Exception:
        return [0.0]


def sort_rows(rows, col, desc=False):
    """按某列排序，**返回新的列表**，不动原来的。"""
    try:
        return sorted(rows, key=lambda r: sort_key(r, col), reverse=desc)
    except Exception:
        return list(rows)


def _icon_path():
    """打包后图标在 _MEIPASS 下，源码运行时就在脚本旁边。找不到就返回 None。"""
    cands = []
    _mei = getattr(sys, '_MEIPASS', None)
    if _mei:
        cands.append(os.path.join(_mei, 'app.ico'))
    cands.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.ico'))
    for c in cands:
        if os.path.isfile(c):
            return c
    return None


def _set_icon(root):
    """给窗口挂图标。失败就拉倒 —— 图标不影响功能，别为此崩在启动上。"""
    try:
        p = _icon_path()
        if p:
            root.iconbitmap(p)
    except Exception:
        pass


def run_gui(initial=None):
    """开窗口。initial 可以预先塞几个文件路径进来（`--gui 甲.pdf 乙.pdf`）。"""
    import threading
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    files = []
    for _p in (initial or ()):
        if _p not in files:
            files.append(_p)
    sort_state = {}      # 列名 -> True 表示从大到小；点一次表头翻一次面
    cols = COLS

    def row_values(r):
        """列表里一行的八格。显示、排序、导出都走这一份，别各写一套。"""
        try:
            conf = '%.2f' % float(r.get('confidence', 0) or 0)
        except Exception:
            conf = ''
        return (r.get('name', ''), r.get('pages', ''), r.get('sampled', ''),
                r.get('skipped', ''), r.get('votes_h', ''), r.get('votes_v', ''),
                r.get('label', ''), conf)

    def retitle(cols):
        """表头挂 ▲ / ▼，让人一眼看出当前按哪列、哪个方向排。"""
        for c in cols:
            arrow = ' ▼' if sort_state.get(c) else (' ▲' if c in sort_state else '')
            tv.heading(c, text=c + arrow)

    def refresh():
        """按 files 的顺序摆占位行（还没识别 / 刚开始识别时用）。"""
        tv.delete(*tv.get_children())
        for p in files:
            tv.insert('', 'end', iid=p,
                      values=(os.path.basename(p), '', '', '', '', '', '', '待识别'))
        retitle(cols)

    def redraw():
        """按 results 当前的顺序重画（排完序用它）。"""
        tv.delete(*tv.get_children())
        for r in results:
            pid = r.get('path', '') or ''
            try:
                tv.insert('', 'end', iid=pid, values=row_values(r))
            except Exception:            # 万一 iid 撞了（同一文件加两次）
                tv.insert('', 'end', values=row_values(r))
        retitle(cols)

    def sort_by(col):
        """点表头排序：同列再点一次就掉个头。"""
        desc = not sort_state.get(col, True)      # 第一次点 = 从小到大
        sort_state.clear()
        sort_state[col] = desc
        if results:
            results[:] = sort_rows(results, col, desc)
            # files 跟到同一个顺序，免得下次 refresh 又跳回去
            known = set(files)
            ordered = [r['path'] for r in results if r.get('path') in known]
            rest = [p for p in files if p not in set(ordered)]
            files[:] = ordered + rest
            redraw()
        elif col == '文件':
            files.sort(key=lambda p: _natkey(os.path.basename(p)), reverse=desc)
            refresh()
        var_status.set('按「%s」%s排列 —— 再点一次表头就是另一头'
                       % (col, '从大到小' if desc else '从小到大'))

    def add_files():
        got = filedialog.askopenfilenames(
            title='挑要识别的 PDF（可以多选）',
            filetypes=[('PDF 文件', '*.pdf'), ('所有文件', '*.*')])
        for g in got:
            if g not in files:
                files.append(g)
        refresh()

    def add_dir():
        d = filedialog.askdirectory(title='挑一个文件夹（会连子文件夹一起找）')
        if not d:
            return
        for g in collect([d]):
            if g not in files:
                files.append(g)
        refresh()

    def clear():
        del files[:]
        refresh()

    def export():
        if not results:
            messagebox.showinfo('还没识别', '先点「开始识别」，才有东西可以存。')
            return
        p = filedialog.asksaveasfilename(
            title='结果存成 CSV', defaultextension='.csv',
            filetypes=[('CSV 表格', '*.csv')],
            initialfile='横竖排识别结果.csv')
        if not p:
            return
        write_csv(results, p, per_page=bool(var_pp.get()))
        messagebox.showinfo('存好了', '已存到：\n%s' % p)

    def split():
        if not results:
            messagebox.showinfo('还没识别', '先点「开始识别」。')
            return
        d = filedialog.askdirectory(title='挑一个地方，按横排/竖排分三个文件夹放好')
        if not d:
            return
        n = split_out(results, d, move=False)
        messagebox.showinfo('分好了', '复制了 %d 本到：\n%s' % (n, d))

    def work():
        try:                       # 输入框里手滑填了别的，别让后台线程崩掉
            step = max(1, int(var_step.get() or 10))
        except Exception:
            step = 10
        rows = []
        for i, p in enumerate(list(files)):
            def prog(cur, tot, _i=i, _p=p):
                root.after(0, lambda: (
                    var_status.set('正在看《%s》第 %d/%d 个抽样页' % (
                        os.path.basename(_p), cur, tot)),
                    pb.configure(value=cur, maximum=max(1, tot))))
            r = detect_pdf(p, step=step, progress=prog)
            rows.append(r)

            def show(_r=r):
                try:               # 行数/iid 不对就别硬写，宁可什么都不做
                    if tv.exists(_r['path']):
                        tv.item(_r['path'], values=row_values(_r))
                except Exception:
                    pass
            root.after(0, show)
        results.clear()
        results.extend(rows)
        root.after(0, lambda: (
            var_status.set('识别完了：%d 本' % len(rows)),
            pb.configure(value=0),
            set_enabled(True)))

    def start():
        if not files:
            messagebox.showinfo('没有文件', '先点「加文件」或「加文件夹」。')
            return
        set_enabled(False)
        results.clear()
        sort_state.clear()   # 重新开始 = 回到原来的顺序
        refresh()
        threading.Thread(target=work, daemon=True).start()

    def set_enabled(on):
        st = 'normal' if on else 'disabled'
        for b in (btn_addf, btn_addd, btn_clear, btn_run, btn_csv, btn_split):
            b.configure(state=st)

    results = []
    root = tk.Tk()
    root.title('%s  %s  （算法借自 CathayPDG）' % (APP_TITLE, APP_VERSION))
    root.geometry('920x560')
    _set_icon(root)

    top = ttk.Frame(root, padding=6)
    top.pack(fill='x')
    btn_addf = ttk.Button(top, text='加文件', command=add_files)
    btn_addf.pack(side='left')
    btn_addd = ttk.Button(top, text='加文件夹', command=add_dir)
    btn_addd.pack(side='left', padx=4)
    btn_clear = ttk.Button(top, text='清空', command=clear)
    btn_clear.pack(side='left')
    ttk.Label(top, text='每几页抽一页：').pack(side='left', padx=(16, 2))
    var_step = tk.StringVar(value='10')
    ttk.Spinbox(top, from_=1, to=100, width=4, textvariable=var_step).pack(side='left')
    var_pp = tk.BooleanVar(value=False)
    ttk.Checkbutton(top, text='CSV 里带逐页明细', variable=var_pp).pack(side='left', padx=(12, 0))
    btn_run = ttk.Button(top, text='开始识别', command=start)
    btn_run.pack(side='left', padx=(16, 0))
    btn_csv = ttk.Button(top, text='存成 CSV', command=export)
    btn_csv.pack(side='left', padx=4)
    btn_split = ttk.Button(top, text='按方向分柜', command=split)
    btn_split.pack(side='left')

    mid = ttk.Frame(root, padding=(6, 0))
    mid.pack(fill='both', expand=True)
    tv = ttk.Treeview(mid, columns=cols, show='headings')
    for c in cols:
        # 点表头就按这一列排序，再点一次掉个头
        tv.heading(c, text=c, command=lambda _c=c: sort_by(_c))
        tv.column(c, width=90 if c != '文件' else 300, anchor='w')
    sb = ttk.Scrollbar(mid, orient='vertical', command=tv.yview)
    tv.configure(yscrollcommand=sb.set)
    tv.pack(side='left', fill='both', expand=True)
    sb.pack(side='right', fill='y')

    bot = ttk.Frame(root, padding=6)
    bot.pack(fill='x')
    var_status = tk.StringVar(
        value='把 PDF 拖进来 → 点「开始识别」（默认每 10 页抽一页）'
              ' —— 认完之后点表头可以按任意一列排序')
    ttk.Label(bot, textvariable=var_status).pack(side='left')
    pb = ttk.Progressbar(bot, mode='determinate')
    pb.pack(side='right', fill='x', expand=True, padx=(12, 0))

    if files:                       # 命令行带进来的文件，先把行摆上
        refresh()
    root.mainloop()


# ---------------------------------------------------------------- 自检
def _make_pdf(path, n, vertical):
    """造样本：vertical=False 横排（一行一行写），True 竖排（一列一列写）。"""
    import fitz
    doc = fitz.open()
    text = ('中華民國史料叢編第二十輯內政篇民政司檔案卷宗'
            '總統府秘書長呈報各省市縣政府組織章程修正草案')
    for _ in range(n):
        pg = doc.new_page(width=595, height=842)
        if vertical:
            x = 500
            for col in range(4):
                y = 80
                for ch in text[:26]:
                    pg.insert_text((x, y), ch, fontsize=13, fontname='china-s', rotate=0)
                    y += 26
                x -= 110
        else:
            y = 90
            for line in range(20):
                pg.insert_text((70, y), text[:28], fontsize=13, fontname='china-s')
                y += 32
    doc.save(path)
    doc.close()


def selftest():
    import tempfile
    tmp = tempfile.mkdtemp(prefix='pdfdir_')
    cases = []
    try:
        for tag, vert in (('横排', False), ('竖排', True)):
            p = os.path.join(tmp, '样本_%s.pdf' % tag)
            _make_pdf(p, 30, vert)
            cases.append((tag, p))
        ok = True
        for tag, p in cases:
            r = detect_pdf(p, step=10)
            good = (r['label'] == tag)
            ok = ok and good
            print('%s  造了一本%s书（30 页，每 10 页抽 1 页 → 抽 %d 页）→ 判为「%s」'
                  ' 横票%d/竖票%d  %s'
                  % ('  OK ' if good else '  FAIL', tag, r['sampled'], r['label'],
                     r['votes_h'], r['votes_v'], r['detail']))
        # ---- 排序（点表头那套逻辑） ----
        rows = [
            {'name': '第10册.pdf', 'pages': 100, 'sampled': 10, 'skipped': 0,
             'votes_h': 1, 'votes_v': 0, 'label': '横排', 'confidence': 0.5},
            {'name': '第2册.pdf', 'pages': 900, 'sampled': 90, 'skipped': 1,
             'votes_h': 0, 'votes_v': 3, 'label': '竖排', 'confidence': 0.9},
            {'name': '第1册.pdf', 'pages': 300, 'sampled': 30, 'skipped': 0,
             'votes_h': 2, 'votes_v': 0, 'label': '横排', 'confidence': 0.7},
            {'name': '丁种.pdf', 'pages': 50, 'sampled': 5, 'skipped': 5,
             'votes_h': 0, 'votes_v': 0, 'label': '未知', 'confidence': 0.0},
        ]
        cases = [
            ('文件', False, ['丁种.pdf', '第1册.pdf', '第2册.pdf', '第10册.pdf']),
            ('文件', True, ['第10册.pdf', '第2册.pdf', '第1册.pdf', '丁种.pdf']),
            ('总页', True, ['第2册.pdf', '第1册.pdf', '第10册.pdf', '丁种.pdf']),
            ('置信', True, ['第2册.pdf', '第1册.pdf', '第10册.pdf', '丁种.pdf']),
            ('横票', True, ['第1册.pdf', '第10册.pdf', '第2册.pdf', '丁种.pdf']),
            ('结论', False, ['第10册.pdf', '第1册.pdf', '第2册.pdf', '丁种.pdf']),
        ]
        for col, desc, want in cases:
            got = [r['name'] for r in sort_rows(rows, col, desc)]
            good = (got == want)
            ok = ok and good
            print('%s  按「%s」%s → %s'
                  % ('  OK ' if good else '  FAIL', col,
                     '降序' if desc else '升序', ' / '.join(got)))
            if not good:
                print('        期望 %s' % ' / '.join(want))
        if sort_rows(rows, '文件') is rows or [r['name'] for r in rows][0] != '第10册.pdf':
            ok = False
            print('  FAIL  sort_rows 应该返回新列表、不动原来的')
        else:
            print('  OK    sort_rows 返回新列表，原来的顺序没被改动')

        print('\n%s' % ('自检通过' if ok else '自检没过'))
        return 0 if ok else 3
    finally:
        try:
            shutil.rmtree(tmp, ignore_errors=True)
        except Exception:
            pass


# ---------------------------------------------------------------- 命令行
def main(argv=None):
    # 窗口版 exe（console=False）下 sys.stdout 是 None，print 会直接崩 —— 先兜住
    if sys.stdout is None:
        sys.stdout = open(os.devnull, 'w')
    if sys.stderr is None:
        sys.stderr = open(os.devnull, 'w')
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        run_gui()
        return 0
    ap = argparse.ArgumentParser(
        description='识别 PDF 是横排还是竖排（算法借自 CathayPDG，默认每 10 页抽一页）')
    ap.add_argument('paths', nargs='*', help='PDF 文件或文件夹（文件夹会递归找）')
    ap.add_argument('--step', type=int, default=10, help='每几页抽一页（默认 10）')
    ap.add_argument('--start', type=int, default=0, help='从第几页开始抽（默认 0 = 第 1 页）')
    ap.add_argument('--render', type=float, default=RENDER, help='渲染放大倍数（默认 1.6）')
    ap.add_argument('--csv', help='结果存成这个 CSV')
    ap.add_argument('--per-page', action='store_true', help='CSV 里附带逐页分数')
    ap.add_argument('--split-out', help='按结论复制到 横排/ 竖排/ 未知/ 三个子文件夹')
    ap.add_argument('--move', action='store_true', help='配合 --split-out：移动而不是复制')
    ap.add_argument('--gui', action='store_true', help='开窗口')
    ap.add_argument('--version', action='store_true', help='看版本号')
    ap.add_argument('--selftest', action='store_true', help='自己造样本跑一遍，验证算法')
    a = ap.parse_args(argv)

    if a.version:
        print('%s %s  （PDF 横排 / 竖排识别，算法借自 CathayPDG）'
              % (APP_NAME, APP_VERSION))
        return 0
    if a.selftest:
        return selftest()
    if a.gui or not a.paths:
        run_gui(a.paths)
        return 0

    files = collect(a.paths)
    if not files:
        print('没找到 PDF。给我文件或文件夹都行。')
        return 2

    rows = []
    for p in files:
        r = detect_pdf(p, step=a.step, start=a.start, render=a.render)
        rows.append(r)

    print_table(rows)
    if a.csv:
        write_csv(rows, a.csv, per_page=a.per_page)
        print('\nCSV 已存：%s' % a.csv)
    if a.split_out:
        n = split_out(rows, a.split_out, move=a.move)
        print('已%s %d 本到 %s' % ('移动' if a.move else '复制', n, a.split_out))
    bad = sum(1 for r in rows if r['error'])
    return 2 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
