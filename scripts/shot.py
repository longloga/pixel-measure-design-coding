#!/usr/bin/env python3
"""Playwright + ローカルの Chrome で、コーディング結果を複数ビューポートでフルページ撮影する。
（`chrome --headless --window-size=375` は使わない: Chrome のウィンドウ最小幅は ~500px のため SP が正しくならない。）

  python3 shot.py file:///path/index.html --out shots/ --vp pc=1440 --vp sp=375
  python3 shot.py URL --vp pc=1400x675   # WxH: ビューポートの高さを指定（全画面 KV など 100vh の要素は
                                         # H = デザイン上の KV 下端座標 にするとデザインと同じ高さになる）
  python3 shot.py http://localhost:8080/index.html --out shots/ --hover ".btn"   # hover 状態も追加で撮影

撮影前にスクリプトが行うこと:
  - transition/animation を無効化（エフェクト途中を撮らないように）、
  - 上から下までスクロールして、画面内に入ったときの fade-in（inview / IntersectionObserver / AOS /
    WOW）と lazy-load 画像を発火させる — スクロールしないと .fade ブロックは opacity:0 のままで撮影結果が空になる、
  - document.fonts.ready を待つ（代替フォントで撮影しないように）、
  - スライダー（slick/swiper）があれば最初のスライドで停止。
ページは _page.open_page で読み込む: networkidle を最大 --settle ms 待ってから続行（GTM/アナリティクスでクラッシュしない）。
scrollWidth（横はみ出しの検出）とページの高さを出力する。
"""
import argparse, os, sys
from playwright.sync_api import sync_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _page import launch, open_page

FREEZE_CSS = '*,*::before,*::after{transition-duration:0s!important;transition-delay:0s!important;' \
             'animation-duration:0s!important;animation-delay:0s!important;animation-iteration-count:1!important;' \
             'caret-color:transparent!important;scroll-behavior:auto!important}'
SCROLL_JS = '''async () => {
  for (let y = 0; y < document.documentElement.scrollHeight; y += Math.round(innerHeight / 2)) {
    scrollTo(0, y); await new Promise(r => setTimeout(r, 60)); }
  scrollTo(0, document.documentElement.scrollHeight); await new Promise(r => setTimeout(r, 150));
  scrollTo(0, 0);
  try { if (window.jQuery) { jQuery('.slick-initialized').slick('slickPause').slick('slickGoTo', 0, true); } } catch (e) {}
  document.querySelectorAll('.swiper').forEach(s => { try { s.swiper.autoplay.stop(); s.swiper.slideTo(0, 0); } catch (e) {} });
  await document.fonts.ready;
}'''

ap = argparse.ArgumentParser()
ap.add_argument('url'); ap.add_argument('--out', default='.')
ap.add_argument('--vp', action='append', default=None, help='name=width hoặc name=WIDTHxHEIGHT (mặc định cao 900)')
ap.add_argument('--wait', type=int, default=800)
ap.add_argument('--no-freeze', action='store_true', help='giữ nguyên animation (khi cần chụp hiệu ứng)')
ap.add_argument('--hover', action='append', default=[], help='selector: chụp thêm ảnh khi hover phần tử đầu tiên khớp')
ap.add_argument('--dpr', type=float, default=1, help='device scale factor (2 để so với design @2x không cần co)')
ap.add_argument('--settle', type=int, default=8000, help='ms tối đa chờ networkidle trước khi chụp với DOM đã sẵn sàng')
a = ap.parse_args()
vps = [v.split('=') for v in (a.vp or ['pc=1440', 'sp=375'])]
os.makedirs(a.out, exist_ok=True)
with sync_playwright() as p:
    b = launch(p)
    for name, w in vps:
        w, _, vh = w.partition('x'); vh = int(vh) if vh else 900
        ctx = b.new_context(viewport={'width': int(w), 'height': vh}, device_scale_factor=a.dpr,
                            is_mobile=int(w) < 768, has_touch=int(w) < 768)
        pg = ctx.new_page()
        note = open_page(pg, a.url, a.settle)
        if note: print(f'  ({name}) {note}')
        if not a.no_freeze: pg.add_style_tag(content=FREEZE_CSS)
        pg.evaluate(SCROLL_JS); pg.wait_for_timeout(a.wait)
        pg.evaluate('document.fonts.ready.then(() => true)')
        sw = pg.evaluate('document.documentElement.scrollWidth')
        h = pg.evaluate('document.documentElement.scrollHeight')
        hidden = pg.evaluate('''() => [...document.querySelectorAll('body *')].filter(e => {
            const r = e.getBoundingClientRect(), c = getComputedStyle(e);
            return r.width > 50 && r.height > 20 && +c.opacity === 0 && c.visibility !== 'hidden'; })
            .filter((e, i, arr) => !arr.some(o => o !== e && o.contains(e)))
            .map(e => e.tagName.toLowerCase() + (e.className ? '.' + String(e.className).trim().split(/\s+/).join('.') : '')
                 + ' @y' + Math.round(e.getBoundingClientRect().top + scrollY))''')
        path = os.path.join(a.out, f'{name}.png'); pg.screenshot(path=path, full_page=True)
        print(name, 'width', w, 'scrollWidth', sw, '(TRÀN NGANG!)' if sw > int(w) else '', 'height', h, '->', path)
        if hidden:
            print(f'  ! còn {len(hidden)} khối opacity:0 sau khi cuộn (nếu là fade-in chưa chạy thì phải xử lý trước khi so; '
                  f'nếu ẩn có chủ ý như scroll-hint, tooltip thì bỏ qua):')
            for e in hidden[:8]: print('     ', e)
        for i, sel in enumerate(a.hover):
            el = pg.query_selector(sel)
            if not el: print('  ! không tìm thấy', sel); continue
            el.scroll_into_view_if_needed(); el.hover(); pg.wait_for_timeout(400)
            bb = el.bounding_box(); pad = 40
            hp = os.path.join(a.out, f'{name}_hover{i}.png')
            pg.screenshot(path=hp, clip={'x': max(bb['x'] - pad, 0), 'y': max(bb['y'] - pad, 0), 'width': bb['width'] + pad * 2, 'height': bb['height'] + pad * 2})
            print('  hover', sel, '->', hp)
        ctx.close()
    b.close()
