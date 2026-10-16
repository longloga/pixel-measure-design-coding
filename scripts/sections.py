#!/usr/bin/env python3
"""Quét dọc mép trái & phải trang để tìm ranh giới các section (đổi màu nền / gradient).
Dùng cho cả ảnh design lẫn ảnh render để so chiều cao từng section.

  python3 sections.py design_pc.png --scale 2
  python3 sections.py render_pc.png --scale 1
"""
import argparse
from PIL import Image
ap = argparse.ArgumentParser()
ap.add_argument('image'); ap.add_argument('--scale', type=float, default=1)
ap.add_argument('--inset', type=int, default=4, help='khoảng cách cột quét tính từ mép, CSS px')
ap.add_argument('--thr', type=int, default=6)
a = ap.parse_args()
im = Image.open(a.image).convert('RGB'); s = a.scale
W = im.width; H = int(im.height / s)
xl = int(a.inset * s); xr = W - 1 - int(a.inset * s)
prev = None; rows = []
for y in range(H):
    c = im.getpixel((xl, int(y * s))) + im.getpixel((xr, int(y * s)))
    if prev is None or max(abs(i - j) for i, j in zip(c, prev)) > a.thr:
        rows.append(y); print(y, '#%02x%02x%02x' % c[:3], '#%02x%02x%02x' % c[3:]); prev = c
print('height', H)
