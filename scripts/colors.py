#!/usr/bin/env python3
"""Lấy mẫu màu tại điểm, hoặc màu tối nhất trong vùng (màu chữ thật, tránh viền anti-alias).

  python3 colors.py design.png --scale 2 --pt btn 1150 40 --pt bg 5 1700
  python3 colors.py design.png --scale 2 --dark h2 180 1068 400 1104
"""
import argparse
from PIL import Image
ap = argparse.ArgumentParser()
ap.add_argument('image'); ap.add_argument('--scale', type=float, default=1)
ap.add_argument('--pt', nargs=3, action='append', default=[], metavar=('NAME', 'X', 'Y'))
ap.add_argument('--dark', nargs=5, action='append', default=[], metavar=('NAME', 'X0', 'Y0', 'X1', 'Y1'))
a = ap.parse_args()
im = Image.open(a.image).convert('RGB'); s = a.scale
hx = lambda c: '#%02x%02x%02x' % c
for n, x, y in a.pt: print(n, hx(im.getpixel((int(float(x) * s), int(float(y) * s)))))
for n, *b in a.dark:
    x0, y0, x1, y1 = [int(float(v) * s) for v in b]
    print(n, hx(min((im.getpixel((x, y)) for x in range(x0, x1) for y in range(y0, y1)), key=sum)))
