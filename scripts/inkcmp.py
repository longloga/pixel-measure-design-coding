#!/usr/bin/env python3
"""So từng DÒNG MỰC (khối chữ / ảnh / nút) trong 1 cột của ảnh design và ảnh render → khoảng cách dọc thật.

Dùng khi không có XD/Figma, hoặc để kiểm chứng xdpos.py trên chính ảnh design. Chỉ quét trong cột x0..x1
(chọn cột chỉ chứa khối cần đo, tránh ảnh/hình trang trí bên cạnh) nên thấy được margin GIỮA các dòng mà
pixeldiff dải lớn bỏ qua (L-SHOT-11).

  python3 inkcmp.py design.png render.png --box 2520 3020 100 560
  python3 inkcmp.py design@2x.png shots/pc.png --dscale 2 --box 2520 3020 100 560 --roff 6 --thr 150 --gap 3

--box Y0 Y1 X0 X1 : vùng theo CSS px của DESIGN; --roff N: render lệch sẵn N px (vd section phía trên đã lệch)
--thr  : ngưỡng khác màu so với màu nền (trung vị) của từng hàng (nền ảnh/gradient → tăng 150〜200)
--gap  : số hàng trống tối đa vẫn coi là cùng 1 khối (chữ nhiều dòng tách riêng → để 3〜4)
Cột: h (cao khối), gap (khoảng trắng tới khối trước), dTop (lệch mép trên),
     Δloc = dTop − dTop của khối hợp lệ trước = lượng margin/padding cần sửa NGAY TRÊN khối đó (so top→top nên
     không bị nhiễu khi chữ số/ảnh render cao thấp 1–2px). Khối cao khác > --hdiff px (dính hình trang trí,
     xuống dòng khác) bị đánh "?" và bỏ qua → thu hẹp --box nếu cần đo nó.
Exit 1 nếu có khối |Δloc| > --tol VÀ |dTop − dTop khối đầu| > --tol (mặc định 1).
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
            # cần cả 2: nhảy so với khối trước VÀ lệch so với khối đầu vùng (tránh báo giả khi +1/-1 do làm tròn)
            if abs(loc) > a.tol and abs(dt - base) > a.tol:
                bad += 1; note = '  <== margin/padding ngay trên khối này'
        f = lambda b: f"{b[0]:6}-{b[1]:<6}" if b else ' ' * 13
        print(f"{f(d)} {(d[1]-d[0]+1) if d else '':>4} {gd if gd is not None else '':>4} | {f(r)} {(r[1]-r[0]+1) if r else '':>4} "
              f"{gr if gr is not None else '':>4} | {dt if dt is not None else '':>5} {loc if loc is not None else '':>5}" + note)
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
