#!/usr/bin/env python3
"""CSS px 座標でデザインからプレースホルダー画像を切り出す（比較時にレンダリングがデザインと同じ見た目になるように）。
JSON ファイルからリストを読む: [{"src": "pc", "box": [x0,y0,x1,y1], "out": "page/top/story.jpg"}, ...]

  python3 crop_assets.py --pc design_pc.png --sp design_sp.png --scale 2 --root user/media/THEME/ crops.json
"""
import argparse, json, os
from PIL import Image
ap = argparse.ArgumentParser()
ap.add_argument('spec'); ap.add_argument('--pc'); ap.add_argument('--sp')
ap.add_argument('--scale', type=float, default=2); ap.add_argument('--root', default='.')
a = ap.parse_args()
src = {k: Image.open(v).convert('RGB') for k, v in (('pc', a.pc), ('sp', a.sp)) if v}
for it in json.load(open(a.spec)):
    x0, y0, x1, y1 = [round(v * a.scale) for v in it['box']]
    p = os.path.join(a.root, it['out']); os.makedirs(os.path.dirname(p) or '.', exist_ok=True)
    r = src[it.get('src', 'pc')].crop((x0, y0, x1, y1))
    r.save(p, quality=88) if p.lower().endswith(('.jpg', '.jpeg')) else r.save(p)
    print(p, r.size)
