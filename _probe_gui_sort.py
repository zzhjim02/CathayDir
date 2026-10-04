# -*- coding: utf-8 -*-
"""端到端验证「点表头排序」——用假的 tkinter，不弹真窗口。

跑法：python _probe_gui_sort.py
"""
import os
import shutil
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)


# ---------------------------------------------------------------- 假 tkinter
class Widget(object):
    def __init__(self, master=None, *a, **k):
        self.master = master

    def pack(self, *a, **k):
        return self

    def configure(self, *a, **k):
        pass

    def set(self, *a, **k):
        pass


class Tree(Widget):
    _ALL = []

    def __init__(self, *a, **k):
        self.kids = []
        self.vals = {}
        self.heads = {}
        self.cmds = {}
        Tree._ALL.append(self)

    def heading(self, c, **kw):
        self.heads.setdefault(c, {})
        if 'text' in kw:
            self.heads[c]['text'] = kw['text']
        if 'command' in kw:
            self.cmds[c] = kw['command']

    def column(self, c, **kw):
        pass

    def insert(self, parent, index, iid=None, values=()):
        if iid is None:
            iid = 'gen%d' % len(self.kids)
        if iid in self.vals:
            iid = iid + '#%d' % len(self.kids)
        self.kids.append(iid)
        self.vals[iid] = tuple(values)
        return iid

    def delete(self, *ids):
        for i in ids:
            self.kids = [k for k in self.kids if k != i]
            self.vals.pop(i, None)

    def get_children(self):
        return list(self.kids)

    def item(self, iid, values=None):
        if values is not None:
            self.vals[iid] = tuple(values)
        return {'values': self.vals.get(iid, ())}

    def exists(self, iid):
        return iid in self.vals

    def yview(self, *a):
        pass


class Var(object):
    def __init__(self, value=None):
        self.v = value

    def get(self):
        return self.v

    def set(self, v):
        self.v = v


class Root(object):
    def __init__(self, *a, **k):
        BUTTONS.clear()

    def title(self, *a):
        pass

    def geometry(self, *a):
        pass

    def iconbitmap(self, *a):
        pass

    def mainloop(self):
        pass

    def after(self, ms, fn=None, *a):
        if callable(fn):
            fn(*a)


BUTTONS = {}


class Button(Widget):
    def __init__(self, master=None, text='', command=None, **k):
        self.text = text
        self.command = command
        BUTTONS[text] = self

    def configure(self, **k):
        pass


def install_fake_tk():
    tk = type(sys)('tkinter')
    tk.Tk = Root
    tk.StringVar = Var
    tk.BooleanVar = Var
    tk.IntVar = Var

    ttk = type(sys)('tkinter.ttk')
    ttk.Frame = Widget
    ttk.Label = Widget
    ttk.Button = Button
    ttk.Spinbox = Widget
    ttk.Checkbutton = Widget
    ttk.Scrollbar = Widget
    ttk.Progressbar = Widget
    ttk.Treeview = Tree
    tk.ttk = ttk

    fd = type(sys)('tkinter.filedialog')
    fd.askopenfilenames = lambda **k: ()
    fd.askdirectory = lambda **k: ''
    fd.asksaveasfilename = lambda **k: ''
    tk.filedialog = fd

    mb = type(sys)('tkinter.messagebox')
    for n in ('showinfo', 'showwarning', 'showerror', 'askyesno'):
        setattr(mb, n, lambda *a, **k: None)
    tk.messagebox = mb

    sys.modules['tkinter'] = tk
    sys.modules['tkinter.ttk'] = ttk
    sys.modules['tkinter.filedialog'] = fd
    sys.modules['tkinter.messagebox'] = mb

    # 线程改成同步跑，测试里不用 sleep。
    # ⚠️ 只能替换 Thread **类**，不能整个换掉 threading 模块 ——
    #    fitz / numpy 内部要用真 threading，换掉之后页面像素会算错（抽到的页全变"跳过"）。
    import threading as _real

    class SyncThread(object):
        def __init__(self, target=None, daemon=False, args=()):
            self.target = target
            self.args = args

        def start(self):
            if self.target:
                self.target(*self.args)

    _real.Thread = SyncThread


install_fake_tk()
import CathayDir as D


def main():
    fails = []

    def check(desc, got, want):
        good = (got == want)
        if not good:
            fails.append(desc)
        print('%s  %s' % ('  OK ' if good else '  FAIL', desc))
        if not good:
            print('         实际: %s' % (got,))
            print('         期望: %s' % (want,))

    tmp = tempfile.mkdtemp(prefix='probe_gui_sort_')
    try:
        # 名字故意用同一前缀：只有前缀相同，才验得到"第 2 册在第 10 册前面"
        specs = [('丛编第10册', 20, False), ('丛编第2册', 60, False), ('丙字单册', 40, True)]
        paths = []
        for nm, n, vert in specs:
            p = os.path.join(tmp, '%s.pdf' % nm)
            D._make_pdf(p, n, vert)
            paths.append(p)

        D.run_gui(paths)
        tv = Tree._ALL[-1]

        names = [tv.item(i)['values'][0] for i in tv.get_children()]
        check('进窗口摆出 %d 行占位' % len(paths),
              sorted(names), sorted(['%s.pdf' % s[0] for s in specs]))

        BUTTONS['开始识别'].command()
        rows = [tv.item(i)['values'] for i in tv.get_children()]
        check('识别完 %d 行都有结论' % len(paths),
              sorted([r[6] for r in rows]), sorted(['横排', '横排', '竖排']))

        pages_of = lambda: [tv.item(i)['values'][1] for i in tv.get_children()]
        tv.cmds['总页']()
        asc = pages_of()
        check('点一次「总页」= 从小到大', asc, sorted(asc))
        check('   表头挂升序箭头',
              [c for c, h in tv.heads.items() if '▲' in (h.get('text') or '')],
              ['总页'])
        tv.cmds['总页']()
        desc = pages_of()
        check('再点一次「总页」= 从大到小', desc, sorted(desc, reverse=True))
        check('   表头挂降序箭头',
              [c for c, h in tv.heads.items() if '▼' in (h.get('text') or '')],
              ['总页'])

        tv.cmds['文件']()
        fn = [tv.item(i)['values'][0] for i in tv.get_children()]
        check('点「文件」= 自然序（第2册 先于 第10册）',
              fn, ['丙字单册.pdf', '丛编第2册.pdf', '丛编第10册.pdf'])

        tv.cmds['竖票']()
        tv.cmds['竖票']()
        vv = [(tv.item(i)['values'][0], tv.item(i)['values'][5])
              for i in tv.get_children()]
        check('点「竖票」降序 = 竖排书排最前', vv[0][0], '丙字单册.pdf')

        csv_path = os.path.join(tmp, 'out.csv')
        sys.modules['tkinter.filedialog'].asksaveasfilename = lambda **k: csv_path
        BUTTONS['存成 CSV'].command()
        body = open(csv_path, encoding='utf-8-sig').read().splitlines()
        check('存出来的 CSV 第一行 = 界面上第一行',
              body[1].split(',')[0], '丙字单册.pdf')

        print('\n%s' % ('全部通过' if not fails else '有 %d 项没过' % len(fails)))
        return 0 if not fails else 1
    finally:
        try:
            shutil.rmtree(tmp, ignore_errors=True)
        except Exception:
            pass


if __name__ == '__main__':
    sys.exit(main())
