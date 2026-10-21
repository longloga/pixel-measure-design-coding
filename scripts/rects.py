#!/usr/bin/env python3
"""So vị trí/kích thước từng khối (DOM getBoundingClientRect) với số đo design.

Dùng khi `pixeldiff` bị nhiễu bởi phần NGOÀI phạm vi sửa (header/KV/footer dùng chung khác design,
banner ngôn ngữ, cookie bar...): căn theo 1 khối mốc trong vùng mình code rồi so từng khối, nên lệch ở
header không lan xuống. Nhanh hơn chụp + pixeldiff (không chụp ảnh), chính xác tới px.

  python3 rects.py http://localhost:8765/page.html targets.json
  python3 rects.py URL targets.json --vp 375 --styles --json out/rects.json

targets.json — danh sách, y/h/x/w là số đo trên DESIGN (CSS px, lấy bằng measure.py), bỏ trống được:
  [{"name": "anchor", "sel": ".anchor-list li", "y": 1118, "h": 100},
   {"name": "h2-1",   "sel": "#link01 h2",       "y": 1498, "h": 86, "x": 220, "w": 1000},
   {"name": "intro",  "sel": ".intro"}]                       # không có y → chỉ in số đo render
  (cũng nhận dạng rút gọn [name, sel, y, h])

Khối mốc = khối đầu tiên có y (hoặc --anchor NAME). Cột:
  Δy    lệch so với design sau khi căn mốc (tích luỹ)
  Δloc  Δy của khối này trừ Δy của khối trước → lỗi phát sinh NGAY GIỮA 2 khối (sửa chỗ này trước)
  Δh/Δx/Δw  lệch kích thước / ngang
--styles in thêm font-size / weight / line-height / letter-spacing / màu của mỗi selector.
Exit 1 nếu có |Δloc| hoặc |Δh| > --tol (mặc định 3).
"""
import argparse, json, os, sys
from playwright.sync_api import sync_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _page import launch, open_page

PREP_JS = '''async () => {
  const st = document.createElement('style');
  st.textContent = '*,*::before,*::after{transition:none!important;animation:none!important}' +
                   '[data-aos]{opacity:1!important;transform:none!important}';
  document.head.appendChild(st);
  for (let y = 0; y < document.documentElement.scrollHeight; y += Math.round(innerHeight / 2)) {
    scrollTo(0, y); await new Promise(r => setTimeout(r, 40)); }
  scrollTo(0, 0); await document.fonts.ready;
}'''
RECT_JS = '''s => { const e = document.querySelector(s); if (!e) return null;
  const r = e.getBoundingClientRect(), c = getComputedStyle(e);
  return {x: r.left + scrollX, y: r.top + scrollY, w: r.width, h: r.height,
          st: [c.fontSize, c.fontWeight, c.lineHeight, c.letterSpacing, c.color, c.fontFamily.split(',')[0]]}; }'''


def norm(t):
    if isinstance(t, dict): return t
    flat = []
    for v in t: flat.extend(v if isinstance(v, list) else [v])   # nhận cả [name, sel, [y, h]]
    keys = ['name', 'sel', 'y', 'h', 'x', 'w']
    return {k: v for k, v in zip(keys, flat) if v is not None}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('url'); ap.add_argument('targets')
    ap.add_argument('--vp', type=int, default=1440)
    ap.add_argument('--anchor', help='tên khối mốc (mặc định: khối đầu tiên có y)')
    ap.add_argument('--styles', action='store_true')
    ap.add_argument('--tol', type=float, default=3)
    ap.add_argument('--wait', type=int, default=800)
    ap.add_argument('--settle', type=int, default=8000)
    ap.add_argument('--json')
    a = ap.parse_args()
    targets = [norm(t) for t in json.load(open(a.targets))]
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={'width': a.vp, 'height': 900})
        note = open_page(pg, a.url, a.settle)
        if note: print('(', note, ')')
        pg.evaluate(PREP_JS); pg.wait_for_timeout(a.wait)
        rows = [(t, pg.evaluate(RECT_JS, t['sel'])) for t in targets]
        b.close()
    anchor = next((t for t, r in rows if r and 'y' in t and (a.anchor is None or t['name'] == a.anchor)), None)
    base = 0
    if anchor:
        base = next(r for t, r in rows if t is anchor)['y'] - anchor['y']
    out, bad, prev = [], 0, None
    print(f"{'name':14s} {'render y':>9s} {'h':>6s} {'Δy':>5s} {'Δloc':>5s} {'Δh':>4s} {'Δx':>4s} {'Δw':>4s}")
    for t, r in rows:
        if r is None:
            print(f"{t['name']:14s} KHÔNG TÌM THẤY {t['sel']}"); bad += 1; continue
        y = r['y'] - base
        d = {'name': t['name'], 'y': round(y, 1), 'h': round(r['h'], 1), 'x': round(r['x'], 1), 'w': round(r['w'], 1)}
        for k in ('y', 'h', 'x', 'w'):
            if k in t: d['d' + k] = round((y if k == 'y' else r[k]) - t[k], 1)
        if 'dy' in d:
            d['dloc'] = round(d['dy'] - (prev if prev is not None else 0), 1); prev = d['dy']
        flag = any(abs(d.get(k, 0)) > a.tol for k in ('dloc', 'dh', 'dx', 'dw'))
        bad += flag
        f = lambda k: f"{d[k]:+5.0f}" if k in d else '    -'
        print(f"{t['name']:14s} {y:9.0f} {r['h']:6.0f} {f('dy')} {f('dloc')} {f('dh')[1:]} {f('dx')[1:]} {f('dw')[1:]}"
              + ('   <<' if flag else ''))
        if a.styles:
            fs, fw, lh, ls, col, fam = r['st']
            print(f"{'':14s}   {fs} / {fw} / lh {lh} / ls {ls} / {col} / {fam}")
            d['styles'] = r['st']
        out.append(d)
    dys = [d['dy'] for d in out if 'dy' in d]
    locs = [d['dloc'] for d in out if 'dloc' in d]
    summ = {'blocks': len(out), 'max_abs_local': max(map(abs, locs), default=0),
            'final_drift': dys[-1] if dys else 0, 'over_tol': bad}
    print(f"\nTÓM TẮT: max |Δloc|={summ['max_abs_local']:.0f}  drift cuối={summ['final_drift']:+.0f}  "
          f"khối vượt ±{a.tol:g}px: {bad}")
    if a.json:
        os.makedirs(os.path.dirname(os.path.abspath(a.json)), exist_ok=True)
        json.dump({'summary': summ, 'rows': out}, open(a.json, 'w'), ensure_ascii=False, indent=1)
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
