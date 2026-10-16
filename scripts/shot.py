#!/usr/bin/env python3
"""Chụp full-page bản code ở nhiều viewport bằng Playwright + Chrome của máy.
(Không dùng `chrome --headless --window-size=375`: Chrome có độ rộng cửa sổ tối thiểu ~500px nên SP sai.)

  python3 shot.py file:///path/index.html --out shots/ --vp pc=1440 --vp sp=375
  python3 shot.py http://localhost:8080/index.html --out shots/ --hover ".btn"   # chụp thêm trạng thái hover

Trước khi chụp, script:
  - tắt transition/animation (để không chụp giữa chừng hiệu ứng),
  - cuộn từ trên xuống dưới để kích hoạt fade-in khi vào màn hình (inview / IntersectionObserver / AOS /
    WOW) và ảnh lazy-load — KHÔNG cuộn thì các khối .fade vẫn opacity:0 và ảnh chụp bị trống,
  - chờ document.fonts.ready (tránh chụp bằng font dự phòng),
  - dừng slider (slick/swiper) ở slide đầu nếu có.
In ra scrollWidth (phát hiện tràn ngang) và chiều cao trang.
"""
import argparse, os
from playwright.sync_api import sync_playwright

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
ap.add_argument('--vp', action='append', default=None, help='name=width')
ap.add_argument('--wait', type=int, default=800)
ap.add_argument('--no-freeze', action='store_true', help='giữ nguyên animation (khi cần chụp hiệu ứng)')
ap.add_argument('--hover', action='append', default=[], help='selector: chụp thêm ảnh khi hover phần tử đầu tiên khớp')
ap.add_argument('--dpr', type=float, default=1, help='device scale factor (2 để so với design @2x không cần co)')
a = ap.parse_args()
vps = [v.split('=') for v in (a.vp or ['pc=1440', 'sp=375'])]
os.makedirs(a.out, exist_ok=True)
cands = ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '/usr/bin/google-chrome', '/usr/bin/chromium']
exe = next((c for c in cands if os.path.exists(c)), None)
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
    for name, w in vps:
        ctx = b.new_context(viewport={'width': int(w), 'height': 900}, device_scale_factor=a.dpr,
                            is_mobile=int(w) < 768, has_touch=int(w) < 768)
        pg = ctx.new_page()
        pg.goto(a.url); pg.wait_for_load_state('networkidle')
        if not a.no_freeze: pg.add_style_tag(content=FREEZE_CSS)
        pg.evaluate(SCROLL_JS); pg.wait_for_timeout(a.wait)
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
