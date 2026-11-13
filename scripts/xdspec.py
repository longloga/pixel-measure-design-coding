#!/usr/bin/env python3
"""Adobe XD ファイル（.xd = JSON の zip）を読む → 全テキスト / shape の正確な spec。画像から計測する代わりに使う。

  python3 xdspec.py design.xd --out spec.json            # 全アートボードを抽出
  python3 xdspec.py design.xd --out spec.json --list     # アートボードの一覧のみ（名前、サイズ）
  python3 xdspec.py design.xd --summary                  # 文字色 / 背景 / 枠線 / グラデーション / エフェクトの一覧表

spec.json:
  artboards: {id: {name, x, y, w, h}}
  texts: [{ab, text, family, weight, size, ls(em), lh(px), color, x, y}]  ← y ≈ テキストを含む行のグリフ上端
  shapes: [{ab, name, kind(rect/line/path), x, y, w, h, fill, opacity, gop, group, z, stroke, sw, dash, r, blend, blur, shadow}]
    opacity = 実効 opacity（shape × すべての親 group）、gop = 親 group 由来の分、group = 直接の親 group 名、
    z = アートボード内の描画順（大きいほど後に描画 = 上に重なる）。
座標はアートボード基準（CSS px @1x）。
注意: マスク付き group 内の shape → 実際のサイズは切り取られている可能性がある（高さを信用する前に画像と照合する）。
一時ディレクトリに展開する。元ファイルは変更しない。
"""
import argparse, json, os, sys, tempfile, zipfile
from collections import Counter
W = {'Thin': 100, 'ExtraLight': 200, 'Light': 300, 'Regular': 400, 'Medium': 500, 'SemiBold': 600,
     'Bold': 700, 'ExtraBold': 800, 'Black': 900}

def hexv(v):
    if isinstance(v, int): return '#%06x' % (v & 0xffffff)
    if isinstance(v, dict): return '#%02x%02x%02x' % (v.get('r', 0), v.get('g', 0), v.get('b', 0))

def fill_of(f):
    if not f: return None
    t = f.get('type')
    if t == 'solid': return hexv(f['color'].get('value'))
    if t == 'gradient':
        g = f['gradient']; st = g.get('meta', {}).get('ux', {}).get('gradientResources', {}).get('stops', [])
        return 'grad(%s;%s)' % (','.join('%s@%.2f' % (hexv(s['color']['value']), s['color'].get('alpha', 1)) for s in st),
                                ','.join(str(round(g.get(k, 0), 2)) for k in ('x1', 'y1', 'x2', 'y2')))
    if t == 'pattern': return 'image'

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('xd'); ap.add_argument('--out'); ap.add_argument('--list', action='store_true')
    ap.add_argument('--summary', action='store_true'); a = ap.parse_args()
    tmp = tempfile.mkdtemp(prefix='xdspec_'); zipfile.ZipFile(a.xd).extractall(tmp)
    man = json.load(open(os.path.join(tmp, 'manifest')))
    abs_ = {}
    def mw(n):
        for c in n.get('children', []) or []:
            b = c.get('uxdesign#bounds')
            if b and c.get('path', '').startswith('artboard-'):
                abs_[c['path']] = dict(name=c.get('name'), x=b['x'], y=b['y'], w=b['width'], h=b['height'])
            mw(c)
    mw(man)
    if a.list:
        for k, v in abs_.items(): print(f"{v['name']:30s} {v['w']}x{v['h']}  ({k})")
        return
    texts, shapes = [], []
    for path, ab in abs_.items():
        g = json.load(open(os.path.join(tmp, 'artwork', path, 'graphics', 'graphicContent.agc')))
        ox, oy, name = ab['x'], ab['y'], ab['name']
        def walk(n, tx, ty, gop=1.0, gname=None):
            t = n.get('transform') or {}; x = tx + t.get('tx', 0); y = ty + t.get('ty', 0)
            st = n.get('style') or {}
            if n.get('type') == 'text':
                raw = n['text'].get('rawText', ''); rs = n.get('meta', {}).get('ux', {}).get('rangedStyles') or []
                lh = (st.get('textAttributes') or {}).get('lineHeight')
                lines = [l for p in n['text'].get('paragraphs', []) for l in p.get('lines', [])]
                pos = 0
                for r in rs:
                    seg = raw[pos:pos + r['length']]; ly = 0
                    for l in lines:
                        hit = [q for q in l if q['from'] <= pos < q['to'] + 1]
                        if hit: ly = hit[0]['y']; break
                    pos += r['length']; s2 = seg.replace('\n', '').strip()
                    if s2 and not ('' <= s2[0] <= ''):
                        texts.append(dict(ab=name, text=s2, family=r.get('fontFamily'), weight=W.get(r.get('fontStyle'), r.get('fontStyle')),
                                          size=r.get('fontSize'), ls=round((r.get('charSpacing') or 0) / 1000, 3), lh=lh,
                                          color=hexv((r.get('fill') or {}).get('value')), x=round(x - ox), y=round(y - oy + ly - (r.get('fontSize') or 0) * 0.88)))
            if n.get('type') == 'shape':
                sh = n['shape']; k = sh.get('type'); s = st.get('stroke') or {}
                fx = {f['type']: f.get('params') for f in st.get('filters', []) if isinstance(f, dict)}
                blur = fx.get('uxdesign#blur'); shadow = fx.get('dropShadow')
                d = dict(ab=name, name=n.get('name'), kind=k, fill=fill_of(st.get('fill')), opacity=round(st.get('opacity', 1) * gop, 3),
                         gop=round(gop, 3), group=gname, z=len(shapes),
                         stroke=hexv(s['color']['value']) if s.get('type') == 'solid' else None, sw=s.get('width') if s.get('type') == 'solid' else None,
                         dash=s.get('dash'), blend=st.get('blendMode'),
                         blur=blur and dict(amount=blur.get('blurAmount'), fillOpacity=round(blur.get('fillOpacity', 1), 2), background=blur.get('backgroundEffect')),
                         shadow=shadow and [dict(dx=q['dx'], dy=q['dy'], r=q['r'], color=hexv(q['color']['value']), alpha=round(q['color'].get('alpha', 1), 2)) for q in shadow.get('dropShadows', [])])
                if k == 'rect':
                    d.update(x=round(x + sh.get('x', 0) - ox), y=round(y + sh.get('y', 0) - oy), w=round(sh.get('width', 0)), h=round(sh.get('height', 0)), r=sh.get('r'))
                elif k == 'line':
                    d.update(x=round(x + min(sh['x1'], sh['x2']) - ox), y=round(y + min(sh['y1'], sh['y2']) - oy), w=round(abs(sh['x2'] - sh['x1'])), h=round(abs(sh['y2'] - sh['y1'])))
                else:
                    d.update(x=round(x - ox), y=round(y - oy))
                shapes.append(d)
            # group/artboard の opacity を子 shape すべてに掛け合わせる（XD はグループ全体に opacity を適用するため）
            cg = gop * (st.get('opacity', 1) if n.get('type') != 'shape' else 1)
            cn = n.get('name') if n.get('type') == 'group' else gname
            for c in n.get('children', []) or []: walk(c, x, y, cg, cn)
            for kk in ('artboard', 'group'):
                if kk in n: walk(n[kk], x, y, cg, cn)
        walk(g, 0, 0)
    spec = dict(artboards={v['name']: v for v in abs_.values()}, texts=texts, shapes=shapes)
    if a.out: json.dump(spec, open(a.out, 'w'), ensure_ascii=False, indent=0); print('ghi', a.out, len(texts), 'text,', len(shapes), 'shape')
    if a.summary or not a.out:
        print('== Artboard'); [print(' ', k, f"{v['w']}x{v['h']}") for k, v in spec['artboards'].items()]
        print('== Màu chữ'); [print(' ', k, n) for k, n in Counter((t['ab'], t['color']) for t in texts).most_common()]
        print('== Font (family/weight/size/ls)'); [print(' ', k, n) for k, n in Counter((t['family'], t['weight'], t['size'], t['ls']) for t in texts).most_common(40)]
        fl = Counter((s['ab'], s['fill'], round(s['opacity'], 2)) for s in shapes if s['fill'] and s['kind'] == 'rect')
        print('== Nền (rect)'); [print(' ', k, n) for k, n in fl.most_common(40)]
        sk = Counter((s['ab'], s['stroke'], s['sw'], json.dumps(s['dash'])) for s in shapes if s['stroke'] and not (s['stroke'] == '#ffffff' and (s['sw'] or 0) < 1))
        print('== Viền / đường kẻ'); [print(' ', k, n) for k, n in sk.most_common(40)]
        print('== Hiệu ứng (blend / blur / shadow)')
        for s in shapes:
            if s['blend'] or s['blur'] or s['shadow']: print(' ', s['ab'], s['name'], s['x'], s['y'], s.get('w'), s.get('h'), s['fill'], s['blend'], s['blur'], s['shadow'])
        print('== Trang trí bán trong suốt (opacity hiệu dụng < 1, gồm opacity của group) — xem L-CSS-17')
        for s in shapes:
            if s['opacity'] < 0.99 and s['kind'] in ('rect', 'ellipse', 'circle', 'path') and (s.get('w') or 0) < 1200:
                print('  ', s['ab'], 'z=%d' % s['z'], s['name'], 'group=%s' % s['group'], 'gop=%s' % s['gop'], 'op=%s' % s['opacity'],
                      s['x'], s['y'], s.get('w'), s.get('h'), s['fill'])

if __name__ == '__main__':
    main()
