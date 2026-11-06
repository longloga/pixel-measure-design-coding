#!/usr/bin/env python3
"""Kiểm tra tự động HTML/CSS/responsive/liên kết cho 1 hoặc nhiều trang tĩnh (không cần design).
Gồm 2 lớp:
  1. Tĩnh (đọc file): thẻ không đóng/đóng sai, id trùng, img thiếu alt/src, file ảnh/CSS/JS/link nội bộ
     không tồn tại, url() trong CSS hỏng, target=_blank thiếu rel, <a> lồng nhau, thứ tự heading,
     href="#" còn sót, tel:/mailto: sai; semantic (SEM-*/FORM-*): h1 ngoài <main>, <section> không heading,
     aria-label trên div/span không role, <small> trong heading, input không label/autocomplete,
     <th> thiếu scope, <picture><source> khác tỉ lệ ảnh mà thiếu width/height (CLS).
  2. Runtime (Playwright, nhiều viewport): tràn ngang + phần tử gây tràn, ảnh lỗi, request 404,
     lỗi console/JS, font web chưa load (rơi về font hệ thống), chữ bị cắt (overflow hidden),
     chữ < 12px ở SP, vùng chạm < 32px ở SP, phần tử bị che/ra ngoài viewport.

  python3 audit.py index.html about.html                     # tĩnh + runtime pc=1440, tb=1024, sp=375
  python3 audit.py *.html --vp pc=1440 --vp sp=375 --json out/audit.json
  python3 audit.py index.html --static-only
  python3 audit.py index.html --base http://localhost:8080/   # trang dùng path gốc "/data/..."
  python3 audit.py index.html --base http://localhost:8080/ --spec spec.json --ab "TOP_PC=1280x740" --ab "TOP_SP=375x740"
      → thêm vị trí khung/chữ theo XD/Figma (xdpos.py): khung lệch = E XD-POS, chữ lệch = W XD-POS-TEXT
  Static còn có W CSS-CLASS-CLASH: class 1 từ vừa là component cấp gốc vừa là element trong component khác (L-CSS-10).

Tag CMS (@link(123), @page_url, {{...}}, <?php ... ?>) được coi là hợp lệ, không báo lỗi.
Mã lỗi (E=lỗi phải sửa, W=cảnh báo nên xem, I=thông tin) dùng chung với references/lessons.md.
Exit code 1 nếu còn E — dùng được trong vòng lặp sửa.

Lỗi mạng/console của tài nguyên KHÁC domain trang (GTM, analytics, font CDN bị CORS khi chạy localhost...)
vẫn được báo nhưng ở mức W với hậu tố -EXT (không làm exit 1). `--strict-external` để coi chúng là E như cũ.
Trang chờ networkidle tối đa --settle ms rồi kiểm tra tiếp (báo I LOAD-SLOW) thay vì lỗi timeout.
"""
import argparse, json, os, re, sys
from collections import Counter
from html.parser import HTMLParser
from urllib.parse import urlparse, unquote

VOID = set('area base br col embed hr img input link meta param source track wbr'.split())
# thẻ mà trình duyệt tự đóng — không báo lỗi khi thiếu thẻ đóng
OPTIONAL_CLOSE = set('p li dt dd option tr td th thead tbody tfoot colgroup rt rp optgroup'.split())
CMS = re.compile(r'^\s*(@\w|\{\{|\{%|<\?|\$\{|\[\[)')


def is_external(u):
    return bool(re.match(r'^(https?:)?//', u)) or u.startswith(('data:', 'javascript:', 'blob:'))


class Parser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.issues, self.ids, self.refs, self.heads = [], [], Counter(), [], []
        self.a_depth = 0
        self.sections, self.pictures, self.labels_for, self.fields = [], [], set(), []
        self.has_main = False

    def open_tags(self):
        return [t for t, _ in self.stack]

    def add(self, lv, code, msg):
        self.issues.append((lv, code, self.getpos()[0], msg))

    def handle_starttag(self, tag, attrs):
        at = dict(attrs)
        if tag not in VOID:
            if tag in OPTIONAL_CLOSE and self.stack and self.stack[-1][0] == tag and tag in ('p', 'li', 'dt', 'dd', 'option', 'tr', 'td', 'th'):
                self.stack.pop()
            self.stack.append((tag, self.getpos()[0]))
        if 'id' in at and at['id']: self.ids[at['id']] += 1
        self.semantic(tag, at)
        if tag == 'a':
            if self.a_depth: self.add('E', 'HTML-NESTED-A', '<a> lồng trong <a>')
            self.a_depth += 1
            h = at.get('href')
            if h is None: self.add('W', 'LINK-NO-HREF', '<a> không có href')
            elif h.strip() in ('#', ''): self.add('I', 'LINK-PLACEHOLDER', f'href="{h}" (link chưa có)')
            else: self.refs.append(('a', h, self.getpos()[0]))
            if at.get('target') == '_blank' and 'noopener' not in (at.get('rel') or '') and 'noreferrer' not in (at.get('rel') or ''):
                self.add('W', 'LINK-BLANK-REL', f'target=_blank thiếu rel="noopener": {h}')
            if h and h.startswith('tel:') and not re.match(r'^tel:\+?[\d-]+$', h): self.add('E', 'LINK-TEL', f'tel sai định dạng: {h}')
            if h and h.startswith('mailto:') and '@' not in h: self.add('E', 'LINK-MAIL', f'mailto sai: {h}')
        if tag == 'img':
            if 'alt' not in at: self.add('E', 'IMG-ALT', f'img thiếu alt: {at.get("src")}')
            if not at.get('src'): self.add('E', 'IMG-SRC', 'img thiếu src')
            else: self.refs.append(('img', at['src'], self.getpos()[0]))
            if not ('width' in at and 'height' in at): self.add('I', 'IMG-SIZE', f'img không có width/height — CSS phải giữ chỗ (aspect-ratio / khung cố định), xem L-HTML-09: {at.get("src")}')
        if tag == 'source' and at.get('srcset'):
            self.refs.append(('img', at['srcset'].split(',')[0].split()[0], self.getpos()[0]))
        if tag == 'link' and at.get('href') and 'stylesheet' in (at.get('rel') or ''): self.refs.append(('css', at['href'], self.getpos()[0]))
        if tag == 'script' and at.get('src'): self.refs.append(('js', at['src'], self.getpos()[0]))
        if re.fullmatch(r'h[1-6]', tag): self.heads.append((int(tag[1]), self.getpos()[0]))
        if 'style' in at and at['style'] and re.search(r'url\(', at['style']):
            for u in re.findall(r'url\(["\']?([^"\')]+)', at['style']): self.refs.append(('img', u, self.getpos()[0]))

    def semantic(self, tag, at):
        ln, opened = self.getpos()[0], self.open_tags()[:-1] if tag not in VOID else self.open_tags()
        if tag == 'main': self.has_main = True
        if tag in ('div', 'span', 'p') and ('aria-label' in at or 'aria-labelledby' in at) and 'role' not in at:
            self.add('W', 'SEM-ARIA-GENERIC', f'aria-label trên <{tag}> không có role (bị bỏ qua) — dùng <section>/<nav>/<aside> hoặc bỏ')
        if tag == 'section': self.sections.append([ln, False, 'aria-label' in at or 'aria-labelledby' in at])
        if re.fullmatch(r'h[1-6]', tag):
            if self.sections: self.sections[-1][1] = True
            if tag == 'h1' and 'main' not in opened: self.add('W', 'SEM-H1-OUTSIDE-MAIN', '<h1> nằm ngoài <main> (skip-link bỏ qua tiêu đề trang)')
        if tag == 'small' and any(re.fullmatch(r'h[1-6]', t) for t in opened):
            self.add('W', 'SEM-SMALL-STYLE', '<small> trong heading — <small> là chú thích phụ; chữ nhỏ để trang trí dùng <span class>')
        if tag == 'th' and 'scope' not in at: self.add('I', 'SEM-TH-SCOPE', '<th> thiếu scope="row|col"')
        if tag == 'label' and at.get('for'): self.labels_for.add(at['for'])
        if tag in ('input', 'select', 'textarea') and at.get('type') not in ('hidden', 'submit', 'button', 'reset', 'image'):
            self.fields.append((ln, tag, at, 'label' in opened))
        if tag == 'picture': self.pictures.append({'ln': ln, 'sources': [], 'img': None})
        if tag == 'source' and 'picture' in opened and self.pictures and at.get('srcset'):
            self.pictures[-1]['sources'].append((at['srcset'].split(',')[0].split()[0], 'width' in at and 'height' in at))
        if tag == 'img' and 'picture' in opened and self.pictures:
            self.pictures[-1]['img'] = (at.get('src'), at.get('width'), at.get('height'))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID and self.stack and self.stack[-1][0] == tag: self.stack.pop()

    def handle_endtag(self, tag):
        if tag in VOID: return
        if tag == 'a': self.a_depth = max(0, self.a_depth - 1)
        if tag == 'section' and self.sections:
            ln, has_head, labelled = self.sections.pop()
            if not has_head and not labelled: self.add('W', 'SEM-SECTION-NOHEAD', f'<section> (dòng {ln}) không có heading — dùng <div> hoặc thêm heading')
        names = [t for t, _ in self.stack]
        if tag not in names:
            self.add('E', 'HTML-STRAY-CLOSE', f'</{tag}> không có thẻ mở tương ứng'); return
        while self.stack:
            t, ln = self.stack.pop()
            if t == tag: break
            if t not in OPTIONAL_CLOSE: self.add('E', 'HTML-UNCLOSED', f'<{t}> (dòng {ln}) chưa đóng trước </{tag}>')


def resolve(page, u, base_dir):
    """Trả về đường dẫn file local để kiểm tra tồn tại, hoặc None nếu không kiểm tra được."""
    if not u or CMS.match(u) or is_external(u) or u.startswith(('#', 'tel:', 'mailto:')): return None
    p = unquote(urlparse(u).path)
    if not p: return None
    root = base_dir if p.startswith('/') else os.path.dirname(os.path.abspath(page))
    f = os.path.normpath(os.path.join(root, p.lstrip('/')))
    if f.endswith('/') or os.path.isdir(f): f = os.path.join(f, 'index.html')
    return f


def picture_ratio_issues(page, root, pictures):
    """<source> có ảnh khác tỉ lệ với <img> mà không ghi width/height → trình duyệt giữ chỗ theo tỉ lệ img → nhảy layout."""
    try:
        from PIL import Image
    except ImportError:
        return []
    def ratio(u):
        f = resolve(page, u, root)
        if not f or not os.path.exists(f): return None
        try:
            w, h = Image.open(f).size
            return w / h
        except Exception:
            return None
    out = []
    for pic in pictures:
        if not pic['img'] or not pic['img'][0]: continue
        src, w, h = pic['img']
        base = (float(w) / float(h)) if (w and h and w.replace('.', '').isdigit() and h.replace('.', '').isdigit()) else ratio(src)
        if not base: continue
        for s, has_dim in pic['sources']:
            r = ratio(s)
            if r and not has_dim and abs(r - base) / base > 0.02:
                out.append(('W', 'SOURCE-SIZE', pic['ln'], f'<source> {s} khác tỉ lệ ảnh img ({r:.2f} vs {base:.2f}) — thêm width/height cho <source> (CLS)'))
    return out


def static_audit(page, root):
    src = open(page, encoding='utf-8', errors='replace').read()
    P = Parser(); P.feed(src); P.close()
    out = list(P.issues)
    for t, ln in P.stack:
        if t not in OPTIONAL_CLOSE | {'html', 'body', 'head'}: out.append(('E', 'HTML-UNCLOSED', ln, f'<{t}> chưa đóng tới cuối file'))
    for i, n in P.ids.items():
        if n > 1: out.append(('E', 'HTML-DUP-ID', 0, f'id="{i}" xuất hiện {n} lần'))
    prev = 0
    for lv, ln in P.heads:
        if prev and lv > prev + 1: out.append(('W', 'HTML-HEADING-SKIP', ln, f'h{prev} → h{lv} (nhảy cấp)'))
        prev = lv
    if sum(1 for lv, _ in P.heads if lv == 1) > 1: out.append(('W', 'HTML-MULTI-H1', 0, 'nhiều hơn 1 <h1>'))
    if not any(lv == 1 for lv, _ in P.heads): out.append(('W', 'SEM-NO-H1', 0, 'trang không có <h1>'))
    if not P.has_main: out.append(('W', 'SEM-NO-MAIN', 0, 'trang không có <main>'))
    for ln, tag, at, wrapped in P.fields:
        if not (wrapped or (at.get('id') and at['id'] in P.labels_for) or 'aria-label' in at or 'aria-labelledby' in at):
            out.append(('W', 'FORM-LABEL', ln, f'<{tag} name="{at.get("name")}"> không có <label> liên kết'))
        nm = (at.get('name') or '').lower()
        if tag == 'input' and 'autocomplete' not in at and (at.get('type') in ('email', 'tel') or nm in ('name', 'email', 'tel', 'zip', 'address')):
            out.append(('I', 'FORM-AUTOCOMPLETE', ln, f'input name="{at.get("name")}" nên có autocomplete'))
    out += picture_ratio_issues(page, root, P.pictures)
    if not re.search(r'<meta[^>]+name=["\']viewport', src, re.I): out.append(('E', 'RESP-VIEWPORT', 0, 'thiếu <meta name="viewport">'))
    if re.search(r'\sstyle="[^"]*(?:width|margin|padding|font-size)\s*:', src): out.append(('I', 'CSS-INLINE', 0, 'có style inline về kích thước — nên chuyển vào SCSS'))
    css_files = []
    for kind, u, ln in P.refs:
        f = resolve(page, u, root)
        if f is None: continue
        if kind == 'a' and not os.path.splitext(f)[1]: continue  # route động, không đoán được
        if not os.path.exists(f):
            code = {'img': 'IMG-MISSING', 'css': 'FILE-MISSING', 'js': 'FILE-MISSING', 'a': 'LINK-BROKEN'}[kind]
            out.append(('E', code, ln, f'không tìm thấy {u}'))
        elif kind == 'css': css_files.append(f)
    out += class_clash_issues(src, css_files)
    for cf in css_files:
        css = open(cf, encoding='utf-8', errors='replace').read()
        for u in sorted(set(re.findall(r'url\(\s*["\']?([^"\')]+)', css))):
            f = resolve(cf, u, root)
            if f and not os.path.exists(f): out.append(('E', 'CSS-URL-MISSING', 0, f'{os.path.relpath(cf, root)}: url({u}) không tồn tại'))
    return out


LAYOUT_UTIL = set('container inner wrap wrapper row col clearfix cf pc tb sp xs sr-only visually-hidden'.split())
SEL_RULE = re.compile(r'([^{}]+)\{[^{}]*\}')
LAST_CLASS = re.compile(r'(?:^|[\s>+~])\.([A-Za-z][\w-]*)$')


def split_top(group):
    """Tách selector theo dấu phẩy CẤP NGOÀI (bỏ qua phẩy trong :not(...), :is(...))."""
    out, depth, cur = [], 0, ''
    for ch in group:
        if ch == '(': depth += 1
        elif ch == ')': depth -= 1
        if ch == ',' and depth == 0: out.append(cur); cur = ''
        else: cur += ch
    return out + [cur]


def class_clash_issues(html, css_files):
    """L-CSS-10: class vừa có rule CẤP GỐC (`.tag{}` = component dùng chung) vừa được dùng làm element trong
    component khác (`.step-box .tag{}`) → element kế thừa ngầm width/padding/font của component chung."""
    used = set(c for v in re.findall(r'class="([^"]*)"', html) for c in v.split())
    roots, owners = set(), {}
    for cf in css_files:
        css = re.sub(r'/\*.*?\*/', '', open(cf, encoding='utf-8', errors='replace').read(), flags=re.S)
        for sel_group in SEL_RULE.findall(css):
            for sel in split_top(sel_group):
                sel = sel.strip()
                if not sel or sel.startswith('@'): continue
                m = re.fullmatch(r'\.([A-Za-z][\w-]*)', sel)
                if m: roots.add(m.group(1)); continue
                m = LAST_CLASS.search(sel)
                if m and re.search(r'[\s>+~]', sel):
                    parent = re.split(r'[\s>+~]+', sel.strip())[-2] if len(re.split(r'[\s>+~]+', sel.strip())) > 1 else ''
                    owners.setdefault(m.group(1), set()).add(parent)
    out = []
    for c in sorted(roots & set(owners) & used):
        if '-' in c or c in LAYOUT_UTIL: continue  # tên 2 từ = component riêng (RSCSS); tiện ích layout dùng chung có chủ ý
        ps = sorted(p for p in owners[c] if p and p != '.' + c)[:3]
        if ps:
            out.append(('W', 'CSS-CLASS-CLASH', 0, f'.{c} là component cấp gốc (.{c}{{}}) nhưng cũng dùng làm element trong {", ".join(ps)} '
                        f'→ kế thừa ngầm style chung (L-CSS-10); chủ ý override thì bỏ qua, không thì đổi tên'))
    return out


RUNTIME_JS = r"""
(opt) => {
  const W = innerWidth, out = [];
  const label = (el) => {
    let s = el.tagName.toLowerCase();
    if (el.id) s += '#' + el.id;
    if (el.classList.length) s += '.' + [...el.classList].slice(0, 3).join('.');
    const p = el.parentElement;
    return (p && p !== document.body ? (p.className ? '.' + String(p.className).split(' ')[0] + ' > ' : '') : '') + s;
  };
  const visible = (el) => { const cs = getComputedStyle(el); const r = el.getBoundingClientRect();
    return cs.display !== 'none' && cs.visibility !== 'hidden' && +cs.opacity > 0 && r.width > 0 && r.height > 0; };
  const hiddenByAncestor = (el) => { for (let p = el.parentElement; p && p !== document.body; p = p.parentElement) {
    const cs = getComputedStyle(p); if (cs.overflowX === 'hidden' || cs.overflowX === 'clip' || cs.position === 'fixed') return true; } return false; };
  const all = [...document.body.querySelectorAll('*')];
  // 1. Phần tử gây tràn ngang (chỉ lấy phần tử ngoài cùng, bỏ con của nó)
  const over = all.filter(el => { const r = el.getBoundingClientRect();
    return (r.right > W + 1 || r.left < -1) && visible(el) && !hiddenByAncestor(el); });
  const top = over.filter(el => !over.some(o => o !== el && o.contains(el)));
  top.slice(0, 15).forEach(el => { const r = el.getBoundingClientRect();
    out.push(['E', 'RESP-OVERFLOW-EL', `${label(el)} tràn: left ${r.left.toFixed(0)} right ${r.right.toFixed(0)} (viewport ${W})`]); });
  // 2. Ảnh lỗi
  document.querySelectorAll('img').forEach(img => {
    if (img.complete && img.naturalWidth === 0 && img.getAttribute('src') && !/^@/.test(img.getAttribute('src')))
      out.push(['E', 'IMG-BROKEN', `ảnh không load: ${img.getAttribute('src')}`]);
    else if (img.naturalWidth && visible(img)) {
      const r = img.getBoundingClientRect(), dpr = opt.sp ? 2 : 1;
      // SVG là vector: naturalWidth chỉ là kích thước khai báo, không mờ khi phóng
      if (!/\.svg(\?|#|$)/i.test(img.currentSrc || img.getAttribute('src') || '') && img.naturalWidth < r.width * dpr * 0.75 && r.width > 80)
        out.push(['W', 'IMG-LOWRES', `${img.getAttribute('src')} hiển thị ${r.width.toFixed(0)}px nhưng ảnh gốc ${img.naturalWidth}px (mờ ở retina)`]);
      const cs = getComputedStyle(img);
      if (cs.objectFit === 'fill' && Math.abs(img.naturalWidth / img.naturalHeight - r.width / r.height) > 0.03 && r.height > 20)
        out.push(['W', 'IMG-DISTORT', `${img.getAttribute('src')} bị méo tỉ lệ (thêm object-fit hoặc sửa width/height)`]);
    }
  });
  // 3. Chữ bị cắt
  all.forEach(el => {
    if (!visible(el) || !el.childNodes.length) return;
    const cs = getComputedStyle(el);
    const hasText = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
    if (!hasText) return;
    // ẩn có chủ ý cho trình đọc màn hình (.sr-only / visually-hidden: khung 1x1px + clip) → không phải lỗi
    if (el.clientWidth <= 1 && el.clientHeight <= 1) return;
    if ((cs.overflow === 'hidden' || cs.overflowX === 'hidden') && cs.textOverflow !== 'ellipsis' && !cs.webkitLineClamp?.match?.(/\d/)
        && (el.scrollWidth > el.clientWidth + 2 || el.scrollHeight > el.clientHeight + 2))
      out.push(['W', 'TEXT-CLIPPED', `${label(el)} chữ bị cắt (${el.scrollWidth}x${el.scrollHeight} > ${el.clientWidth}x${el.clientHeight})`]);
    if (opt.sp && parseFloat(cs.fontSize) > 0 && parseFloat(cs.fontSize) < 12)
      out.push(['W', 'TEXT-TINY', `${label(el)} font-size ${cs.fontSize} < 12px ở SP`]);
  });
  // 4. Font web không dùng được -> rơi về font hệ thống
  const fams = new Set();
  all.forEach(el => { if (visible(el)) fams.add(getComputedStyle(el).fontFamily.split(',')[0].trim().replace(/["']/g, '')); });
  const generic = /^(serif|sans-serif|monospace|system-ui|-apple-system|inherit|initial|Font Awesome.*|FontAwesome)$/i;
  fams.forEach(f => { if (!generic.test(f) && !document.fonts.check(`16px "${f}"`))
    out.push(['W', 'FONT-NOT-LOADED', `font "${f}" chưa load — đang hiển thị bằng font dự phòng`]); });
  // 5. Vùng chạm nhỏ ở SP
  if (opt.sp) document.querySelectorAll('a[href], button, input, select, label[for]').forEach(el => {
    if (!visible(el)) return; const r = el.getBoundingClientRect();
    if ((r.width < 24 || r.height < 24) && el.textContent.trim().length < 3)
      out.push(['I', 'A11Y-TAP', `${label(el)} vùng chạm ${r.width.toFixed(0)}x${r.height.toFixed(0)}px`]); });
  return { issues: out, scrollWidth: document.documentElement.scrollWidth, height: document.documentElement.scrollHeight };
}
"""


SETTLE_MS = 8000
URL_RE = re.compile(r'https?://[^\s\'"]+')


def make_classifier(page_url, strict):
    host = urlparse(page_url).netloc

    def lv_code(code, *urls):
        ext = [u for u in urls if u and not u.startswith('data:') and urlparse(u).netloc and urlparse(u).netloc != host]
        if ext and len(ext) == len([u for u in urls if u]) and not strict:
            return 'W', code + '-EXT'
        return 'E', code

    def console(m):
        if m.type != 'error': return None
        loc = (m.location or {}).get('url', '')
        urls = URL_RE.findall(m.text) or [loc]
        return lv_code('JS-CONSOLE', *urls[:1])
    return lv_code, console


def runtime_audit(urls, vps, wait, strict=False):
    from playwright.sync_api import sync_playwright
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from _page import launch, open_page
    res = {}
    with sync_playwright() as p:
        b = launch(p)
        for name, url in urls:
            for vn, w in vps:
                pg = b.new_page(viewport={'width': int(w), 'height': 900})
                errs = []
                lv_code, console_lv = make_classifier(url, strict)
                pg.on('console', lambda m: errs.append((*console_lv(m), m.text[:200])) if m.type == 'error' else None)
                pg.on('pageerror', lambda e: errs.append(('E', 'JS-ERROR', str(e)[:200])))
                pg.on('response', lambda r: errs.append((*lv_code('HTTP-404', r.url), f'{r.status} {r.url[-120:]}')) if r.status >= 400 else None)
                pg.on('requestfailed', lambda r: errs.append((*lv_code('HTTP-FAIL', r.url), f'{r.failure} {r.url[-120:]}')) if not r.url.startswith('data:') else None)
                try:
                    note = open_page(pg, url, settle_ms=SETTLE_MS)
                    if note: errs.append(('I', 'LOAD-SLOW', note))
                except Exception as e:
                    errs.append(('E', 'LOAD', str(e)[:200]))
                # cuộn hết trang để kích hoạt lazy-load / inview animation
                pg.evaluate('async () => { for (let y = 0; y < document.body.scrollHeight; y += 600) { scrollTo(0, y); await new Promise(r => setTimeout(r, 40)); } scrollTo(0, 0); }')
                pg.evaluate('document.fonts.ready'); pg.wait_for_timeout(wait)
                r = pg.evaluate(RUNTIME_JS, {'sp': int(w) < 768})
                if r['scrollWidth'] > int(w): errs.append(('E', 'RESP-OVERFLOW', f'scrollWidth {r["scrollWidth"]} > viewport {w}'))
                res[(name, vn)] = [tuple(i) for i in errs] + [tuple(i) for i in r['issues']]
                pg.close()
        b.close()
    return res


def xdpos_issues(url, spec, ab, tol, settle):
    """Chạy xdpos.py: khung lệch (B) = E vì shape↔DOM khớp chính xác; chữ lệch (T) = W vì tâm chữ còn nhiễu metric font."""
    import subprocess, tempfile
    name, _, vp = ab.partition('=')
    vp = vp or '1280x740'
    tmp = tempfile.NamedTemporaryFile(suffix='.json', delete=False).name
    cmd = [sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'xdpos.py'), url, spec,
           '--ab', name, '--vp', vp, '--tol', str(tol), '--json', tmp, '--settle', str(settle)]
    if int(vp.split('x')[0]) < 768: cmd.append('--mobile')
    r = subprocess.run(cmd, capture_output=True, text=True)
    try: d = json.load(open(tmp))
    except Exception: return [('E', 'XD-POS-FAIL', f'xdpos.py lỗi: {(r.stderr or r.stdout)[-300:]}')]
    out = []
    for it in d['items']:
        if abs(it['loc']) <= tol + 0.5: continue
        lv, code = ('E', 'XD-POS') if it['kind'] == 'B' else ('W', 'XD-POS-TEXT')
        out.append((lv, code, f"y{it['y']:.0f} {it['el']} «{it['name']}» Δloc {it['loc']:+.0f}px (dy {it['dy']:+.0f}) → margin/padding ngay trên nó"))
    if d.get('wrong'): out.append(('I', 'XD-POS-SKIP', f"{len(d['wrong'])} mục lệch > 60px bị bỏ (ghép nhầm / khác chủ ý)"))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pages', nargs='+')
    ap.add_argument('--root', default='.', help='thư mục gốc site (để giải path bắt đầu bằng /)')
    ap.add_argument('--base', help='URL gốc khi phải chạy qua server (vd http://localhost:8080/)')
    ap.add_argument('--vp', action='append', help='name=width (mặc định pc=1440 tb=1024 sp=375)')
    ap.add_argument('--static-only', action='store_true')
    ap.add_argument('--wait', type=int, default=600)
    ap.add_argument('--json', help='ghi kết quả JSON (metrics.py đọc được)')
    ap.add_argument('--max-same', type=int, default=3, help='mỗi mã W/I chỉ in tối đa N dòng')
    ap.add_argument('--quiet-info', action='store_true', help='ẩn mục I')
    ap.add_argument('--strict-external', action='store_true', help='lỗi tài nguyên khác domain vẫn tính E (hành vi cũ)')
    ap.add_argument('--settle', type=int, default=8000, help='ms tối đa chờ networkidle')
    ap.add_argument('--spec', help='spec.json từ xdspec.py/figspec.py → chạy xdpos.py (vị trí khung/chữ, L-MEAS-15)')
    ap.add_argument('--ab', action='append', default=[], help='artboard=WxH cho --spec, vd "TOP_PC=1280x740" (lặp lại cho SP)')
    ap.add_argument('--pos-tol', type=float, default=2, help='ngưỡng Δloc px cho --spec')
    a = ap.parse_args()
    global SETTLE_MS
    SETTLE_MS = a.settle
    root = os.path.abspath(a.root)
    vps = [v.split('=') for v in (a.vp or ['pc=1440', 'tb=1024', 'sp=375'])]
    report = {}
    for pg in a.pages:
        report[(pg, 'static')] = [(lv, c, f'L{ln} {m}' if ln else m) for lv, c, ln, m in static_audit(pg, root)]
    if not a.static_only:
        urls = [(pg, (a.base.rstrip('/') + '/' + os.path.relpath(os.path.abspath(pg), root)) if a.base else 'file://' + os.path.abspath(pg)) for pg in a.pages]
        report.update(runtime_audit(urls, vps, a.wait, a.strict_external))
        if a.spec:
            for pg, url in urls:
                for ab in a.ab:
                    report[(pg, 'xdpos ' + ab)] = xdpos_issues(url, a.spec, ab, a.pos_tol, a.settle)
    total = Counter()
    for (pg, where), items in report.items():
        seen, rows = set(), []
        for it in items:
            if it in seen or (a.quiet_info and it[0] == 'I'): continue
            seen.add(it); rows.append(it); total[it[0]] += 1
        if not rows: continue
        print(f'\n## {pg} [{where}]')
        cnt = Counter(r[1] for r in rows); shown = Counter()
        for lv, code, msg in sorted(rows, key=lambda r: 'EWI'.index(r[0])):
            shown[code] += 1
            if lv != 'E' and cnt[code] > a.max_same and shown[code] > a.max_same:
                if shown[code] == a.max_same + 1: print(f'  {lv} {code:<18} ... và {cnt[code] - a.max_same} mục tương tự')
                continue
            print(f'  {lv} {code:<18} {msg}')
    print(f'\nTỔNG: E={total["E"]}  W={total["W"]}  I={total["I"]}')
    if a.json:
        os.makedirs(os.path.dirname(os.path.abspath(a.json)), exist_ok=True)
        json.dump({'total': dict(total), 'by_code': dict(Counter(i[1] for v in report.values() for i in v)),
                   'items': [{'page': p, 'where': w, 'level': i[0], 'code': i[1], 'msg': i[2]} for (p, w), v in report.items() for i in v]},
                  open(a.json, 'w'), ensure_ascii=False, indent=1)
    sys.exit(1 if total['E'] else 0)


if __name__ == '__main__':
    main()
