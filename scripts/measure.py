#!/usr/bin/env python3
"""Đo các "dòng mực" (text/ảnh/box) trong một vùng: in y bắt đầu-kết thúc, chiều cao, x trái-phải.
Pixel được coi là mực nếu khác màu nền (lấy tại cột x0 cùng hàng) quá ngưỡng thr.

  python3 measure.py design.png --scale 2 --box 90 790 1300 1530 --thr 20
Mẹo:
- Nền gradient ngang: dùng thr ~20 (gradient chỉ lệch ~11), chữ nhạt trên nền (#F2F0F4/#fff) vẫn bắt được.
- Chỉ muốn đo chữ đậm: thr 40-60. Muốn tách chữ EN lớn khỏi dòng sub: thu hẹp x.
- Suy ra: font-size ≈ chiều cao nét kanji / 0.92; line-height = khoảng cách y giữa 2 dòng;
  letter-spacing ≈ (độ rộng dòng / số ký tự) - font-size.
"""
import argparse
from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument('image'); ap.add_argument('--scale', type=float, default=1)
ap.add_argument('--box', type=float, nargs=4, required=True, metavar=('X0', 'Y0', 'X1', 'Y1'), help='CSS px')
ap.add_argument('--thr', type=int, default=30)
ap.add_argument('--cols', action='store_true', help='đo theo cột thay vì hàng (tìm các khối ngang)')
a = ap.parse_args()
im = Image.open(a.image).convert('RGB'); px = im.load(); s = a.scale
x0, y0, x1, y1 = [int(v * s) for v in a.box]
diff = lambda p, q: sum(abs(i - j) for i, j in zip(p, q))
if not a.cols:
    grp = None
    def out(g): print('rows %.1f-%.1f (h %.1f)  x %.1f-%.1f' % (g[0] / s, g[1] / s, (g[1] - g[0] + 1) / s, g[2] / s, g[3] / s))
    for y in range(y0, y1):
        bg = px[x0, y]
        xs = [x for x in range(x0, x1) if diff(px[x, y], bg) > a.thr]
        if xs:
            grp = [y, y, min(xs), max(xs)] if grp is None else [grp[0], y, min(grp[2], min(xs)), max(grp[3], max(xs))]
        elif grp: out(grp); grp = None
    if grp: out(grp)
else:
    grp = None
    for x in range(x0, x1):
        bg = px[x, y0]
        ys = [y for y in range(y0, y1) if diff(px[x, y], bg) > a.thr]
        if ys:
            grp = [x, x] if grp is None else [grp[0], x]
        elif grp: print('cols %.1f-%.1f (w %.1f)' % (grp[0] / s, grp[1] / s, (grp[1] - grp[0] + 1) / s)); grp = None
    if grp: print('cols %.1f-%.1f (w %.1f)' % (grp[0] / s, grp[1] / s, (grp[1] - grp[0] + 1) / s))
