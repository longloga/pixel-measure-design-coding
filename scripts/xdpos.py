#!/usr/bin/env python3
"""So VỊ TRÍ dọc từng khối + từng đoạn chữ trên trang đã code với spec từ xdspec.py / figspec.py.

xdcmp.py chỉ so style chữ (size/weight/ls/lh/màu) — margin/padding sai vẫn lọt (L-MEAS-15). Script này ghép:
  - shape (rect) XD ↔ phần tử DOM cùng x / w / h (±3px)  → dy của khung (card, nút, section có nền...)
  - đoạn chữ XD ↔ text node cùng nội dung                 → dy của tâm dòng đầu
    (tâm XD = y + size/2 vì y của chữ XD là mép trên em-box; tâm DOM = tâm rect dòng đầu)
rồi sắp theo y design và in:
  dy    lệch tuyệt đối (render − design)
  Δloc  dy của mục này − dy của mục CÙNG LOẠI ngay trước (chữ↔chữ, khung↔khung) → lỗi phát sinh NGAY giữa
        2 mục: margin / padding / line-height của khối đó sai. Sửa từ Δloc đầu tiên vượt ngưỡng trở xuống.
  Tâm chữ DOM lệch tâm em-box XD theo metric font (≈ ±2px, Shippori 50px ≈ -4px) → chữ đổi font/cỡ có thể
  báo Δloc giả ±2〜4px: XÁC NHẬN bằng inkcmp.py trên ảnh design trước khi sửa (L-MEAS-15).

  python3 xdpos.py http://localhost:8765/index.html spec.json --ab "TOP_PC" --vp 1280x740
  python3 xdpos.py URL spec.json --ab "TOP_SP" --vp 375x740 --mobile --from 1800 --to 4000 --all
  python3 xdpos.py URL spec.json --ab "TOP_PC" --json out.json --tol 1

Mặc định (--tol 2) chỉ in mục có |Δloc| > tol (kèm 1 dòng ngữ cảnh trước). --all in mọi mục. Đặt --vp cao bằng KV của
design (L-SHOT-10). Mục có |dy| > --max (mặc định 60) bị coi là ghép nhầm và bỏ qua (in ở cuối).
Exit 1 nếu còn |Δloc| > tol.
"""
import argparse, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright
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

TEXT_JS = """(items)=>{
 const norm=s=>s.replace(/\\s+/g,'');
 const nodes=[]; const w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
 while(w.nextNode()){const t=w.currentNode,el=t.parentElement; if(!el)continue; const tx=norm(t.data); if(!tx)continue;
   const c=getComputedStyle(el); if(c.display=='none'||c.visibility=='hidden')continue;
   const rg=document.createRange(); rg.selectNodeContents(t); const rs=rg.getClientRects(); if(!rs.length||!rs[0].width)continue;
   nodes.push({tx,top:rs[0].top+scrollY,h:rs[0].height,left:rs[0].left,
     tag:el.tagName.toLowerCase()+(typeof el.className=='string'&&el.className?'.'+el.className.trim().split(/\\s+/)[0]:'')});}
 return items.map(([needle,X,Y])=>{const n=norm(needle); const key=n.slice(0,Math.min(6,n.length)); let best=null,bd=1e9;
   for(const o of nodes){ if(!(o.tx.includes(key)||(o.tx.length>=2&&n.startsWith(o.tx))))continue;
     const d=Math.abs(o.top-Y)+Math.abs(o.left-X)*0.5; if(d<bd){bd=d;best=o}}
   return best?{c:best.top+best.h/2,tag:best.tag}:null});}"""

RECT_JS = """(S)=>{const R=[];for(const e of document.querySelectorAll('body *')){const c=getComputedStyle(e);
  if(c.display=='none'||c.visibility=='hidden')continue; const r=e.getBoundingClientRect(); if(!r.width||!r.height)continue;
  R.push({x:r.left,y:r.top+scrollY,w:r.width,h:r.height,
    tag:e.tagName.toLowerCase()+(typeof e.className=='string'&&e.className.trim()?'.'+e.className.trim().split(/\\s+/).slice(0,2).join('.'):'')});}
 return S.map(s=>{let best=null,bd=1e9;for(const r of R){if(Math.abs(r.x-s.x)>3||Math.abs(r.w-s.w)>3||Math.abs(r.h-s.h)>4)continue;
   const d=Math.abs(r.y-s.y); if(d<bd){bd=d;best=r}} return best});}"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('url'); ap.add_argument('spec'); ap.add_argument('--ab', required=True)
    ap.add_argument('--vp', default='1280x740'); ap.add_argument('--mobile', action='store_true')
    ap.add_argument('--prep', default=''); ap.add_argument('--settle', type=int, default=2000)
    ap.add_argument('--from', dest='y0', type=float, default=-1e9); ap.add_argument('--to', dest='y1', type=float, default=1e9)
    ap.add_argument('--tol', type=float, default=2); ap.add_argument('--max', type=float, default=60)
    ap.add_argument('--all', action='store_true'); ap.add_argument('--json')
    ap.add_argument('--no-shapes', action='store_true'); ap.add_argument('--no-texts', action='store_true')
    a = ap.parse_args()
    spec = json.load(open(a.spec))
    W, H = map(int, a.vp.split('x'))
    inr = lambda y: a.y0 <= y <= a.y1
    texts = [] if a.no_texts else [t for t in spec['texts'] if t['ab'] == a.ab and len(t['text'].strip()) >= 2
                                   and t.get('size') and inr(t['y'])]
    shapes = [] if a.no_shapes else [s for s in spec['shapes'] if s['ab'] == a.ab and s.get('kind') == 'rect'
                                     and s.get('w', 0) >= 40 and s.get('h', 0) >= 16 and s['w'] < W + 20 and inr(s['y'])]
    with sync_playwright() as p:
        b = launch(p); pg = b.new_page(viewport={'width': W, 'height': H}, is_mobile=a.mobile, has_touch=a.mobile)
        note = open_page(pg, a.url, a.settle)
        if note: print('!', note)
        pg.evaluate(PREP_JS)
        if a.prep: pg.evaluate('()=>{' + a.prep + '}'); pg.wait_for_timeout(600)
        tr = pg.evaluate(TEXT_JS, [[t['text'], t['x'], t['y']] for t in texts])
        sr = pg.evaluate(RECT_JS, [{'x': s['x'], 'y': s['y'], 'w': s['w'], 'h': s['h']} for s in shapes])
        b.close()
    items, wrong = [], []
    seen = set()
    for t, r in zip(texts, tr):
        if not r: continue
        dy = r['c'] - (t['y'] + t['size'] / 2)
        it = dict(kind='T', y=t['y'], x=t['x'], dy=dy, el=r['tag'], name=t['text'].strip()[:22])
        (wrong if abs(dy) > a.max else items).append(it)
    for s, r in zip(shapes, sr):
        if not r: continue
        k = (round(r['y']), r['tag'])
        if k in seen: continue
        seen.add(k)
        dy = r['y'] - s['y']
        it = dict(kind='B', y=s['y'], x=s['x'], dy=dy, dh=r['h'] - s['h'], el=r['tag'], name=f"{s['w']}x{s['h']} {s.get('name') or ''}"[:22])
        (wrong if abs(dy) > a.max else items).append(it)
    items.sort(key=lambda i: (i['y'], i['x']))
    # Δloc so với mục TRƯỚC CÙNG LOẠI (chữ↔chữ, khung↔khung): tâm chữ DOM lệch tâm em-box XD một lượng phụ
    # thuộc metric font (Shippori 50px ≈ -4px), trộn 2 loại sẽ báo nhiễu ±2〜5px ở mọi chỗ chuyển loại.
    prev = {}; flagged = 0
    for it in items:
        p_ = prev.get(it['kind'])
        it['loc'] = 0 if p_ is None else it['dy'] - p_
        prev[it['kind']] = it['dy']
    out = []
    for i, it in enumerate(items):
        bad = abs(it['loc']) > a.tol + 0.5
        if bad: flagged += 1
        if a.all or bad:
            if not a.all and i and (not out or out[-1] is not items[i - 1]): out.append(items[i - 1])
            out.append(it)
    print(f"{a.ab}: {len(items)} mục (chữ {sum(i['kind']=='T' for i in items)}, khung {sum(i['kind']=='B' for i in items)}), "
          f"Δloc vượt ±{a.tol:g}px: {flagged}   [T=tâm dòng chữ, B=khung]")
    print(f"{'y':>6} {'x':>5} K {'dy':>5} {'Δloc':>5} {'dh':>4}  {'phần tử':26} XD")
    for it in out:
        mark = '  <==' if abs(it['loc']) > a.tol + 0.5 else ''
        dh = f"{it['dh']:+.0f}" if it.get('dh') is not None and abs(it.get('dh', 0)) >= 0.5 else ''
        print(f"{it['y']:6.0f} {it['x']:5.0f} {it['kind']} {it['dy']:+5.0f} {it['loc']:+5.0f} {dh:>4}  {it['el'][:26]:26} {it['name']}{mark}")
    if wrong:
        print(f"bỏ qua {len(wrong)} mục |dy|>{a.max:g} (ghép nhầm / khác chủ ý?):",
              ', '.join(f"{w['name'][:10]}@{w['y']:.0f}" for w in wrong[:12]))
    if a.json:
        json.dump(dict(items=items, wrong=wrong, flagged=flagged), open(a.json, 'w'), ensure_ascii=False, indent=1)
    sys.exit(1 if flagged else 0)


if __name__ == '__main__':
    main()
