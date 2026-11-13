#!/usr/bin/env python3
"""L-FLOW-09: 補助画像（1 画面キャプチャ、追従、hover、アコーディオン展開時など）に「だけ」あり、メインデザインに無い内容を探す。

各補助画像について、メインデザイン画像内で最も一致する位置を探索し（行ごとのプロファイルを縮小して比較）、その位置で
ピクセル比較する: 「異なる」帯を出力し（「画面上端/下端」付き → たいてい固定バー / 追従）、main|ref を並べた画像を
--out に切り出して確認できるようにする。幅の異なる補助画像はメイン画像の幅に合わせて縮小する。

  python3 refcheck.py design_pc.png ref_scroll.png ref_hover.png --out $S/refcheck
  python3 refcheck.py design_sp.png sp_menu_open.png --thr 40 --min-band 12

各画像の結果: 一致位置（メインデザイン上の y）、一致度（%）、異なる帯の一覧。どこにも一致しない（一致度が低い）
画像 = 全く別の状態 / ページ（メニュー展開、モーダル）→ その状態を個別にコーディング・検証する。
異なる帯を含む補助画像があれば exit 1 → 画像分類表（SKILL.md ステップ 1）に記載して実装すること。
"""
import argparse, os, sys
import numpy as np
from PIL import Image


def load(p, width=None):
    im = Image.open(p).convert('RGB')
    if width and im.width != width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    return im


def best_offset(main, ref, f=4):
    """縦オフセットの探索: 縮小したプロファイル（幅 160、高さ /f）で比較。"""
    w = 160
    m = np.asarray(main.convert('L').resize((w, max(1, main.height // f)))).astype(np.float32)
    r = np.asarray(ref.convert('L').resize((w, max(1, ref.height // f)))).astype(np.float32)
    H, h = len(m), len(r)
    if h > H:
        return 0, 0.0
    best, bo = 1e9, 0
    for o in range(0, H - h + 1):
        d = np.abs(m[o:o + h] - r).mean()
        if d < best:
            best, bo = d, o
    return bo * f, best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('main'); ap.add_argument('refs', nargs='+')
    ap.add_argument('--out'); ap.add_argument('--thr', type=int, default=60, help='tổng |ΔRGB| coi là khác')
    ap.add_argument('--frac', type=float, default=0.02, help='tỉ lệ cột khác tối thiểu của 1 hàng')
    ap.add_argument('--min-band', type=int, default=8, help='dải khác cao tối thiểu (px)')
    a = ap.parse_args()
    M = load(a.main)
    if a.out: os.makedirs(a.out, exist_ok=True)
    found = 0
    for rp in a.refs:
        R = load(rp, M.width)
        off, score = best_offset(M, R)
        # フル解像度で ±6px の微調整
        mr = np.asarray(R).astype(int)
        cands = []
        for o in range(max(0, off - 6), min(M.height - R.height, off + 6) + 1):
            mm = np.asarray(M.crop((0, o, M.width, o + R.height))).astype(int)
            cands.append((np.abs(mm - mr).sum(2).mean(), o))
        if cands:
            _, off = min(cands)
        mm = np.asarray(M.crop((0, off, M.width, off + R.height))).astype(int)
        diff = np.abs(mm - mr).sum(2) > a.thr
        rows = diff.mean(1) > a.frac
        match = 100 * (1 - diff.mean())
        bands, y = [], 0
        while y < len(rows):
            if rows[y]:
                s = y
                while y < len(rows) and rows[y:y + 6].any(): y += 1
                if y - s >= a.min_band: bands.append((s, y))
            y += 1
        name = os.path.basename(rp)
        print(f"\n== {name}  {R.width}x{R.height}  khớp tại y={off} trên design chính, giống {match:.1f}%")
        if match < 70:
            print("   ⚠ gần như không khớp chỗ nào → trạng thái/trang KHÁC (menu mở, modal, trang con): code + chụp riêng trạng thái này")
        if not bands:
            print("   không có dải khác — ảnh này chỉ là ảnh cắt của design chính")
            continue
        found += 1
        for i, (s, e) in enumerate(bands):
            cols = np.where(diff[s:e].any(0))[0]
            edge = ''
            if s < R.height * 0.15: edge = '  ← MÉP TRÊN màn hình (header cố định / thanh khi cuộn?)'
            if e > R.height * 0.85: edge = '  ← MÉP DƯỚI màn hình (追従 / CTA cố định?)'
            print(f"   dải khác y{s}-{e} (cao {e - s}px, x {cols.min()}-{cols.max()}) ↔ design chính y{off + s}-{off + e}{edge}")
            if a.out:
                h = e - s; c = Image.new('RGB', (M.width * 2 + 10, h), 'red')
                c.paste(M.crop((0, off + s, M.width, off + e)), (0, 0)); c.paste(R.crop((0, s, R.width, e)), (M.width + 10, 0))
                p = os.path.join(a.out, f"{os.path.splitext(name)[0]}_{i}.png"); c.save(p)
                print(f"     → {p}  (trái: design chính | phải: ảnh phụ)")
    print(f"\n{found}/{len(a.refs)} ảnh phụ có nội dung KHÔNG có trong design chính → ghi vào bảng phân loại ảnh và hiện thực (L-FLOW-09).")
    sys.exit(1 if found else 0)


if __name__ == '__main__':
    main()
