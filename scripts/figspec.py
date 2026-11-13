#!/usr/bin/env python3
"""Figma ファイルから正確な spec を取得（Figma MCP `use_figma` 経由）→ xdspec.py と同じ形式の spec.json。

get_design_context の数値を使わない理由: Figma は letter-spacing を % で保持する（6% = 0.06em）が、
get_design_context の参考コードは font-size を掛けた px で出力する（16px なら `tracking-[0.96px]`）→ 元の単位が失われ、
丸め誤差が出て、SP で font-size が変わると誤る（L-MEAS-14）。このスクリプトは各テキストの {unit, value} を直接読む。

  python3 figspec.py js 1:9 15:200            # JS を出力 → そのまま use_figma に貼り付け（大きい場合はフレームごとに 1 回）
  python3 figspec.py js 1:9 --only texts      # 大きいフレーム: 2 回に分けて呼ぶ（--only texts / --only shapes）
  python3 figspec.py save raw_pc.json raw_sp.json --out spec.json --summary
                                              # raw_*.json = use_figma の戻り値をそのまま保存したもの

spec.json（xdspec.py と同じ、xdcmp.py で使用可）:
  artboards: {name: {id, x, y, w, h}}
  texts: [{ab, id, text, family, weight, size, ls(em), ls_raw, lh(px|null), lh_raw, color, cop, x, y, case, deco}]
    ls = PERCENT/100 または PIXELS/size（em、小数 4 桁）— CSS: `letter-spacing: <ls>em`、px は使わない。
    ls_raw = Figma の元の値（"6%" / "1.2px"）、lh_raw = "AUTO" / "170%" / "28px"。
    lh = AUTO のとき null（Figma がフォントから自動計算 — 推測せずレンダリングで計測する）。
    color = 最上位 fill の hex、cop = fill の opacity（1 未満の場合）。
  shapes: [{ab, id, name, kind, x, y, w, h, fill, opacity, gop, group, z, stroke, sw, r, shadow, blur}]
座標はフレーム基準（CSS px @1x）。非表示ノード（とその子）は除外。
"""
import argparse, json, sys
from collections import Counter

JS = r"""const IDS = __IDS__;
const ONLY = __ONLY__;  // 'texts' | 'shapes' | null
const r2 = v => Math.round(v * 100) / 100, r4 = v => Math.round(v * 10000) / 10000;
const hex = c => '#' + [c.r, c.g, c.b].map(v => Math.round(v * 255).toString(16).padStart(2, '0')).join('');
const top = fs => Array.isArray(fs) ? fs.filter(f => f.visible !== false) : [];
const paint = fs => { const p = top(fs); if (!p.length) return null; const f = p[p.length - 1];
  if (f.type === 'SOLID') return hex(f.color);
  if (f.type.startsWith('GRADIENT')) return f.type.slice(9).toLowerCase() + '(' + f.gradientStops.map(s => hex(s.color) + '@' + r2(s.color.a) + ' ' + Math.round(s.position * 100) + '%').join(',') + ')';
  return f.type.toLowerCase(); };
const pop = fs => { const p = top(fs); const f = p[p.length - 1]; return f && f.opacity != null && f.opacity < 1 ? r2(f.opacity) : undefined; };
const lsEm = (l, fs) => l.unit === 'PERCENT' ? r4(l.value / 100) : r4(l.value / fs);
const lsRaw = l => l.unit === 'PERCENT' ? r2(l.value) + '%' : r2(l.value) + 'px';
const lhPx = (l, fs) => l.unit === 'PIXELS' ? r2(l.value) : l.unit === 'PERCENT' ? r2(fs * l.value / 100) : null;
const lhRaw = l => l.unit === 'AUTO' ? 'AUTO' : l.unit === 'PERCENT' ? r2(l.value) + '%' : r2(l.value) + 'px';
const out = { artboards: {}, texts: [], shapes: [] };
let z = 0;
for (const id of IDS) {
  const ab = await figma.getNodeByIdAsync(id);
  if (!ab) { out.artboards['?' + id] = { id, error: 'not found' }; continue; }
  const B = ab.absoluteBoundingBox; const name = ab.name;
  out.artboards[name] = { id, x: r2(B.x), y: r2(B.y), w: r2(B.width), h: r2(B.height) };
  const walk = (n, gop, gname) => {
    if (n.visible === false) return;
    z++;
    const b = n.absoluteBoundingBox; const op = 'opacity' in n ? n.opacity : 1;
    if (n.type === 'TEXT' && b) {
      if (ONLY === 'shapes') return;
      const segs = n.getStyledTextSegments(['fontName', 'fontWeight', 'fontSize', 'letterSpacing', 'lineHeight', 'fills', 'textCase', 'textDecoration']);
      for (const s of segs) {
        const t = s.characters.replace(/\s+/g, ' ').trim(); if (!t) continue;
        const lh = lhPx(s.lineHeight, s.fontSize);
        const row = { ab: name, id: n.id, text: t, family: s.fontName.family, weight: s.fontWeight, size: r2(s.fontSize),
          ls: lsEm(s.letterSpacing, s.fontSize), ls_raw: lsRaw(s.letterSpacing), lh, lh_raw: lhRaw(s.lineHeight),
          color: paint(s.fills), x: r2(b.x - B.x), y: r2(b.y - B.y + Math.max(0, ((lh || s.fontSize * 1.45) - s.fontSize) / 2)) };
        const cop = pop(s.fills); if (cop !== undefined) row.cop = cop;
        if (gop * op < 1) row.op = r2(gop * op);
        if (s.textCase !== 'ORIGINAL') row.case = s.textCase;
        if (s.textDecoration !== 'NONE') row.deco = s.textDecoration;
        out.texts.push(row);
      }
      return;
    }
    if (ONLY !== 'texts' && n !== ab && b && n.type !== 'GROUP' && n.type !== 'SECTION') {
      const fill = 'fills' in n ? paint(n.fills) : null; const stroke = 'strokes' in n ? paint(n.strokes) : null;
      const fx = 'effects' in n ? n.effects.filter(e => e.visible !== false) : [];
      if (fill || stroke || fx.length) {
        const d = { ab: name, id: n.id, name: n.name, kind: n.type.toLowerCase(), x: r2(b.x - B.x), y: r2(b.y - B.y), w: r2(b.width), h: r2(b.height),
          fill, opacity: r2(gop * op), gop: r2(gop), group: gname, z };
        if (stroke) { d.stroke = stroke; d.sw = typeof n.strokeWeight === 'number' ? n.strokeWeight : 'mixed'; d.salign = n.strokeAlign; if (n.dashPattern && n.dashPattern.length) d.dash = n.dashPattern; }
        if ('cornerRadius' in n) d.r = typeof n.cornerRadius === 'number' ? n.cornerRadius : [n.topLeftRadius, n.topRightRadius, n.bottomRightRadius, n.bottomLeftRadius];
        const fop = 'fills' in n ? pop(n.fills) : undefined; if (fop !== undefined) d.fop = fop;
        const sh = fx.filter(e => e.type === 'DROP_SHADOW' || e.type === 'INNER_SHADOW');
        if (sh.length) d.shadow = sh.map(e => ({ inset: e.type === 'INNER_SHADOW', dx: e.offset.x, dy: e.offset.y, r: e.radius, spread: e.spread || 0, color: hex(e.color), alpha: r2(e.color.a) }));
        const bl = fx.find(e => e.type === 'LAYER_BLUR' || e.type === 'BACKGROUND_BLUR'); if (bl) d.blur = { type: bl.type, r: bl.radius };
        if (n.blendMode && n.blendMode !== 'PASS_THROUGH' && n.blendMode !== 'NORMAL') d.blend = n.blendMode;
        out.shapes.push(d);
      }
    }
    if ('children' in n) for (const c of n.children) walk(c, n === ab ? 1 : gop * op, n === ab ? null : n.name);
  };
  walk(ab, 1, null);
}
out.bytes = JSON.stringify(out).length;
return out;"""


def cmd_js(a):
    ids = [i.replace('-', ':') for i in a.ids]
    print(JS.replace('__IDS__', json.dumps(ids)).replace('__ONLY__', json.dumps(a.only)))


def cmd_save(a):
    spec = dict(artboards={}, texts=[], shapes=[])
    for f in a.raw:
        d = json.load(open(f))
        if isinstance(d, dict) and 'result' in d and isinstance(d['result'], dict): d = d['result']
        for k in ('artboards', 'texts', 'shapes'):
            if k not in d: sys.exit(f'{f}: thiếu khoá "{k}" — đây có phải giá trị trả về của `figspec.py js` không?')
        spec['artboards'].update(d['artboards']); spec['texts'] += d['texts']; spec['shapes'] += d['shapes']
    bad = [k for k, v in spec['artboards'].items() if v.get('error')]
    if bad: print('!! frame không tìm thấy:', ', '.join(bad))
    if a.out:
        json.dump(spec, open(a.out, 'w'), ensure_ascii=False, indent=0)
        print('ghi', a.out, len(spec['texts']), 'text,', len(spec['shapes']), 'shape')
    if a.summary: summary(spec)


def summary(spec):
    T = spec['texts']
    print('== Frame'); [print(' ', k, f"{v.get('w')}x{v.get('h')}", v.get('id')) for k, v in spec['artboards'].items()]
    print('== Font (family / weight / size / letter-spacing → CSS / line-height)')
    for (fam, w, sz, ls, raw, lh), n in Counter((t['family'], t['weight'], t['size'], t['ls'], t['ls_raw'], t['lh_raw']) for t in T).most_common(50):
        css = '0' if not ls else f'{ls:g}em'
        print(f'  {n:>3}× {fam} {w} {sz:g}px  ls {raw:>7} → letter-spacing: {css:9s} lh {lh}')
    px = [t for t in T if t['ls_raw'].endswith('px') and t['ls']]
    if px: print(f'!! {len(px)} đoạn chữ đặt letter-spacing theo px trong Figma — đã đổi sang em theo font-size của đoạn đó; '
                  'nếu font-size đổi ở SP thì kiểm lại ý đồ (giữ px hay giữ tỉ lệ).')
    print('== Màu chữ'); [print(' ', k, n) for k, n in Counter((t['ab'], t['color'], t.get('cop')) for t in T).most_common(20)]
    S = spec['shapes']
    if S:
        print('== Nền (fill / opacity)'); [print(' ', k, n) for k, n in Counter((s['ab'], s['fill'], s['opacity']) for s in S if s['fill']).most_common(20)]
        print('== Viền'); [print(' ', k, n) for k, n in Counter((s['ab'], s.get('stroke'), s.get('sw'), s.get('salign')) for s in S if s.get('stroke')).most_common(15)]
        print('== Bo góc'); [print(' ', k, n) for k, n in Counter(json.dumps(s.get('r')) for s in S if s.get('r')).most_common(15)]
        fx = [s for s in S if s.get('shadow') or s.get('blur') or s.get('blend')]
        if fx: print('== Hiệu ứng'); [print(' ', s['ab'], s['name'], s['w'], s['h'], s.get('shadow'), s.get('blur'), s.get('blend')) for s in fx[:30]]


def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest='cmd', required=True)
    j = sub.add_parser('js', help='in JS cho use_figma'); j.add_argument('ids', nargs='+', help='node id frame (1:9 hoặc 1-9)')
    j.add_argument('--only', choices=['texts', 'shapes'], help='chỉ lấy chữ / chỉ lấy shape (frame lớn → return bị cắt)')
    s = sub.add_parser('save', help='gộp giá trị use_figma trả về → spec.json'); s.add_argument('raw', nargs='+')
    s.add_argument('--out'); s.add_argument('--summary', action='store_true')
    a = ap.parse_args(); (cmd_js if a.cmd == 'js' else cmd_save)(a)


if __name__ == '__main__':
    main()
