#!/usr/bin/env python3
"""Cắt ảnh design dài thành các đoạn nhỏ để xem bằng Read (ảnh quá dài sẽ bị thu nhỏ không đọc được).

Ví dụ:
  python3 slice.py design_pc.png out/ --scale 2 --step 900        # PC 2x -> mỗi đoạn 900 CSS px
  python3 slice.py design_sp.png out/ --scale 2 --step 2000 --grid 3  # SP: ghép 3 cột cạnh nhau
Toạ độ y của đoạn thứ i = i*step (đơn vị CSS px), in ra để tra cứu.
"""
import argparse, os
from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument('image'); ap.add_argument('outdir')
ap.add_argument('--scale', type=float, default=2, help='device pixel ratio của ảnh (2 nếu ảnh @2x)')
ap.add_argument('--step', type=int, default=900, help='chiều cao mỗi đoạn, CSS px')
ap.add_argument('--grid', type=int, default=1, help='>1: ghép N đoạn liền nhau thành 1 ảnh ngang (hợp cho SP)')
a = ap.parse_args()
os.makedirs(a.outdir, exist_ok=True)
im = Image.open(a.image).convert('RGB')
W = round(im.width / a.scale); H = round(im.height / a.scale)
im = im.resize((W, H))
base = os.path.splitext(os.path.basename(a.image))[0]
strips = [(y, im.crop((0, y, W, min(H, y + a.step)))) for y in range(0, H, a.step)]
if a.grid == 1:
    for i, (y, s) in enumerate(strips):
        p = f'{a.outdir}/{base}_{i:02d}.png'; s.save(p); print(p, 'y=', y)
else:
    for g in range(0, len(strips), a.grid):
        grp = strips[g:g + a.grid]
        o = Image.new('RGB', (W * len(grp) + 20 * (len(grp) - 1), a.step), 'black')
        for j, (y, s) in enumerate(grp): o.paste(s, (j * (W + 20), 0))
        p = f'{a.outdir}/{base}_g{g // a.grid:02d}.png'; o.save(p)
        print(p, 'cột y=', [y for y, _ in grp])
print('CSS size:', W, 'x', H)
