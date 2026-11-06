#!/usr/bin/env python3
"""So style chữ trên trang đã code với spec từ xdspec.py hoặc figspec.py (size / weight / letter-spacing / line-height / màu).

  python3 xdcmp.py http://localhost:8765/index.html spec.json --ab "TOP_PC" --vp 1280x740
  python3 xdcmp.py URL spec.json --ab "TOP_SP" --vp 375x740 --mobile --json out.json

Ghép từng đoạn chữ XD với text node trên trang có cùng nội dung (8 ký tự đầu), chọn node gần toạ độ XD nhất
(đặt --vp cao sao cho KV/khối đầu cao bằng design để toạ độ gần nhau). Bỏ qua lệch line-height khi tuỳ chọn
--lh-multiline (mặc định chỉ báo lh khi XD có lineHeight). Dòng "ghép nhầm" thường lệch size rất lớn — kiểm bằng mắt.
--prep "JS" chạy thêm trước khi đo (mở accordion, đóng modal...).
"""
import argparse, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright
from _page import launch, open_page

JS = """([needle,X,Y])=>{
 const norm=s=>s.replace(/\\s+/g,''); const n=norm(needle); const key=n.slice(0,Math.min(8,n.length));
 const w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT); let best=null,bd=1e9,bn=null;
 while(w.nextNode()){const t=w.currentNode,el=t.parentElement; if(!el)continue; const tx=norm(t.data); if(!tx)continue;
   if(!(tx.includes(key)||(tx.length>=2&&n.startsWith(tx))))continue;
   const rg=document.createRange(); rg.selectNodeContents(t); const r=rg.getBoundingClientRect(); if(!r.width)continue;
   const d=Math.abs(r.top+scrollY-Y)+Math.abs(r.left-X)*0.5; if(d<bd){bd=d;best=el;bn=r}}
 if(!best) return null; const c=getComputedStyle(best); const fs=parseFloat(c.fontSize);
 const rgb=(c.color.match(/\\d+/g)||[]).slice(0,3).map(v=>(+v).toString(16).padStart(2,'0')).join('');
 return {tag:best.tagName.toLowerCase()+(typeof best.className=='string'&&best.className?'.'+best.className.trim().split(/\\s+/)[0]:''),
   fs, fw:+c.fontWeight, ls:(c.letterSpacing=='normal'?0:parseFloat(c.letterSpacing))/fs,
   lh:c.lineHeight=='normal'?null:parseFloat(c.lineHeight), color:'#'+rgb, dist:Math.round(bd)}}"""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('url'); ap.add_argument('spec'); ap.add_argument('--ab', required=True)
    ap.add_argument('--vp', default='1280x740'); ap.add_argument('--mobile', action='store_true')
    ap.add_argument('--prep', default=''); ap.add_argument('--json'); ap.add_argument('--settle', type=int, default=2000)
    a = ap.parse_args()
    spec = json.load(open(a.spec)); segs = [t for t in spec['texts'] if t['ab'] == a.ab and len(t['text']) >= 2]
    w, h = map(int, a.vp.split('x'))
    rows, seen = [], set()
    with sync_playwright() as p:
        b = launch(p); pg = b.new_page(viewport={'width': w, 'height': h}, is_mobile=a.mobile, has_touch=a.mobile)
        open_page(pg, a.url, a.settle); pg.wait_for_timeout(1000)
        if a.prep: pg.evaluate('()=>{' + a.prep + '}'); pg.wait_for_timeout(600)
        for s in segs:
            k = (s['text'][:12], s['y'] // 200)
            if k in seen: continue
            seen.add(k); rows.append(dict(s, r=pg.evaluate(JS, [s['text'], s['x'], s['y']])))
        b.close()
    bad, miss = [], []
    for x in rows:
        r = x['r']
        if not r: miss.append(x); continue
        d = []
        if x['size'] and abs(r['fs'] - x['size']) >= 0.5: d.append(f"size {r['fs']:g}→{x['size']}")
        if isinstance(x['weight'], int) and r['fw'] != x['weight']: d.append(f"weight {r['fw']}→{x['weight']}")
        if abs(r['ls'] - x['ls']) > 0.011: d.append(f"ls {r['ls']:.2f}→{x['ls']:.2f}em")
        if x['lh'] and r['lh'] and abs(r['lh'] - x['lh']) > 1.5: d.append(f"lh {r['lh']:g}→{x['lh']}")
        if x['color'] and r['color'] != x['color']: d.append(f"color {r['color']}→{x['color']}")
        if d: bad.append(dict(y=x['y'], text=x['text'][:24], el=r['tag'], diff=', '.join(d)))
    print(f"{a.ab}: so sánh {len(rows)}, lệch {len(bad)}, không tìm thấy {len(miss)}  (giá trị: đang code→XD)")
    for b_ in sorted(bad, key=lambda z: z['y']): print(f"  y{b_['y']:>6} {b_['text']:26s} {b_['el']:22s} {b_['diff']}")
    if miss: print('  không tìm thấy:', ', '.join(m['text'][:14] for m in miss[:20]))
    if a.json: json.dump(dict(bad=bad, miss=[m['text'] for m in miss]), open(a.json, 'w'), ensure_ascii=False)

if __name__ == '__main__':
    main()
