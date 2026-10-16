#!/usr/bin/env python3
"""Ước lượng border-radius tại góc một box: đi theo đường chéo từ góc vào đến khi gặp pixel khác nền.
r ≈ d / 0.2929. Nếu ảnh có nền trắng ngay tại góc thì kết quả sai (quá lớn) — bỏ qua góc đó.

  python3 radius.py design.png --scale 2 --corner TL 733 2010 --corner BR 1409.5 2617.5
"""
import argparse
from PIL import Image
ap = argparse.ArgumentParser()
ap.add_argument('image'); ap.add_argument('--scale', type=float, default=1)
ap.add_argument('--corner', nargs=3, action='append', required=True, metavar=('TL|TR|BL|BR', 'X', 'Y'))
ap.add_argument('--thr', type=int, default=25)
a = ap.parse_args()
im = Image.open(a.image).convert('RGB'); s = a.scale
D = {'TL': (1, 1), 'TR': (-1, 1), 'BL': (1, -1), 'BR': (-1, -1)}
for k, x, y in a.corner:
    x, y = float(x), float(y); dx, dy = D[k]
    bg = im.getpixel((int((x - dx * 3) * s), int((y - dy * 3) * s)))
    for i in range(120):
        p = im.getpixel((int((x + dx * i) * s), int((y + dy * i) * s)))
        if sum(abs(u - v) for u, v in zip(p, bg)) > a.thr:
            print(k, (x, y), 'd=', i, 'radius≈', round(i / 0.2929)); break
