# CHANGELOG

Mọi thay đổi của skill này (script, `SKILL.md`, `references/`, README) đều phải có 1 mục ở đây, mới nhất ở
trên cùng. Mỗi mục gồm 4 phần:

- **Thay đổi** — làm gì (1 dòng mỗi ý).
- **Lý do** — vấn đề THỰC TẾ nào dẫn tới thay đổi, kèm mã bài học (`L-XXX-NN`) nếu có. Không ghi tên khách
  hàng / dự án / đường dẫn máy (repo này được chia sẻ).
- **So sánh trước / sau** — hành vi và số liệu đo được trước và sau khi đổi (thời gian, số lần lỗi, số E/W
  của audit, độ lệch px...). Không có số thì ghi rõ "chưa đo".
- **Tương thích** — lệnh cũ còn chạy như trước không, option nào để giữ hành vi cũ.

Tạo khung tự động (đã điền sẵn danh sách file, option CLI, mã bài học thay đổi):
`python3 scripts/changelog.py draft` · kiểm tra trước khi commit: `python3 scripts/changelog.py check`
(git pre-commit hook: `python3 scripts/changelog.py install-hook`).

Phiên bản: `MAJOR.MINOR.PATCH` — MAJOR khi bỏ/đổi hành vi cũ không tương thích, MINOR khi thêm script /
option / quy trình, PATCH khi sửa lỗi hoặc chỉnh chữ.

---

## [1.9.1] — 2026-11-13 — Comment / docstring trong script chuyển sang tiếng Nhật

### Thay đổi
- `scripts/*.py` (21 file): toàn bộ comment `#`, comment JS `//` nhúng trong script và docstring (module + hàm) dịch
  từ tiếng Việt sang tiếng Nhật. Nội dung giữ nguyên ý, ví dụ lệnh giữ nguyên.
- `.gitignore`, comment của git pre-commit hook do `changelog.py install-hook` tạo: dịch sang tiếng Nhật.
- Không đổi logic, option CLI, message in ra màn hình.

### Lý do
- Quy tắc mới: comment trong code phải viết bằng tiếng Nhật để thành viên người Nhật đọc hiểu được (repo public).

### So sánh trước / sau
- Trước: comment/docstring tiếng Việt. Sau: tiếng Nhật; `py_compile` toàn bộ script OK, `audit.py --help` chạy được.
- Số liệu hiệu suất: không ảnh hưởng (chưa đo — không đổi hành vi).

### Tương thích
- Hoàn toàn tương thích; chỉ đổi phần mô tả `--help` (lấy từ docstring) sang tiếng Nhật.

## [1.9.0] — 2026-11-06 — Tự động hoá 3 lỗi lặp nhiều nhất, audit kiểm vị trí theo XD, metrics đúng số

### Thay đổi
- `scripts/audit.py`: `--spec spec.json --ab "ARTBOARD=WxH"` (lặp được) → gọi `xdpos.py`; khung lệch = E `XD-POS`,
  chữ lệch = W `XD-POS-TEXT`, `--pos-tol` (mặc định 2). Static thêm W `CSS-CLASS-CLASH` (class 1 từ vừa là rule cấp gốc
  vừa là element trong component khác; bỏ qua tiện ích layout `.container/.inner/.pc/.sp...`; tách selector đúng
  với `:not(a,b)`).
- Thêm `scripts/refcheck.py`: dò vị trí từng ảnh phụ trong design chính (profile hàng + tinh chỉnh ±6px), in dải
  nội dung chỉ có ở ảnh phụ, đánh dấu mép trên/dưới màn hình, cắt ảnh so sánh; exit 1 nếu có.
- `scripts/metrics.py`: `start` (a) tự đóng run cũ chưa `end` của cùng thư mục (đánh dấu bỏ dở, tính tới sự kiện
  cuối), (b) `--source png|other` → liệt kê file .xd/.fig trong dự án + Desktop/Downloads (14 ngày), `--no-source-check`
  để bỏ. `report`: cột `user_req` = mọi lần người dùng yêu cầu sửa (trước + sau giao); run không hoạt động > 12h coi là
  bỏ dở và loại khỏi trung bình; review chỉ lấy trung bình trên run có điểm + nhắc khi < nửa số run có điểm.
- `SKILL.md`: refcheck ở bước 1, audit `--spec` ở bước 6, cách đọc mã mới. `lessons.md`: L-CSS-10, L-MEAS-11,
  L-FLOW-09 ghi số lần lặp + cột Tự động. README (JA/VI): thêm refcheck.py.

### Lý do
- `metrics.py report`: 3 bài học vi phạm nhiều nhất L-CSS-10 (3×), L-MEAS-11 (3×), L-FLOW-09 (2×) chỉ là quy tắc chữ
  → vẫn lặp. xdpos (1.8.0) phải nhớ chạy riêng (L-MEAS-13 lặp 2×) → gắn vào audit, lệnh Claude luôn chạy.
- Số liệu metrics sai lệch: "0.1 lần bị yêu cầu sửa" trong khi thực tế 2.4 lỗi sau giao (không cộng lần sửa sau giao);
  review TB 0.5/5 vì tính run không chấm là 0; 1 run bỏ dở ghi 30.188 phút.

### So sánh trước / sau
| Hạng mục | Trước | Sau |
|---|---|---|
| audit trên trang top (CSS còn lệch margin) | không biết vị trí: E=0 liên quan | E `XD-POS` 1 + W `XD-POS-TEXT` 22 (đúng các section lệch) |
| audit trên cùng trang sau khi sửa margin | — | 0 E XD-POS, 2 W (nhiễu font, đã xác nhận ±1px) |
| L-CSS-10 (CSS giả lập `.tag{}` + `.step-box .tag{}`) | không báo | W CSS-CLASS-CLASH; trang thật: 0 báo nhầm (sau sửa `:not()` / tiện ích) |
| L-FLOW-09 (ảnh 1 màn hình có thanh CTA 80px ở đáy) | không công cụ | refcheck: khớp y=3000, 1 dải "MÉP DƯỚI" y660-740; ảnh cắt thường: 0 dải (1.5s) |
| L-MEAS-11 khi `start --source png` | không cảnh báo | liệt kê file nguồn (máy thử: 10 file 14 ngày, in 5) |
| metrics: số lần người dùng yêu cầu sửa / run | 0.1 | 2.5 (đúng) |
| metrics: review TB | 0.5/5 (tính cả run không chấm) | 5.0/5 (1 run có chấm) + nhắc chấm |
| metrics: run bỏ dở 30.188 phút | tính vào TB | loại khỏi TB, ghi "(bỏ dở)" |

### Tương thích
- Lệnh cũ chạy như trước. audit không có `--spec` thì không gọi xdpos; `CSS-CLASS-CLASH` chỉ là W (không đổi exit).
  metrics: cột `user_fixes` trong report thay bằng `user_req` (CSV đổi tên cột tương ứng); `start` có thể in cảnh báo
  / tự đóng run cũ — `--no-source-check` để tắt cảnh báo nguồn.

## [1.8.0] — 2026-11-05 — xdpos.py + inkcmp.py: kiểm VỊ TRÍ dọc từng khối/chữ (margin), không chỉ style

### Thay đổi
- Thêm `scripts/xdpos.py`: ghép shape XD/Figma ↔ phần tử DOM (x/w/h ±3) và đoạn chữ ↔ text node, so tâm dòng
  (XD `y + size/2`), in `dy` và `Δloc` (lệch phát sinh giữa 2 mục cùng loại) — exit 1 nếu |Δloc| > `--tol` (mặc định 2).
- Thêm `scripts/inkcmp.py`: tách dòng mực trong 1 cột (`--box`) của ảnh design và ảnh render, so top→top → `Δloc` = px
  margin/padding cần sửa; khối cao khác > `--hdiff` (dính hình trang trí) đánh "?" và bỏ qua; exit 1 nếu còn lệch.
- `SKILL.md`: thêm 2 script vào bảng, bước 0b (sau xdcmp phải chạy xdpos), bước 6 (lệnh + mục "Khoảng cách trong
  section"), điều kiện đạt thêm `xdpos exit 0` và `inkcmp Δloc ≤ 1`.
- `references/lessons.md`: L-MEAS-13 ghi **lặp lại lần 2** + cột Tự động; thêm L-MEAS-15 [!!], L-SHOT-11 [!!],
  L-CSS-22 [!], L-IMG-07 [!].
- `references/measurement-rules.md`: mục "Toạ độ chữ từ XD/Figma và so vị trí".

### Lý do
- Trang top dài ~10k px code theo XD: `xdcmp.py` báo style chữ khớp, `pixeldiff` `final_drift` 8px, nhưng người dùng
  so với ảnh design thấy lệch margin-bottom ở nhiều chỗ. Đo lại: 8 section lệch 2–13px (khoảng label↔heading↔catch,
  padding-top trong card, chữ trong banner, ảnh→tiêu đề card, chữ trong card link, footer). Lệch +5/−4 bù trừ nên
  pixeldiff dải 200px không thấy (L-SHOT-11). L-MEAS-13 đã yêu cầu so rect DOM với spec nhưng chưa có script → bị bỏ
  qua lần 2 (L-MEAS-13, L-MEAS-15).
- Lúc sửa phải viết tay 5 script tạm (ghép shape, ghép chữ, tách mực, so blocks, truy vấn rect) — gom thành 2 script.
- Tab cao 56 thay vì 55 + `align-items:center`, logo có viền trong suốt (L-CSS-22); ảnh nền cắt từ design đã có lớp
  phủ nhưng CSS phủ thêm → màu đậm gấp đôi, người dùng tưởng ảnh design là bản cũ (L-IMG-07).

### So sánh trước / sau
Đo trên cùng trang, CSS trước khi sửa margin ↔ sau khi sửa (PC 1280):

| Hạng mục | Trước | Sau |
|---|---|---|
| Công cụ kiểm vị trí dọc theo XD | không có (chỉ xdcmp = style) | `xdpos.py`, `inkcmp.py` |
| `xdpos.py --tol 2`: mục báo lệch / 230 | 23 (đúng 8 section phải sửa) | 2 (do đổi font, ink xác nhận ±1) |
| `inkcmp.py` 8 section: khối báo lệch | 11 | 0 |
| `pixeldiff` final_drift / chênh chiều cao | 8px / +8px (trông "gần đạt") | 0 / 0 |
| Lệch lớn nhất khung XD↔DOM (sau căn) | 13px trong section | ±1px |
| Số script tạm phải viết khi điều tra | 5 | 0 |

### Tương thích
- Chỉ thêm script/tài liệu; lệnh cũ (`xdcmp`, `pixeldiff`, `rects`, `rowcmp`) không đổi. Điều kiện "đạt" ở bước 6
  chặt hơn (thêm xdpos/inkcmp).

## [1.7.1] — 2026-11-05 — lessons: L-CSS-21 (style blockquote tại base/_cms.scss)

### Thay đổi
- `references/lessons.md`: thêm L-CSS-21 [!].

### Lý do
- Code trang regulation: trích dẫn được làm thành class `.quote-box` mới, trong khi template đã định nghĩa `blockquote`
  ở `base/_cms.scss`; người dùng yêu cầu chuyển style về thẻ `blockquote` tại đó (L-CSS-21).

### So sánh trước / sau
| Hạng mục | Trước | Sau |
|---|---|---|
| Vị trí style trích dẫn | class mới trong style chung | thẻ `blockquote` trong `base/_cms.scss` |
| Độ lệch khối trích dẫn (DOM vs design) | PC 0px / SP 0px Δloc | không đổi (PC 0px / SP 0px Δloc) |

### Tương thích
- Chỉ thêm tài liệu; không đổi script/lệnh.

## [1.7.0] — 2026-10-30 — figspec.py: spec chữ/shape từ Figma qua Plugin API (letter-spacing đúng đơn vị)

### Thay đổi
- Thêm `scripts/figspec.py`: `js <frameId>... [--only texts|shapes]` in đoạn JS cho `use_figma` (đọc từng đoạn chữ:
  family / weight / size / letterSpacing {unit, value} / lineHeight / màu; shape: fill / viền / bo góc / shadow / blur /
  opacity hiệu dụng); `save raw.json... --out spec.json --summary` gộp thành spec cùng định dạng xdspec.
- `SKILL.md` bước 0b: quy trình khi có link Figma — không lấy ls/lh từ `get_design_context`.
- `references/lessons.md`: thêm L-MEAS-14 [!!].
- `scripts/xdcmp.py`: chỉ sửa docstring (nhận spec từ figspec.py).

### Lý do
- Người dùng thấy letter-spacing lấy từ Figma vẫn sai (L-MEAS-14). Kiểm trên file thật: 412 text node, mọi
  letterSpacing đều đơn vị PERCENT (0 / 1.6 / 6 / 8 / 10%), nhưng `get_design_context` xuất `tracking-[0.96px]` cho
  đoạn 16px 6% → mất đơn vị gốc, dễ chép thành px và sai khi font-size đổi ở SP.

### So sánh trước / sau
| Hạng mục | Trước | Sau |
|---|---|---|
| ls của đoạn 16px 6% | `0.96px` (get_design_context) | `ls 0.06` / `ls_raw "6%"` → `.06em` |
| Đoạn chữ có spec trên frame カラムあり（PC） | 0 (không có công cụ) | 106 đoạn, ~21 KB return |
| Kiểm chứng tự động với Figma | không | `xdcmp.py` dùng chung spec |

### Tương thích
- Chỉ thêm script/tài liệu; xdspec.py / xdcmp.py chạy như cũ.

## [1.6.3] — 2026-10-29 — Bài học: kiểm từng phần tử theo XD, nhãn inline-block, icon Font Awesome

### Thay đổi
- `references/lessons.md`: thêm L-MEAS-13 [!!] (pixeldiff dải không chứng minh từng phần tử khớp — bắt buộc
  xdcmp + rect DOM vs spec mỗi vòng), L-CSS-19 [!] (nhãn inline-block tạo line box cao), L-CSS-20 [!] (icon Font
  Awesome rộng cố định 1.25em).

### Lý do
- Sau khi báo "max Δ 5px, tổng chiều cao khớp", người dùng đối chiếu thông số XD và chỉ ra: logo 187→191px, hàng
  header phải lệch 4–6px, chữ KV lệch, khoảng dưới thẻ お知らせ và khoảng trên/dưới đoạn chữ thẻ ご相談 lệch.
  Khi kiểm lại bằng `xdcmp.py` (chưa chạy ở các vòng trước) còn phát hiện màu tag sai (cam → xanh #31a867).

### So sánh trước / sau (cùng trang top)
| Hạng mục | Trước | Sau |
|---|---|---|
| xdcmp PC: lệch size/weight/ls/màu | 1 (màu tag) | 0 |
| xdcmp SP: lệch size/weight/ls/màu | 0 (chưa chạy trước đó) | 0 |
| Rect DOM vs XD (thẻ お知らせ, khung ご相談, thẻ 地域医療, 採用, footer) | lệch 2–6px | ≤ 2px |
| pixeldiff PC height_diff / SP height_diff | -1 / 15 | 0 / 1 |

### Tương thích
- Chỉ thêm tài liệu, không đổi script.

## [1.6.2] — 2026-10-29 — Không ghi width/height trên img; giữ chỗ bằng CSS

### Thay đổi
- `references/lessons.md`: viết lại L-HTML-09 — mặc định không ghi width/height trong HTML; giữ chỗ bằng CSS
  (`aspect-ratio` / khung cố định); SVG tự xuất có width/height gốc = viewBox; cách kiểm chứng (chặn ảnh → đo → tải → đo).
- `SKILL.md` bước 5: thay dòng "luôn có width/height" bằng quy tắc mới.
- `scripts/audit.py`: thông báo `IMG-SIZE` (mức I) đổi nội dung — nhắc kiểm CSS giữ chỗ thay vì yêu cầu thuộc tính.

### Lý do
- Người dùng yêu cầu bỏ width/height trên img (nếu không ảnh hưởng) và không thêm nữa. Khi bỏ trên trang top đo
  được 2 ảnh hưởng thật và đã khắc phục bằng CSS: SVG làm tròn kích thước gốc (lệch 1px), icon SP `height:auto` làm
  khối nhảy 18px khi tải (L-HTML-09).

### So sánh trước / sau (cùng 1 trang top)
| Hạng mục | Trước (có width/height) | Sau (bỏ, + aspect-ratio / SVG viewBox) |
|---|---|---|
| Thẻ img có width/height | 25 | 0 |
| Chênh `top` các section khi ảnh chưa tải → đã tải (1400/1000/375/320) | 0 / – / – / – (chưa đo) | 0 / 0 / 0 / 0 px |
| CLS đo khi ảnh trễ 400ms (PC / SP) | 0.001 / 0.002 | 0.001 / 0.002 |
| pixeldiff PC (max Δ, height_diff) | 5 / 2 | 5 / -1 |

### Tương thích
- Không đổi option/mã lỗi; chỉ đổi nội dung thông báo IMG-SIZE và tài liệu.

## [1.6.1] — 2026-10-29 — audit.py: bỏ báo nhầm cho .sr-only và ảnh SVG

### Thay đổi
- `scripts/audit.py`: `TEXT-CLIPPED` bỏ qua phần tử khung ≤ 1×1px (mẫu `.sr-only` / visually-hidden — ẩn có chủ ý
  cho trình đọc màn hình). `IMG-LOWRES` bỏ qua ảnh `.svg` (vector, naturalWidth chỉ là kích thước khai báo).

### Lý do
- Khi thêm ngữ cảnh ẩn cho các link trùng tên (「詳細を見る<span class="sr-only">（…）</span>」) để đạt semantic,
  audit báo 12 W `TEXT-CLIPPED`; icon/minh hoạ xuất SVG từ XD bị báo `IMG-LOWRES` ở SP/XS. Cả hai đều không phải lỗi,
  làm loãng danh sách W thật.

### So sánh trước / sau (cùng 1 trang top, vp pc=1400 tb=1000 sp=375 xs=320)
| Hạng mục | Trước | Sau |
|---|---|---|
| W `TEXT-CLIPPED` (.sr-only) | 12 | 0 |
| W `IMG-LOWRES` (.svg) | 6 | 0 |
| Tổng W | 43 | 11 (còn lại: TEXT-TINY theo design, SEM-H1-OUTSIDE-MAIN do khung template) |
| E | 1 (favicon 404 — tag CMS) | 1 (không đổi) |

### Tương thích
- Không đổi option. Chữ bị cắt thật (khung > 1px) và ảnh bitmap vẫn được báo như cũ.

## [1.6.0] — 2026-10-29 — Trang trí mờ theo group (opacity/lớp), viewport cao tuỳ chỉnh, mask bị bỏ

### Thay đổi
- `scripts/xdspec.py`: opacity của shape nhân thêm opacity của mọi group/artboard cha (XD áp opacity cho cả nhóm);
  thêm field `gop` (phần opacity từ group), `group` (tên group trực tiếp), `z` (thứ tự vẽ). `--summary` thêm mục
  "Trang trí bán trong suốt". Sửa crash `KeyError: 'w'` khi in mục hiệu ứng cho shape không phải rect/line.
- `scripts/shot.py`: `--vp name=WIDTHxHEIGHT` để đặt chiều cao viewport (mặc định vẫn 900).
- `references/lessons.md`: L-CSS-17 [!!] (blob trang trí: opacity group + lớp chồng giữa các section),
  L-CSS-18 [!] (`mask` nhiều lớp bị trình duyệt bỏ → KV hình chữ nhật), L-SHOT-10 [!] (phần tử 100vh khi chụp).
- `SKILL.md`: bước 0b nhắc đọc mục trang trí bán trong suốt; bước 6 ví dụ `--vp pc=1440x<đáy KV>`.

### Lý do
- Trang top có các vòng tròn mờ cam/xanh: XD đặt từng cặp trong group có opacity 0.21–0.33, `xdspec` cũ báo 1.0
  → code quá đậm; sau đó đặt lớp sai (blob của section sau nằm trên nền + đường cong của section trước). Người dùng
  chỉ ra 2 lần (L-CSS-17).
- Đáy KV cong bằng `mask` nhiều lớp với `calc()` trong kích thước `radial-gradient` → khai báo bị bỏ, KV vuông;
  người dùng chỉ ra (L-CSS-18).
- KV `100vh` không so được với design vì `shot.py` cố định cao 900 (L-SHOT-10).

### So sánh trước / sau (cùng 1 file XD 5 artboard, trang top 1400px)
| Hạng mục | Trước | Sau |
|---|---|---|
| `xdspec --summary` | crash `KeyError: 'w'` (exit 1) | chạy hết (exit 0) |
| Opacity 9 blob gradient trang top | {1.0, 0.538} (sai cho 8/9) | {0.206, 0.234, 0.328, 0.538} = đúng XD |
| Texts / số shape trong spec.json | 1901 shape | giống hệt (texts bằng nhau, 1901 shape) |
| `shot.py --vp pc=1400x675` | `ValueError` | chụp được; pixeldiff PC: height_diff 2px, max Δ 5px |
| `shot.py --vp pc=1400` (KV 100vh, cao 900) | KV cao 870 ≠ design 645 | không đổi (giữ hành vi cũ) |

### Tương thích
- `xdspec.py`: field `opacity` giờ là opacity hiệu dụng (đã nhân group) — giá trị chỉ khác ở shape nằm trong group
  có opacity < 1; field mới chỉ thêm, không bỏ field cũ.
- `shot.py`: `--vp name=width` chạy như cũ (cao 900).

## [1.5.0] — 2026-10-23 — Semantic HTML: quy tắc + kiểm tra tự động trong audit.py

### Thay đổi
- `scripts/audit.py`: thêm kiểm tra tĩnh semantic — W `SEM-H1-OUTSIDE-MAIN`, `SEM-NO-H1`, `SEM-NO-MAIN`,
  `SEM-SECTION-NOHEAD`, `SEM-ARIA-GENERIC`, `SEM-SMALL-STYLE`, `FORM-LABEL`, `SOURCE-SIZE` (so tỉ lệ file ảnh
  `<source>` với `<img>`, cần Pillow); I `SEM-TH-SCOPE`, `FORM-AUTOCOMPLETE`.
- `SKILL.md` bước 5: checklist "Semantic HTML"; bước 6: mã SEM-*/FORM-*/SOURCE-SIZE phải sửa hoặc nêu lý do.
- `references/lessons.md`: L-HTML-07 [!!], L-HTML-08 [!], L-HTML-09 [!], L-HTML-10.

### Lý do
- Sau khi giao 1 LP, người dùng yêu cầu kiểm tra semantic/SEO: tìm thấy h1 (KV) ngoài `<main>`, `<small>` dùng để
  thu nhỏ chữ trong h1, `<section>` không heading, `aria-label` trên `div` thường, `th` thiếu scope, form thiếu
  autocomplete, và ảnh SP trong `<picture>` khác tỉ lệ nhưng `<source>` không có width/height (CLS ở SP).
  audit cũ không bắt được lỗi nào trong số này. Người dùng cũng muốn bỏ width/height của img vì "rườm rà" →
  ghi rõ lý do giữ (L-HTML-09).

### So sánh trước / sau (cùng 1 trang LP, `--static-only`)
| Hạng mục | Trước | Sau |
|---|---|---|
| audit cũ trên markup trước khi sửa semantic | W=0 (không phát hiện) | — |
| audit mới trên markup trước khi sửa | — | W=9 (1 ARIA-GENERIC, 1 H1-OUTSIDE-MAIN, 1 SMALL-STYLE, 1 SECTION-NOHEAD, 5 SOURCE-SIZE), I +15 (TH-SCOPE, AUTOCOMPLETE) |
| audit mới trên markup đã sửa | — | W=0 |
| Chiều cao ảnh SP trước/sau khi load (5 ảnh picture) | lệch theo tỉ lệ PC | bằng nhau (330/253/240/239/356) |
| Fixture form 4 field (label bọc / for=id / không label / aria-label) | — | chỉ field không label bị báo |

### Tương thích
- Mã cũ và exit code giữ nguyên; kiểm tra mới chỉ ở mức W/I nên không làm exit 1. Không có Pillow thì bỏ qua SOURCE-SIZE.

---

## [1.4.0] — 2026-10-22 — Lấy spec từ file XD (xdspec.py / xdcmp.py) thay vì đo ảnh

### Thay đổi
- Thêm `scripts/xdspec.py`: đọc .xd (zip JSON) → artboard, text (family/weight/size/ls/lh/màu/vị trí theo từng đoạn),
  shape (rect/line: nền, viền, dash, bo góc, gradient + hướng, blend, background blur, drop shadow); `--summary` in bảng tổng hợp.
- Thêm `scripts/xdcmp.py`: render trang, ghép đoạn chữ XD ↔ DOM (chữ + vị trí gần nhất), báo lệch size/weight/ls/lh/màu.
- `SKILL.md`: thêm bước 0b (hỏi file nguồn; có .xd thì dùng spec, ảnh chỉ để xem/so sánh).
- `references/lessons.md`: L-MEAS-11 [!!], L-MEAS-12, L-CSS-16, L-JS-06.

### Lý do
- Người dùng kiểm bằng PerfectPixel thấy font-size lệch 1–2px nhiều chỗ. Có file XD nhưng skill chỉ đo ảnh JPG: chọn nhầm
  (size, ls) cùng độ rộng; màu chữ/viền đo từ JPG sai (#222933/#2c4c72 thay vì #1e293b/#0055b8); bỏ sót blend 乗算, blur,
  shadow, gradient chéo; bỏ sót artboard 「フッター｜開いた時」.

### So sánh trước / sau (trang top, PC/SP/modal/menu)
- Thuộc tính chữ lệch so với XD: trước 146 (PC 49, SP 44, modal 20, menu 33) → sau 0 (còn lại chỉ là ghép nhầm cặp chữ trong ảnh).
- Màu chữ lệch: trước ~120 phần tử → sau 0. Shape (nền/viền/bo góc) lệch: trước 67 (PC) → sau 0 thật.
- Vị trí khối so với rect XD: lệch cục bộ PC ≤ ±2px, SP ≤ ±3px (trước: tới −21px PC, +72px SP).

### Tương thích
- Script mới, không đổi script cũ.

---

## [1.3.2] — 2026-10-22 — Bài học: không tự thêm mixin ngoài template

### Thay đổi
- `references/lessons.md`: thêm L-CSS-15 [!] — chỉ dùng mixin/hàm có sẵn; cách refactor an toàn (so computed style trước/sau).

### Lý do
- Người dùng chỉ ra: mixin `fs()` tự thêm (gộp `rem()` + `rem-tb()`) không có trong template.

### So sánh trước / sau
- Refactor 76 chỗ `@include fs()` → `rem()` + `rem-tb()` trong khối `@media` sẵn có: 0/1804 phần tử đổi font-size/line-height,
  chiều cao trang không đổi (PC/SP, 2 trang).

### Tương thích
- Chỉ thêm tài liệu.

---

## [1.3.1] — 2026-10-22 — Bài học: không ghi đè asset người dùng; texture/mask trang trí

### Thay đổi
- `references/lessons.md`: thêm L-FLOW-10 [!!] (kiểm tra file tồn tại/mtime trước khi ghi asset), L-IMG-06 [!] (texture
  cover + transform trong pseudo-element; mask tách bằng ngưỡng phải lấp lỗ; kiểm tra 1920/2560 và nhiều frame animation).

### Lý do
- Người dùng chỉ ra: texture キラキラ bản sạch họ đặt vào bị ghi đè; ribbon キラキラ bị dẹt ở màn rộng và lộ trắng khi chuyển
  động. Tự phát hiện khi kiểm tra: mask tách từ ảnh có lỗ ở chỗ texture gần trắng.

### So sánh trước / sau
- Sau sửa: 1280/1920/2560 × 3 thời điểm animation — không méo, không lộ trắng, không lỗ (kiểm tra bằng ảnh chụp).

### Tương thích
- Chỉ thêm tài liệu.

---

## [1.3.0] — 2026-10-22 — Bước 0 bắt buộc kiểm tra JS có sẵn trong template; lỗi nhiều instance module

### Thay đổi
- `SKILL.md` bước 0: thêm mục "JS có sẵn" — liệt kê `js/module`, `js/plugin`, cách `parts.html` gọi, map tương tác → module.
- `references/lessons.md`: nâng L-JS-04 lên [!!] (ví dụ thực tế tab/accordion tự viết), thêm L-JS-05 [!] (module gọi nhiều
  instance → bind click toàn cục, cuộn trang/xoá trạng thái nhóm khác; cách test bằng scrollY).

### Lý do
- Người dùng chỉ ra SAU khi giao: tab (お知らせ, コラム) và accordion (menu SP, footer) viết mới trong `common.js` trong khi
  template có `module/tab.js`, `module/jquery.accordion.js`. Khi chuyển sang `tab.js` phát hiện thêm: 2 nhóm tab → bấm tab
  nhóm này làm trang cuộn 391px (instance nhóm kia xử lý click), cùng lỗi có trong trang parts mẫu của template.

### So sánh trước / sau
- Trước: ~40 dòng JS tab/accordion tự viết. Sau: dùng module có sẵn; bấm tab không còn cuộn (scrollY trước = sau ở cả trang
  top và parts), không lỗi JS.

### Tương thích
- Chỉ thêm tài liệu/quy tắc; không đổi script.

---

## [1.2.0] — 2026-10-22 — Bài học: text-shadow vs ảnh, không inpaint ảnh tạm, semantic card link, rem() r4, trang trí full-width

### Thay đổi
- `references/lessons.md`: thêm L-MEAS-08 [!!] (quầng tối quanh chữ = text-shadow), L-MEAS-09 [!] (so độ dày nét / weight
  của chữ số trang trí), L-MEAS-10 [!] (fit font-size bằng render thử, tiêu chí độ rộng cả dòng).
- `references/lessons.md`: thêm L-CSS-11 (bo góc vạch trang trí nhỏ), L-CSS-12 (palt của core), L-CSS-13 (tab đổi
  height gây giật → clip-path), L-CSS-14 [!!] (`rem()` r4: thiếu px → CSS lỗi; SP phải `rem-tb`).
- `references/lessons.md`: thêm L-RESP-08 (trang trí full-width bị cắt ở ≥1900), L-RESP-09 (SVG tự vẽ méo → asset gốc,
  giữ tỉ lệ), L-HTML-06 (`<a>` bọc div/p → `.hover-all`), L-IMG-05 [!!] (không inpaint/làm mờ ảnh tạm).
- `SKILL.md` bước 4, 5: thêm quy tắc không inpaint, text-shadow, asset trang trí gốc, semantic card link, bo góc nhỏ.

### Lý do
- Người dùng chỉ ra SAU khi giao trang top (ảnh PC/SP dạng JPG/PNG tĩnh): (1) chữ KV có text-shadow nhưng bị hiểu là
  nền ảnh, ảnh tạm được "xoá chữ" bằng làm mờ → mảng mờ ở KV/nền section/ảnh card; (2) vạch trang trí trên thẻ thiếu
  bo góc; (3) dải trang trí vẽ lại bằng SVG `preserveAspectRatio=none` bị méo và lệch, ở ≥1900px bị cắt một nửa;
  (4) card link `<a>` bọc `div`; (5) chữ số viền để weight 300, design bold (vòng fit chỉ thử size/ls);
  (6) tab đổi chiều cao khi click gây giật.
- Tự phát hiện trong cùng phiên: palt của core làm co kana; `rem()` co 1/6 ở SP; `rem(20)` thiếu px → ~190 dòng CSS
  không hợp lệ trong template.

### So sánh trước / sau
- Trước: 6 lỗi trên do người dùng phát hiện sau khi giao. Sau: chưa đo (cần lần chạy tiếp theo để thống kê bằng
  `metrics.py report`).

### Tương thích
- Chỉ thêm tài liệu/quy tắc; không đổi script, lệnh cũ chạy như trước.

---

## [1.1.1] — 2026-10-21 — Bài học: tên class trùng component dùng chung; phân loại mục đích từng ảnh

### Thay đổi
- `references/lessons.md`: thêm L-CSS-10 [!] — grep tên class ở cấp gốc trước khi dùng; đo x/w + `--styles` cho
  phần tử nhỏ (thẻ, nhãn, nút) bằng `rects.py`.
- `references/lessons.md`: thêm L-FLOW-09 [!!] — lập bảng mục đích của MỌI ảnh nhận được (code / tham khảo
  trạng thái: 追従, hover, accordion, animation, 表示) và điểm khác so với ảnh chính.
- `SKILL.md` bước 1: thêm bước "Phân loại từng ảnh nhận được" trước khi đọc nội dung.

### Lý do
- Lỗi phát hiện SAU khi giao (người dùng chỉ ra): thẻ "STEP1–4" trong 1 khối đặt class `.tag`, trùng component
  `.tag` của theme (`width: 130px; font-weight: bold`) → thẻ rộng 130px thay vì 76px, chữ đậm thay vì 500.
  Vòng so sánh trước đó chỉ đo vị trí/chiều cao khối lớn (y, h), không đo x/w của phần tử nhỏ nên không bắt được.
- Lỗi thứ 2 phát hiện SAU khi giao (người dùng chỉ ra): người dùng gửi 2 ảnh — 1 design full-page và 1 ảnh
  crop 1 màn hình. Ảnh crop được coi là "ảnh cắt của design chính" nên bỏ sót thanh nút 追従 cố định ở đáy màn hình
  (3 nút, nút thứ 3 「ふるさと納税で寄付する」 chỉ có trong ảnh đó). Quy trình cũ không có bước xác định mục đích
  của từng ảnh.
- Khi kiểm tra lại cùng khối còn thấy thêm: tiêu đề cạnh thẻ letter-spacing .1em (design .05em, dòng dài hơn
  21px) và vạch ngăn bên trong #e6e6e6 (design ≈ #efefef) — cũng là lỗi chỉ thấy khi đo phần tử nhỏ/màu.

### So sánh trước / sau
| Hạng mục | Trước | Sau |
|---|---|---|
| Thẻ STEP (design 76×30) | 130×30 (Δw +54), bold | 76×30 (Δw 0) ×4 thẻ, weight 500 |
| Tiêu đề cạnh thẻ, x kết thúc dòng (design 760) | 781 (+21) | 761 (+1) |
| Màu vạch ngăn trong accordion / FAQ (design ≈ #efefef) | #e6e6e6 | #efefef |
| Bài học về trùng tên class | không có | L-CSS-10, kèm cách kiểm tra bằng `rects.py` |
| Thanh nút 追従 (chỉ có trong ảnh tham khảo) | 2 nút, thiếu 「ふるさと納税で寄付する」 | 3 nút 420×69 tại x 70/510/950 (ảnh: 420×70 tại 67/507/947) |
| Bước phân loại ảnh trong quy trình | không có | SKILL.md bước 1 + L-FLOW-09 |

File (so với `v1.1.0`): `references/lessons.md` +2 dòng, `SKILL.md` +5 dòng, `CHANGELOG.md`.

### Tương thích
- Chỉ thêm tài liệu; không đổi script.

---

## [1.1.0] — 2026-10-21 — Tải trang bền vững, so sánh theo khối DOM, audit tách lỗi bên thứ 3, changelog

### Thay đổi
- Thêm `scripts/_page.py`: hàm mở trang dùng chung — chờ `networkidle` có giới hạn (`--settle`, mặc định
  8000ms) rồi tiếp tục với DOM đã sẵn sàng, luôn chờ `document.fonts.ready`.
- `shot.py`: dùng `_page.open_page` thay cho `goto()` + `wait_for_load_state('networkidle')` không giới hạn;
  chờ font lần nữa sau khi cuộn; thêm `--settle`.
- `audit.py`: dùng `_page.open_page`; lỗi console/mạng của tài nguyên KHÁC domain trang chuyển từ E sang W
  với hậu tố `-EXT`; tải chậm báo `I LOAD-SLOW` thay vì `E LOAD`; thêm `--strict-external`, `--settle`.
- Thêm `scripts/rects.py`: so tọa độ DOM từng khối với số đo design, căn theo khối mốc; cột `Δloc` chỉ ra lỗi
  phát sinh giữa 2 khối; `--styles` in font-size / weight / line-height / letter-spacing / màu; exit 1 khi vượt `--tol`.
- Thêm `scripts/rowcmp.py`: so từng dòng mực trong 1 khối design ↔ render, tự dò lệch dọc; báo lệch dọc cục bộ,
  x kết thúc dòng, chiều cao nét, số dòng khác nhau.
- Thêm `scripts/changelog.py` + file này: bắt buộc ghi Thay đổi / Lý do / So sánh trước-sau cho mỗi lần cập nhật skill.
- `SKILL.md`: bước 0 thêm checklist dựng môi trường (server gốc, chạy ngoài sandbox, kiểm tra compile CSS tái tạo
  đúng file cũ, xác định phạm vi phần dùng chung); bước 6 thêm nhánh dùng `rects.py`/`rowcmp.py` khi phần ngoài
  phạm vi khác design, và quy tắc gom lỗi rồi sửa 1 lần; mô tả audit `-EXT`; mục "Cập nhật chính skill".
- `references/lessons.md`: thêm L-SHOT-06, L-SHOT-07, L-SHOT-08, L-SHOT-09, L-MEAS-07.

### Lý do
- Một lần code trang con (PC 1440, ~10 nghìn px, có GTM/analytics và icon font tải từ domain khác) mất ~1 giờ,
  trong đó hơn một nửa không phải code mà là dựng lại môi trường và công cụ đo:
  - `shot.py` chờ "load"/"networkidle" → timeout 30s do request analytics treo, script crash, phải chạy lại
    (lần chụp SP crash 3 lần liên tiếp) → L-SHOT-06.
  - Đo vị trí khi webfont chưa tải xong → xuống dòng khác, cả 1 vòng so sánh cho số sai → L-SHOT-07.
  - Header/KV dùng chung khác design → `pixeldiff` lệch dây chuyền từ đầu trang, không dùng được; phải tự viết
    script so tọa độ DOM và so dòng mực ngay trong phiên → L-SHOT-08 (nay thành `rects.py`, `rowcmp.py`).
  - Compile SCSS bằng sass trơn ra file khác hẳn bản cũ (thiếu autoprefixer) → mất thời gian điều tra → L-SHOT-09.
  - Ước lượng letter-spacing từ khoảng cách ký tự nhiễu, kết quả mâu thuẫn; cách đúng là so vị trí xuống dòng
    và x kết thúc dòng → L-MEAS-07.
  - `audit.py` báo 47 E, gần như toàn bộ là lỗi CORS/analytics của domain khác khi chạy localhost → 2 lỗi thật
    (ảnh CSS không tồn tại) bị chôn trong nhiễu.
- Người dùng yêu cầu mỗi lần cập nhật skill phải ghi rõ đã đổi gì, vì sao, và so sánh được trước/sau.

### So sánh trước / sau
Đo trên cùng 1 trang thực tế, cùng máy, cùng server local:

| Hạng mục | Trước (1.0.0) | Sau (1.1.0) |
|---|---|---|
| `shot.py` PC + SP trên trang có GTM | timeout 30s → crash; SP crash 3/3 lần | chạy xong lần đầu, 46s cho cả PC + SP, in cảnh báo "chưa networkidle" |
| `audit.py` (pc + sp) | E=47 (≈45 là CORS/analytics domain khác) | E=2 (2 lỗi thật: `url()` ảnh không tồn tại), W=25 gồm các mục `-EXT` |
| So vị trí khối khi header/KV khác design | `pixeldiff` drift từ đầu trang, không chỉ ra được khối lỗi; phải tự viết script trong phiên | `rects.py`: 23 khối, max \|Δloc\|=2px, drift cuối −4px, kết quả trùng với số đo tay |
| So dòng chữ trong 1 khối | tự viết script, phải đoán dy | `rowcmp.py` tự dò dy (khớp 4/4 dòng), chỉ ra letter-spacing sai qua x kết thúc dòng |
| Ghi lại thay đổi của skill | không có, chỉ có git log 1 dòng | `CHANGELOG.md` + `changelog.py draft/check` + pre-commit hook |
| Thời gian 1 trang con tương tự | ~39 phút đo bằng `metrics.py` (thực tế ~1 giờ) | chưa đo — cập nhật ở lần dùng tiếp theo |

File (so với `85ecdd8`):

| File | Loại | Dòng |
|---|---|---|
| `SKILL.md` | sửa | +17 / -1 (+ mục "Cập nhật chính skill") |
| `references/lessons.md` | sửa | +5 / -0 |
| `scripts/audit.py` | sửa | +40 / -9 |
| `scripts/shot.py` | sửa | +9 / -5 |
| `scripts/_page.py` | thêm | +33 |
| `scripts/rects.py` | thêm | +110 |
| `scripts/rowcmp.py` | thêm | +82 |
| `scripts/changelog.py` | thêm | +128 |
| `CHANGELOG.md` | thêm | — |
| `README.md`, `README.vi.md` | sửa | thêm dòng `rects.py`/`rowcmp.py`, `CHANGELOG.md` vào bảng thành phần; phiên bản → xem CHANGELOG |

CLI:
- `audit.py` thêm option: `--settle`, `--strict-external`
- `shot.py` thêm option: `--settle`
- Script mới: `rects.py`, `rowcmp.py`, `changelog.py`

### Tương thích
- Không bỏ option nào; mọi lệnh cũ chạy như trước.
- `shot.py`/`audit.py` vẫn chờ `networkidle` như cũ khi trang tải kịp; chỉ khác khi quá `--settle` ms (trước:
  crash, nay: đi tiếp + cảnh báo). Muốn chờ lâu hơn: `--settle 30000`.
- `audit.py`: muốn tính lỗi tài nguyên khác domain là E như trước → `--strict-external`. Lưu ý trang mở bằng
  `file://`: mọi tài nguyên http (kể cả font CDN) bị coi là khác domain.
- JSON của `audit.py` có thêm mã `*-EXT`, `LOAD-SLOW`; `metrics.py` vẫn đọc được (đếm theo mức E/W/I).

---

## [1.0.0] — 2026-10-16 — Phiên bản đầu

### Thay đổi
- Quy trình đo pixel → code → render → so sánh tự động → audit → self-review theo lessons → metrics.
- Script: `slice.py`, `sections.py`, `measure.py`, `colors.py`, `radius.py`, `crop_assets.py`, `shot.py`,
  `pixeldiff.py`, `compare.py`, `audit.py`, `metrics.py`.
- `references/measurement-rules.md`, `references/lessons.md`; README tiếng Nhật (chính) và tiếng Việt.

### Lý do
- Code từ ảnh design bằng ước lượng mắt sai 10–30% và không kiểm chứng được; cần quy trình đo + so sánh tự động.

### So sánh trước / sau
- Mốc khởi đầu — chưa có số liệu so sánh.

### Tương thích
- —
