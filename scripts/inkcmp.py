#!/usr/bin/env python3
"""デザイン画像とレンダリング画像の 1 カラム内で「インク行」（文字ブロック / 画像 / ボタン）を 1 つずつ比較 → 実際の縦方向の間隔。

XD/Figma が無いとき、またはデザイン画像上で xdpos.py の結果を検証するときに使う。x0..x1 のカラム内だけを走査する
（計測対象のブロックだけを含むカラムを選び、横の画像や装飾を避ける）ため、大きな帯で比較する pixeldiff では
見逃す行間のマージンも検出できる（L-SHOT-11）。

  python3 inkcmp.py design.png render.png --box 2520 3020 100 560
  python3 inkcmp.py design@2x.png shots/pc.png --dscale 2 --box 2520 3020 100 560 --roff 6 --thr 150 --gap 3

--box Y0 Y1 X0 X1 : デザイン側の CSS px での範囲。--roff N: render が最初から N px ずれている（例: 上のセクションがずれている）
--thr  : 各行の背景色（中央値）との色差のしきい値（画像/グラデーション背景 → 150〜200 に上げる）
--gap  : 同じブロックとみなす空白行の最大数（複数行の文字が分かれてしまう場合 → 3〜4）
列: h（ブロックの高さ）、gap（前のブロックまでの余白）、dTop（上端のズレ）、
     Δloc = dTop − 直前の有効ブロックの dTop = そのブロックの直上で直すべき margin/padding の量（top→top で比較するので
     数字や画像のレンダリング高さが 1〜2px 違ってもノイズにならない）。高さが --hdiff px 以上異なるブロック（装飾に
     くっついた、改行位置が違う）は "?" を付けてスキップ → 計測したい場合は --box を狭める。
|Δloc| > --tol かつ |dTop − 先頭ブロックの dTop| > --tol のブロックがあれば exit 1（既定 1）。
"""
import argparse, sys
import numpy as np
from PIL import Image


def blocks(path, scale, y0, y1, x0, x1, thr, gap):
    im = Image.open(path).convert('RGB')
    if scale != 1:
        im = im.resize((round(im.width / scale), round(im.height / scale)), Image.LANCZOS)
    a = np.asarray(im).astype(int)[max(0, y0):y1, x0:x1]
    bg = np.median(a, axis=1, keepdims=True)
    ink = (np.abs(a - bg).sum(2) > thr).sum(1) > 1
    out, y = [], 0
    while y < len(ink):
        if ink[y]:
            s = y
            while y < len(ink) and ink[y:y + gap].any():
                y += 1
            out.append((s + y0, y + y0 - 1))
        y += 1
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('design'); ap.add_argument('render')
    ap.add_argument('--box', nargs=4, type=int, required=True, metavar=('Y0', 'Y1', 'X0', 'X1'))
    ap.add_argument('--dscale', type=float, default=1); ap.add_argument('--rscale', type=float, default=1)
    ap.add_argument('--roff', type=int, default=0); ap.add_argument('--thr', type=int, default=120)
    ap.add_argument('--gap', type=int, default=4); ap.add_argument('--tol', type=float, default=1)
    ap.add_argument('--hdiff', type=int, default=3)
    a = ap.parse_args()
    y0, y1, x0, x1 = a.box
    D = blocks(a.design, a.dscale, y0, y1, x0, x1, a.thr, a.gap)
    R = blocks(a.render, a.rscale, y0 + a.roff, y1 + a.roff, x0, x1, a.thr, a.gap)
    print(f"design {len(D)} khối, render {len(R)} khối" + ("  ⚠ số khối khác nhau: thu hẹp --box / chỉnh --gap --thr" if len(D) != len(R) else ''))
    print(f"{'design':>13} {'h':>4} {'gap':>4} | {'render':>13} {'h':>4} {'gap':>4} | {'dTop':>5} {'Δloc':>5}")
    bad = 0; last = None; base = None
    for i in range(max(len(D), len(R))):
        d = D[i] if i < len(D) else None; r = R[i] if i < len(R) else None
        gd = d[0] - D[i - 1][1] - 1 if d and i else None
        gr = r[0] - R[i - 1][1] - 1 if r and i else None
        dt = r[0] - a.roff - d[0] if d and r else None
        hd = (r[1] - r[0]) - (d[1] - d[0]) if d and r else None
        note, loc = '', None
        if dt is not None and abs(hd) > a.hdiff:
            note = f'  ? cao khác {hd:+d}px (dính hình khác / xuống dòng khác) — bỏ qua'
        elif dt is not None:
            loc = dt - last if last is not None else 0
            last = dt
            base = dt if base is None else base
            # 両方を満たす場合のみ: 直前ブロックからのジャンプ かつ 範囲先頭ブロックからのズレ（丸めによる ±1 の誤検知を防ぐ）
            if abs(loc) > a.tol and abs(dt - base) > a.tol:
                bad += 1; note = '  <== margin/padding ngay trên khối này'
        f = lambda b: f"{b[0]:6}-{b[1]:<6}" if b else ' ' * 13
        print(f"{f(d)} {(d[1]-d[0]+1) if d else '':>4} {gd if gd is not None else '':>4} | {f(r)} {(r[1]-r[0]+1) if r else '':>4} "
              f"{gr if gr is not None else '':>4} | {dt if dt is not None else '':>5} {loc if loc is not None else '':>5}" + note)
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
