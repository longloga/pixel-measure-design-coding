#!/usr/bin/env python3
"""範囲内の「インク行」（文字行、画像、ボタン）をデザインとレンダリング画像で 1 行ずつ比較し、1 つの表に並べる。

1 ブロック内で: どの行が縦にずれているか（段落間隔/margin の誤り）、どの行の終端 x が違うか
（font-size / letter-spacing / ブロック幅の誤り → 改行位置が変わる）、字面の高さが違うか（font-size の誤り）がわかる。
2 画像間の縦ズレ dy を自動探索する（最も多くの行が一致する値）ので、レンダリング上の位置を事前に知る必要はない。

  python3 rowcmp.py design.png shots/pc.png --box 260 2900 1180 3420
  python3 rowcmp.py design.png shots/pc.png --box 260 2900 1180 3420 --dy 20 --thr 40 --dscale 2

列: y (rel) = 範囲の最初の行からの y、h = 字面の高さ、x0-x1 = インクの端。
`<<` は |Δy| > 2（前の行との比較、つまりそこで発生した誤り）または |Δx1| > 3 または |Δh| > 1 のとき。
注意: body の `text-align: justify` により、改行位置が同じでも満行の x1 はデザインと異なる — 疑うべきなのは
別の文字で改行している場合のみ（段落最終行の x1 がずれている、または行数が違う）。
"""
import argparse
import numpy as np
from PIL import Image


def rows(path, box, scale, thr):
    im = np.asarray(Image.open(path).convert('RGB')).astype(int)
    x0, y0, x1, y1 = [int(round(v * scale)) for v in box]
    y0, y1 = max(y0, 0), min(y1, im.shape[0])
    reg = im[y0:y1, x0:x1]
    ink = np.abs(reg - reg[:, :1, :]).sum(axis=2) > thr          # 背景色 = 各行の左端カラムの色
    out, cur = [], None
    for i, line in enumerate(ink):
        xs = np.nonzero(line)[0]
        if len(xs):
            cur = [i, i, xs[0], xs[-1]] if cur is None else [cur[0], i, min(cur[2], xs[0]), max(cur[3], xs[-1])]
        elif cur is not None:
            out.append(cur); cur = None
    if cur is not None: out.append(cur)
    s = scale
    return [((a + y0) / s, (b - a + 1) / s, (c + x0) / s, (d + x0) / s) for a, b, c, d in out]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('design'); ap.add_argument('render')
    ap.add_argument('--box', type=float, nargs=4, required=True, metavar=('X0', 'Y0', 'X1', 'Y1'), help='CSS px trên design')
    ap.add_argument('--dy', type=float, help='lệch dọc render so với design (bỏ trống = tự dò)')
    ap.add_argument('--search', type=float, default=300, help='phạm vi tự dò dy (px)')
    ap.add_argument('--thr', type=int, default=40)
    ap.add_argument('--dscale', type=float, default=1); ap.add_argument('--rscale', type=float, default=1)
    a = ap.parse_args()
    d = rows(a.design, a.box, a.dscale, a.thr)
    if not d: print('Không thấy dòng mực nào trong vùng design'); return
    x0, y0, x1, y1 = a.box
    if a.dy is None:
        cand = rows(a.render, [x0, y0 - a.search, x1, y1 + a.search], a.rscale, a.thr)
        best = (-1, 0)
        for r in cand:
            sh = r[0] - d[0][0]
            score = sum(any(abs(q[0] - sh - p[0]) <= 2 and abs(q[1] - p[1]) <= 2 for q in cand) for p in d)
            if score > best[0] or (score == best[0] and abs(sh) < abs(best[1])): best = (score, sh)
        dy = best[1]
        print(f'dy tự dò = {dy:+.0f}px (khớp {best[0]}/{len(d)} dòng)')
    else:
        dy = a.dy
    r = rows(a.render, [x0, y0 + dy, x1, y1 + dy], a.rscale, a.thr)
    base_d, base_r = d[0][0], (r[0][0] if r else 0)
    print(f"{'design  y(rel) h  x0-x1':30s} | {'render  y(rel) h  x0-x1':30s} Δy  Δx1")
    prev = 0
    for i in range(max(len(d), len(r))):
        p = d[i] if i < len(d) else None; q = r[i] if i < len(r) else None
        fp = f"{p[0] - base_d:6.0f} {p[1]:4.0f}  {p[2]:.0f}-{p[3]:.0f}" if p else '-'
        fq = f"{q[0] - base_r:6.0f} {q[1]:4.0f}  {q[2]:.0f}-{q[3]:.0f}" if q else '-'
        tail = ''
        if p and q:
            ddy = (q[0] - base_r) - (p[0] - base_d); loc = ddy - prev; prev = ddy
            dx1 = q[3] - p[3]
            flag = abs(loc) > 2 or abs(dx1) > 3 or abs(q[1] - p[1]) > 1
            tail = f"{ddy:+4.0f} {dx1:+4.0f}" + ('  <<' if flag else '')
        elif p or q:
            tail = '  << số dòng khác'
        print(f'{fp:30s} | {fq:30s} {tail}')


if __name__ == '__main__':
    main()
