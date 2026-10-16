#!/usr/bin/env python3
"""So sánh TỰ ĐỘNG design ↔ render theo từng dải ngang: tự dò offset dọc của mỗi dải (không cần nhập
--yd/--ym bằng tay như compare.py), in bảng độ lệch, và xuất ảnh heatmap chỉ chỗ khác.

Cách hiểu bảng:
  drift  = render đang lệch bao nhiêu px so với design tại dải này (cộng dồn từ trên xuống).
  Δ      = drift dải này - drift dải trước → chính là lỗi chiều cao CỤC BỘ, nằm ở giữa 2 dải.
           Sửa từ dải có |Δ| lớn nhất ở trên cùng trước — sửa nó sẽ kéo cả phần dưới về đúng.
  diff%  = % pixel còn khác (> --thr) sau khi đã căn offset → lỗi về kích thước/vị trí ngang/màu/font.
  dx     = lệch ngang tốt nhất của dải (≠0 → container/padding trái-phải sai).

  python3 pixeldiff.py design_pc.png shots/pc.png --dscale 2 --out diff_pc.png
  python3 pixeldiff.py design_sp.png shots/sp.png --dscale 2 --band 150 --out diff_sp.png --json m/pd_sp.json
  python3 pixeldiff.py design_pc.png shots/pc.png --dscale 2 --from 0 --to 1600   # chỉ 1 vùng

Tham số: --band chiều cao dải (CSS px, mặc định 200), --search phạm vi dò offset (mặc định ±200,
tăng lên nếu lệch nhiều), --mask vùng bỏ qua (ảnh placeholder khác, slider...) dạng x0 y0 x1 y1 theo design.
Dải gần như trơn (nền trắng) thì offset không xác định → đánh dấu '~' và lấy drift của dải trước.
"""
import argparse, json, os
import numpy as np
from PIL import Image, ImageDraw

ap = argparse.ArgumentParser()
ap.add_argument('design'); ap.add_argument('render')
ap.add_argument('--dscale', type=float, help='mặc định: tự suy ra = rộng design / rộng render'); ap.add_argument('--rscale', type=float, default=1)
ap.add_argument('--band', type=int, default=200); ap.add_argument('--search', type=int, default=200)
ap.add_argument('--xsearch', type=int, default=12)
ap.add_argument('--thr', type=int, default=40, help='ngưỡng khác biệt mỗi pixel (0-255, xám)')
ap.add_argument('--penalty', type=float, default=0.02, help='phạt mỗi px offset khi dò (ưu tiên offset nhỏ)')
ap.add_argument('--mismatch', type=float, default=35, help='diff%% vượt mức này = nội dung khác hẳn, không dùng offset')
ap.add_argument('--resync-max', type=float, default=15, help='diff%% tối đa để chấp nhận vị trí dò lại toàn trang')
ap.add_argument('--from', dest='y0', type=int, default=0); ap.add_argument('--to', dest='y1', type=int)
ap.add_argument('--mask', type=int, nargs=4, action='append', default=[], metavar=('X0', 'Y0', 'X1', 'Y1'))
ap.add_argument('--out', help='ảnh heatmap: design | render đã căn | vùng khác (đỏ)')
ap.add_argument('--json')
a = ap.parse_args()

R = Image.open(a.render).convert('L'); W = round(R.width / a.rscale)
R = np.asarray(R.resize((W, round(R.height / a.rscale))), dtype=np.int16)
Dimg = Image.open(a.design).convert('L')
if not a.dscale:
    a.dscale = Dimg.width / W; print(f'dscale tự nhận = {a.dscale:g} (design {Dimg.width}px / render {W}px)')
D = np.asarray(Dimg.resize((W, round(Dimg.height / a.dscale * W / (Dimg.width / a.dscale)))), dtype=np.int16)
if abs(Dimg.width / a.dscale - W) > 2:
    print(f'! design rộng {Dimg.width / a.dscale:.0f}px, render {W}px — đã co design theo render, kiểm tra lại --dscale/viewport')
M = np.ones_like(D, dtype=bool)
for x0, y0, x1, y1 in a.mask: M[y0:y1, x0:x1] = False
y1 = min(a.y1 or D.shape[0], D.shape[0])

def cost(db, mb, ry, dx, st=1):
    if ry < 0 or ry + db.shape[0] * st > R.shape[0]: return None
    rb = R[ry:ry + db.shape[0] * st:st, ::st]
    if dx: rb = np.roll(rb, -dx, axis=1)
    return np.abs(db - rb)[mb].mean() if mb.any() else 0

def pct(db, mb, ry, dx):
    rb = R[ry:ry + db.shape[0]]
    if rb.shape[0] < db.shape[0]: return 100.0
    rb = np.roll(rb, -dx, axis=1)
    return float(((np.abs(db - rb) > a.thr) & mb).sum() / max(mb.sum(), 1) * 100)

def resync(db, mb, y):
    """Tìm vị trí khớp nhất của dải design trên toàn bộ render (thô bước 8, ảnh co 1/4, rồi tinh)."""
    small = [(cost(db[::4, ::4], mb[::4, ::4], ry, 0, 4), ry) for ry in range(0, R.shape[0] - db.shape[0], 8)]
    small = sorted(c for c in small if c[0] is not None)[:5]
    best = None
    for _, ry in small:
        _, k = min(((cost(db, mb, ry + k, 0) or 1e9, k) for k in range(-8, 9)))
        _, dx = min(((cost(db, mb, ry + k, j) or 1e9, j) for j in range(-a.xsearch, a.xsearch + 1)))
        d = pct(db, mb, ry + k, dx)
        if best is None or d < best[2]: best = (ry + k - y, dx, d)
    return best

rows, prev, drift = [], 0, 0
for y in range(a.y0, y1, a.band):
    h = min(a.band, y1 - y); db = D[y:y + h]; mb = M[y:y + h]
    flat = db[mb].std() < 3 if mb.any() else True
    if flat:
        rows.append({'y': y, 'h': h, 'drift': drift, 'delta': 0, 'dx': 0, 'diff': None, 'flat': True}); continue
    # dò thô (bước 4px, quanh drift hiện tại) rồi dò tinh ±4
    cands = [(cost(db[::2, ::2], mb[::2, ::2], y + drift + o, 0, 2), o) for o in range(-a.search, a.search + 1, 4)]
    cands = [c for c in cands if c[0] is not None]
    if not cands: break
    # ưu tiên giữ offset cũ: chỉ đổi khi tốt hơn rõ rệt (tránh khớp nhầm vào nội dung lặp/khác hẳn)
    c0 = cost(db[::2, ::2], mb[::2, ::2], y + drift, 0, 2)
    cbest, o = min((c + a.penalty * abs(k), k) for c, k in cands)
    if c0 is not None and not (cbest < c0 * 0.8): o = 0
    o = min(((cost(db, mb, y + drift + k, 0) or 1e9, k) for k in range(o - 4, o + 5)))[1]
    off = drift + o
    _, dx = min(((cost(db, mb, y + off, k) or 1e9, k) for k in range(-a.xsearch, a.xsearch + 1)))
    diff = pct(db, mb, y + off, dx)
    if diff > a.mismatch or abs(o) >= a.search - 4:
        # mất dấu: render có khối dài/ngắn hơn design (> --search) -> dò lại trên TOÀN trang render
        g = resync(db, mb, y)
        # xác nhận: diff tốt hơn rõ rệt VÀ dải kế tiếp (có nội dung) cũng khớp ở cùng offset — tránh khớp nhầm
        # vào khối trông giống (card, nút lặp lại)
        ok = g is not None and g[2] < min(a.mismatch, a.resync_max) and g[2] < diff * 0.6
        if ok:
            ny = y + h
            while ny < y1 and D[ny:ny + a.band][M[ny:ny + a.band]].std() < 3: ny += a.band
            if ny < y1:
                nb = D[ny:ny + a.band]; nm = M[ny:ny + a.band]
                ok = pct(nb, nm, ny + g[0], g[1]) < a.resync_max and pct(nb, nm, ny + g[0], g[1]) < pct(nb, nm, ny + drift, 0)
        if ok:
            off, dx, diff = g
            rows.append({'y': y, 'h': h, 'drift': off, 'delta': 0, 'jump': off - drift, 'dx': dx, 'diff': round(diff, 2), 'flat': False})
            drift = off; continue
    if diff > a.mismatch:  # nội dung khác hẳn (ảnh placeholder khác, chưa code, slider...) -> không tin offset
        rows.append({'y': y, 'h': h, 'drift': drift, 'delta': 0, 'dx': 0, 'diff': round(diff, 2), 'flat': False, 'mismatch': True}); continue
    rows.append({'y': y, 'h': h, 'drift': off, 'delta': off - drift, 'dx': dx, 'diff': round(diff, 2), 'flat': False})
    drift = off

print(f'{"design y":>9} {"render y":>9} {"drift":>6} {"Δ":>5} {"dx":>4} {"diff%":>6}')
for r in rows:
    flag = '  <-- lỗi chiều cao ở trên dải này' if abs(r['delta']) > 3 else ''
    if r['dx'] and abs(r['dx']) > 2: flag += f'  <-- lệch ngang {r["dx"]}px'
    if r.get('jump'): flag = f'  <-- DÒ LẠI: phía trên có khối render {"dài" if r["jump"] > 0 else "ngắn"} hơn design {abs(r["jump"])}px (thêm/thiếu khối, hoặc chủ ý như tab cuộn)'
    if r.get('mismatch'): flag = '  <-- NỘI DUNG KHÁC HẲN (thiếu khối / ảnh khác / animation chưa chạy?) — xem heatmap'
    elif r['diff'] is not None and r['diff'] > 8: flag += '  <-- khác nhiều'
    print(f'{r["y"]:>9} {r["y"] + r["drift"]:>9} {r["drift"]:>6} {("~" if r["flat"] else r["delta"]):>5} {r["dx"]:>4} '
          f'{("-" if r["diff"] is None else "%.1f" % r["diff"]):>6}{flag}')
real = [r for r in rows if not r['flat'] and not r.get('mismatch')]
summary = {
    'render_height': int(R.shape[0]), 'design_height': int(D.shape[0]),
    'height_diff': int(R.shape[0] - D.shape[0]),
    'max_abs_delta': max((abs(r['delta']) for r in real), default=0),
    'bands_bad': sum(1 for r in real if abs(r['delta']) > 3 or (r['diff'] or 0) > 8),
    'resyncs': [r['jump'] for r in rows if r.get('jump')],
    'bands_mismatch': sum(1 for r in rows if r.get('mismatch')),
    'mean_diff_pct': round(float(np.mean([r['diff'] for r in real])), 2) if real else 0,
    'final_drift': rows[-1]['drift'] if rows else 0,
}
print('\nTÓM TẮT:', ', '.join(f'{k}={v}' for k, v in summary.items()))
print('Đạt khi: max_abs_delta ≤ 3, final_drift ≤ 5, mean_diff_pct thấp và không tăng giữa các vòng.')

if a.out:
    Hs = y1 - a.y0; out = Image.new('RGB', (W * 3 + 24, Hs), 'black')
    dimg = Image.fromarray(D[a.y0:y1].astype(np.uint8)).convert('RGB')
    al = np.full((Hs, W), 255, dtype=np.int16); heat = np.zeros((Hs, W, 3), dtype=np.uint8)
    for r in rows:
        s, e = r['y'] - a.y0, r['y'] - a.y0 + r['h']; ry = r['y'] + r['drift']
        seg = R[max(ry, 0):ry + r['h']]
        if seg.shape[0] < r['h']: continue
        seg = np.roll(seg, -r['dx'], axis=1); al[s:e] = seg
        d = (np.abs(D[r['y']:r['y'] + r['h']] - seg) > a.thr) & M[r['y']:r['y'] + r['h']]
        base = (D[r['y']:r['y'] + r['h']] * 0.35 + 140).astype(np.uint8)
        heat[s:e] = np.stack([base] * 3, -1); heat[s:e][d] = (230, 30, 30)
    out.paste(dimg, (0, 0)); out.paste(Image.fromarray(al.astype(np.uint8)).convert('RGB'), (W + 12, 0))
    out.paste(Image.fromarray(heat), (W * 2 + 24, 0))
    dr = ImageDraw.Draw(out)
    for r in rows:
        if abs(r['delta']) > 3 or r.get('jump'): dr.line([(0, r['y'] - a.y0), (out.width, r['y'] - a.y0)], fill=(255, 0, 255), width=2)
    z = min(1, 6000 / Hs); out = out.resize((int(out.width * z), int(Hs * z))) if z < 1 else out
    out.save(a.out); print('heatmap:', a.out, out.size, '(trái design | giữa render đã căn | phải chỗ khác màu đỏ, vạch tím = lỗi chiều cao)')
if a.json:
    os.makedirs(os.path.dirname(os.path.abspath(a.json)), exist_ok=True)
    json.dump({'summary': summary, 'rows': rows}, open(a.json, 'w'), ensure_ascii=False, indent=1)
