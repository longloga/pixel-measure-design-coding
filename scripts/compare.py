#!/usr/bin/env python3
"""Ghép design (trái) và render (phải) cạnh nhau cho một đoạn, để xem bằng Read.
Mỗi bên có offset y riêng vì section có thể lệch (hoặc section bị bỏ qua).

  python3 compare.py design_pc.png shots/pc.png --dscale 2 --yd 1616 --ym 1613 --h 1100 --out c.png --zoom 0.5
Nhiều đoạn (hợp cho SP): --pair yd ym h lặp lại, các đoạn được xếp ngang.
"""
import argparse
from PIL import Image
ap = argparse.ArgumentParser()
ap.add_argument('design'); ap.add_argument('render')
ap.add_argument('--dscale', type=float, default=2); ap.add_argument('--rscale', type=float, default=1)
ap.add_argument('--yd', type=int); ap.add_argument('--ym', type=int); ap.add_argument('--h', type=int)
ap.add_argument('--pair', nargs=3, type=int, action='append', default=[], metavar=('YD', 'YM', 'H'))
ap.add_argument('--out', default='compare.png'); ap.add_argument('--zoom', type=float, default=1)
a = ap.parse_args()
D = Image.open(a.design).convert('RGB'); R = Image.open(a.render).convert('RGB')
W = round(R.width / a.rscale)
pairs = a.pair or [(a.yd, a.ym, a.h)]
tiles = []
for yd, ym, h in pairs:
    d = D.crop((0, int(yd * a.dscale), D.width, int((yd + h) * a.dscale))).resize((W, h))
    m = R.crop((0, int(ym * a.rscale), R.width, int((ym + h) * a.rscale))).resize((W, h))
    t = Image.new('RGB', (W * 2 + 12, h), 'red'); t.paste(d, (0, 0)); t.paste(m, (W + 12, 0)); tiles.append(t)
o = Image.new('RGB', (sum(t.width for t in tiles) + 24 * (len(tiles) - 1), max(t.height for t in tiles)), 'black')
x = 0
for t in tiles: o.paste(t, (x, 0)); x += t.width + 24
if a.zoom != 1: o = o.resize((int(o.width * a.zoom), int(o.height * a.zoom)))
o.save(a.out); print(a.out, o.size)
