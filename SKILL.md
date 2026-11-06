---
name: pixel-measure-design-coding
description: >-
  Code một trang (LP / trang top / trang con) từ ảnh design PC + SP (PNG/JPG export từ XD, Figma, PDF...)
  thành HTML/SCSS khớp gần như 100% bằng cách ĐO PIXEL bằng script (không ước lượng bằng mắt), cắt ảnh
  placeholder từ design, render bằng headless Chrome, so sánh TỰ ĐỘNG (pixeldiff: lệch chiều cao từng dải,
  % pixel khác, heatmap) và sửa đến khi lệch ≤ vài px; kèm kiểm tra tự động HTML/CSS/responsive/liên kết
  (audit), bộ quy tắc rút từ lỗi thực tế (lessons) và ghi đo hiệu suất (metrics: thời gian, số vòng sửa,
  số lần bị yêu cầu sửa, lỗi sau giao). Dùng khi người dùng gửi screenshot design và yêu cầu "code lại",
  "code giống design", "coding LP từ ảnh", "trùng khớp thiết kế", "pixel perfect"; khi cần "kiểm tra trang
  đã code", "check lỗi HTML/responsive/link", "so với design còn lệch chỗ nào"; hoặc khi người dùng yêu cầu
  sửa lỗi trên trang đã code bằng skill này. Áp dụng mọi dự án (s3/r4-template mirahos, nuweb, WordPress,
  HTML tĩnh) — skill lo đo và kiểm chứng, kết hợp với quy ước coding của project.
---

# Pixel-measure design coding

Mục tiêu: tái tạo design từ ảnh tĩnh với số đo **lấy từ pixel**, rồi **chứng minh** độ khớp bằng render +
so sánh tự động, và **không lặp lại lỗi cũ**. Nhìn ảnh bằng mắt chỉ để hiểu bố cục; mọi con số
(font-size, line-height, margin, width, màu, radius) đều phải đến từ script đo. Lý do: mắt người (và
model) ước lượng sai 10–30% với khoảng cách, script đo sai < 1px, và vòng render-so-sánh bắt được những
lỗi mà đọc code không thấy.

Script ở `scripts/` cạnh file này (gọi bằng đường dẫn tuyệt đối, ký hiệu `$P` dưới đây =
`~/.claude/skills/pixel-measure-design-coding/scripts`). Python + Pillow + numpy; `shot.py`/`audit.py`
dùng Playwright với Chrome của máy. Đơn vị tham số là **CSS px** — script tự nhân `--scale`.
File tạm (crop, shots, json) để trong scratchpad, không để trong project.

| Script | Việc |
|---|---|
| `slice.py` | cắt ảnh design dài thành đoạn để đọc |
| `sections.py` | ranh giới section + màu nền 2 mép |
| `measure.py` | dòng mực/khối trong 1 vùng → font-size, line-height, khoảng cách |
| `colors.py` / `radius.py` | màu điểm / màu chữ thật; bo góc |
| `crop_assets.py` | cắt ảnh placeholder từ design |
| `shot.py` | chụp render full-page nhiều viewport (tự cuộn kích hoạt fade-in, tắt animation, chờ font, dừng slider, `--hover`) |
| `pixeldiff.py` | **so sánh tự động** design↔render: drift/Δ từng dải, dx, diff%, heatmap, JSON |
| `rects.py` | so **tọa độ DOM từng khối** với số đo design: Δy, Δloc (lỗi phát sinh giữa 2 khối), Δh, `--styles` (font/lh/ls) — không bị nhiễu bởi header/KV dùng chung |
| `xdpos.py` | **vị trí dọc** khung + tâm chữ XD/Figma ↔ DOM: dy, `Δloc` (margin/padding sai ngay giữa 2 mục) — thứ `xdcmp` không kiểm |
| `inkcmp.py` | so **dòng mực top→top** trong 1 cột design↔render: `Δloc` = px margin cần sửa; không cần XD, xác nhận báo của xdpos |
| `refcheck.py` | dò vị trí từng **ảnh phụ** trong design chính, in dải nội dung CHỈ có ở ảnh phụ (追従, thanh cố định, trạng thái) — L-FLOW-09 |
| `rowcmp.py` | so **từng dòng mực** trong 1 khối design↔render (tự dò dy): lệch dọc, x kết thúc dòng (ls/font sai → xuống dòng khác) |
| `compare.py` | ghép cạnh nhau 1 đoạn để xem bằng mắt |
| `audit.py` | **kiểm tra tự động** HTML/CSS/responsive/link/ảnh/font/JS, exit 1 nếu còn lỗi E |
| `metrics.py` | **ghi hiệu suất**: start/iter/fix/end/review/report |
| `changelog.py` | chỉ dùng khi **sửa chính skill**: `draft` (khung changelog từ git diff), `check`, `install-hook` |

Tài liệu: `references/measurement-rules.md` (công thức suy số đo) và `references/lessons.md` (bộ quy tắc
từ lỗi thực tế, có ID `L-xxx-nn` — dùng để ghi metrics và để self-review).

## Quy trình

### 0. Bắt đầu: điều tra project + mở run đo hiệu suất

```bash
python3 $P/metrics.py start --page index --source png --note "top PC+SP"   # chạy trong thư mục project
```

**Dựng môi trường trước khi đo (5 phút đầu, đừng để giữa chừng mới phát hiện — L-SHOT-06/07):**
- Trang dùng path gốc `/data/...` → chạy server ở gốc project (`python3 -m http.server 8765`), không dùng file://.
- Playwright/Chrome cần mạng → chạy `shot.py`/`rects.py`/`audit.py` **ngoài sandbox** ngay từ lần đầu.
- Kiểm tra cách compile CSS **tái tạo đúng** file `.css` hiện có (compile ra file tạm rồi so kích thước/selector)
  TRƯỚC khi sửa SCSS. Live Sass Compile thường kèm autoprefixer → compile sass trơn sẽ khác hẳn.
- Phạm vi: header/KV/footer/khối dùng chung khác design → hỏi hoặc ghi lại, không chỉnh pixel phần đó.

Đọc `references/lessons.md` (ít nhất các mục [!!]) và memory của project (quy ước riêng: thư mục ảnh,
font, thứ tự trang...).

**JS có sẵn (L-JS-04 [!!]):** liệt kê `js/common.js`, `js/module/*.js`, `js/plugin/*` và xem `parts.html`/regulation
gọi chúng thế nào (markup, option, class trạng thái). Mọi tương tác trong design (tab, accordion, slider, modal,
switcher…) phải map sang module có sẵn trước; chỉ viết mới khi không có, và nêu lý do trong báo cáo.

Điều tra project: settings Sass, breakpoint, mixin, CSS base (`_core.scss`/reset: thường set
`p { line-height }`, `* { letter-spacing }`), class tiện ích (`.container`, `.pc`/`.tb`/`.sp`/`.xs`), JS
chung (slide menu, smooth scroll, accordion, inview), cách compile (Live Sass/koala/dart-sass, compressed
hay expanded — giữ đúng như CSS đang có), cách xem trang (file:// hay cần server vì path bắt đầu bằng `/`).
Code phải đọc như code xung quanh: đặt tên theo quy ước project (RSCSS: component 2 từ, element 1 từ,
variant `-xxx`), dùng biến màu có sẵn. Yêu cầu cấu trúc của người dùng ("tiêu đề dùng h2.top", "dùng
flex", "bỏ qua section X") tuân thủ tuyệt đối.

### 0b. Có file nguồn (.xd / Figma)? → lấy spec từ file, KHÔNG đo từ ảnh (L-MEAS-11 [!!])

Hỏi ngay từ đầu: có file XD/Figma không. Có `.xd` → `python3 $P/xdspec.py design.xd --list` (liệt kê MỌI artboard —
kể cả trạng thái phụ như 「フッター｜開いた時」, ホバー, モーダル) rồi `--out spec.json --summary`: font-size / weight /
letter-spacing (charSpacing/1000 em) / line-height / màu chữ theo từng đoạn, nền / viền / bo góc / gradient (hướng) /
blend / blur / shadow của shape. Viết CSS từ các số này; ảnh chỉ dùng để xem bố cục và so sánh render.
Sau khi code: `python3 $P/xdcmp.py URL spec.json --ab <artboard> --vp 1280x740` (ghép đoạn chữ ↔ DOM theo chữ + vị trí,
báo size/weight/ls/lh/màu lệch). Đặt chiều cao viewport sao cho KV cao bằng design để toạ độ khớp.
xdcmp **không kiểm vị trí** → chạy tiếp `python3 $P/xdpos.py URL spec.json --ab <artboard> --vp 1280x740`
(L-MEAS-15 [!!]): Δloc ≠ 0 = margin/padding ngay trên mục đó sai; xác nhận bằng `inkcmp.py` rồi sửa. Exit 0 mới qua.
Shape trong group có mask: chiều cao trong spec có thể lớn hơn phần hiển thị — đối chiếu ảnh trước khi dùng.
Trang trí mờ (blob, vòng tròn, lớp phủ): đọc mục "Trang trí bán trong suốt" — opacity đã gồm opacity của group cha;
1 group = 1 phần tử có nhiều lớp nền + `opacity`, và kiểm lớp chồng lấn giữa các section bằng màu pixel (L-CSS-17).

**Có link Figma (L-MEAS-14 [!!]):** KHÔNG lấy letter-spacing / line-height từ code của `get_design_context`
(`tracking-[0.96px]` là px đã nhân font-size — mất đơn vị %, làm tròn sai, sai khi SP đổi font-size). Lấy spec bằng
Plugin API: `python3 $P/figspec.py js <frameId> [--only texts|shapes]` → dán nguyên văn vào `use_figma` (đọc
`figma-use` trước; mỗi frame 1 lần gọi, `bytes` > ~60k thì tách `--only`) → lưu giá trị trả về thành
`raw_<frame>.json` → `python3 $P/figspec.py save raw_*.json --out spec.json --summary`. Viết `letter-spacing` theo
cột `ls` (em; Figma 6% = `.06em`), line-height theo `lh_raw` (`AUTO` = không có số, đo bằng render). Spec cùng định
dạng xdspec → kiểm bằng `xdcmp.py` như trên (`--ab` = tên frame Figma). `get_design_context` vẫn dùng cho cấu trúc,
asset, màu biến.

### 1. Xác định scale và cắt ảnh để xem

Ảnh full-page dài sẽ bị thu nhỏ khi Read → không đọc được chữ. Kiểm tra kích thước: PC rộng 2880 → @2x
của 1440; 1440 → @1x; SP 750 → @2x của 375 (lỗi sai scale: L-MEAS-02). Liệt kê **mọi** artboard/ảnh
design nhận được (L-FLOW-02) và xác nhận đó là bản mới nhất (L-SHOT-04).

```bash
python3 $P/slice.py design_pc.png crops/ --scale 2 --step 900
python3 $P/slice.py design_sp.png crops/ --scale 2 --step 2000 --grid 3
```

**Phân loại từng ảnh nhận được (L-FLOW-09):** chạy trước `python3 $P/refcheck.py design_pc.png ảnh_phụ1 ảnh_phụ2 --out $S/refcheck`
(exit 1 = có nội dung chỉ ở ảnh phụ, mở ảnh cắt trong `--out`), rồi với MỖI ảnh ghi mục đích — để code (design PC/SP) hay để tham khảo
trạng thái/hiển thị (追従イメージ / thanh cố định khi cuộn, hover, accordion mở, animation, popup) — và những gì
ảnh đó có mà ảnh chính KHÔNG có (so từng vùng, nhất là phần dính mép trên/dưới màn hình). Mọi điểm đó đều phải
code và kiểm chứng bằng ảnh chụp đúng trạng thái (cuộn tới vị trí, hover...).

Đọc lần lượt, ghi chép: danh sách section, nội dung chữ (gõ lại chính xác, kể cả 「」“”〜), vị trí
xuống dòng ở PC và SP (`<br class="pc">` / `<br class="sp">`), thứ tự khối thay đổi ở SP, phần tử có
hover/animation/slider. Chỗ mơ hồ (link đi đâu, có tương tác không) → hỏi trước (L-FLOW-05).

### 2. Đo khung trang

```bash
python3 $P/sections.py design_pc.png --scale 2      # ranh giới section + màu nền 2 mép
python3 $P/measure.py design_pc.png --scale 2 --box 100 1620 1340 2716 --thr 20
```

Ra: chiều cao mỗi section, nền gradient (màu trái ≠ phải), màu nền, heading và padding từng section.
Tìm **pattern lặp** (cùng padding-top/bottom, cùng khoảng heading→nội dung) → 1 rule chung.

### 3. Đo chi tiết từng khối

- Chữ: `measure.py` cho từng dòng → font-size, line-height, letter-spacing, khoảng cách đoạn
  (xem measurement-rules). Thu hẹp `--box` theo x để tách các khối chồng nhau.
- Lưới card/cột: `--cols` → width, gap.
- Màu: `colors.py --pt` cho nền/nút, `--dark` cho màu chữ thật. Không dùng opacity thay màu (L-MEAS-05).
- Bo góc: `radius.py` (bỏ góc có nền trắng trong ảnh — kết quả quá lớn).
- Oval/ellipse: đo x mép ở nhiều y rồi khớp phương trình (`border-radius: 330px / 50%`).
- Phần tử tràn container: ghi khoảng cách tới mép viewport → `calc((C - 100vw)/2 + Npx)` / `50vw`.

Ghi số đo vào ghi chú ngắn theo section trước khi viết code.

### 4. Ảnh placeholder

Project chưa có ảnh → cắt từ design (từ bản @2x để không mờ, L-IMG-01) bằng JSON toạ độ + `crop_assets.py`,
lưu đúng thư mục theo quy ước project (L-FLOW-04). Ảnh có chữ đè (KV) lấy từ bản SP nếu sạch. Icon nhiều
biến thể cắt riêng. Nói rõ với người dùng đây là ảnh tạm.
**Không inpaint / làm mờ để xoá chữ đè lên ảnh** (L-IMG-05): xoá nội dung đè (ẩn layer) trước khi xuất ảnh —
có file nguồn thì tự ẩn rồi export, chỉ có ảnh tĩnh thì xin ảnh sạch. Quầng tối quanh chữ là `text-shadow`
của chữ, không phải ảnh (L-MEAS-08). Hình trang trí (dải, sóng, キラキラ) xin asset gốc, giữ tỉ lệ (L-RESP-09).

### 5. Viết HTML → SCSS

Thứ tự: HTML toàn trang → SCSS PC → SCSS SP trong cùng selector (`@media (max-width: $screen-tb)`). Khi
làm SP **không sửa code PC** và chú ý specificity (L-RESP-02); ẩn/hiện dùng `.pc/.sp` sẵn có (L-RESP-03).
Dùng giá trị đã đo, không làm tròn "cho đẹp" trừ khi lệch ≤ 2px. Không ép bằng `position:absolute`
(L-CSS-04). Chỗ số đo chỉ ra mối quan hệ (ảnh thẳng hàng tiêu đề) thì comment ngắn lý do.
Bẫy CSS hay gặp: xem lessons nhóm L-CSS (line-height của `p` bị base đè, letter-spacing không kế thừa,
header height ≠ design, absolute đè phần tử tĩnh, shadow drawer lọt mép, palt của core, `rem()` ở SP,
tab đổi chiều cao gây giật). HTML: `<a>` chỉ chứa phrasing content — card link dùng `.hover-all`/stretched
link (L-HTML-06). Phần tử trang trí nhỏ kiểm tra bo góc (L-CSS-11).

**Semantic HTML (L-HTML-07〜10)** — chọn thẻ theo nghĩa, không theo hình dáng:
- Khung: `header` / `main` (chứa cả KV có `<h1>`) / `footer`; khối cố định phụ (CTA bên, nút 追従) là
  `<aside aria-label>`. Đúng 1 `<h1>`; mỗi `<section>` có heading (không có → `<div>`); h2→h3→h4 không nhảy cấp.
- Danh sách → `ul`/`ol` (các bước, timeline → `ol`); cặp nhãn–giá trị (募集要項) → `table` với
  `th scope="row"` hoặc `dl`; nhấn mạnh nghĩa → `em`/`strong`; chữ nhỏ trang trí → `span` (không `small`).
- `aria-label` chỉ đặt trên landmark/thẻ có role, không trên `div`/`span` thường; icon trang trí `aria-hidden="true"`.
- Ảnh: alt mô tả nội dung (ảnh biểu đồ ghi số liệu trong alt; ảnh trang trí `alt=""`); `<img>` và từng
  `<source>`: KHÔNG ghi width/height trong HTML (người dùng không muốn) — giữ chỗ bằng CSS (`aspect-ratio` cho ảnh
  `height:auto`, hoặc khung cố định); SVG tự xuất đặt width/height gốc = viewBox; kiểm: chặn ảnh → đo top các
  section → cho tải → chênh 0px (L-HTML-09).
- Form: mỗi field có `<label>` liên kết, `autocomplete` cho tên/email/điện thoại, `required` đúng field bắt buộc.
- Kiểm: `audit.py` (mã SEM-*/FORM-*/SOURCE-SIZE phải = 0 hoặc nêu lý do giữ) + in outline heading bằng DOM.

### 6. Compile → render → so sánh tự động → kiểm tra → lặp

```bash
# compile theo cách project dùng, ví dụ:
npx -y sass --no-source-map --style=compressed sass/import.scss css/import.css
python3 $P/shot.py file:///abs/path/index.html --out $S/shots --vp pc=1440 --vp sp=375   # KV 100vh: --vp pc=1440x<đáy KV> (L-SHOT-10)
python3 $P/pixeldiff.py design_pc.png $S/shots/pc.png --out $S/d_pc.png --json $S/pd_pc.json
python3 $P/pixeldiff.py design_sp.png $S/shots/sp.png --band 150 --out $S/d_sp.png --json $S/pd_sp.json
python3 $P/xdpos.py URL spec.json --ab <artboard_PC> --vp 1280x<đáy KV>        # có XD/Figma: phải exit 0
python3 $P/inkcmp.py design_pc.png $S/shots/pc.png --box Y0 Y1 X0 X1 --thr 150 # mỗi section, cột chữ chính
python3 $P/audit.py index.html --json $S/audit.json --quiet-info   # có spec: thêm --base URL --spec spec.json --ab "PC=1280x740" --ab "SP=375x740"
python3 $P/metrics.py iter --pixeldiff $S/pd_pc.json --pixeldiff $S/pd_sp.json --audit $S/audit.json
```

**Khi header/KV/phần dùng chung ngoài phạm vi khác design** (pixeldiff lệch dây chuyền từ đầu trang):
ghi tọa độ design của mọi khối chính vào `targets.json` (1 lần, bằng `measure.py`) rồi dùng
`rects.py URL targets.json` thay cho pixeldiff ở mỗi vòng — nhanh hơn (không chụp ảnh), căn theo khối mốc,
`Δloc` chỉ thẳng chỗ gây lệch. Dùng `rowcmp.py` cho khối có Δh ≠ 0 để thấy dòng nào lệch / xuống dòng khác.
Gom TẤT CẢ lỗi của 1 vòng rồi sửa 1 lần, không sửa từng chỗ rồi chụp lại.

**Khoảng cách trong section (L-SHOT-11 [!!]):** pixeldiff dải 200px và `final_drift` nhỏ KHÔNG chứng minh margin đúng —
lệch +5/-4 bù trừ nhau. Mỗi vòng: `xdpos.py` (có XD/Figma) liệt kê chỗ phát sinh lệch; với từng section chạy
`inkcmp.py --box` trên cột chữ chính (bỏ hình trang trí, khối "?" = dính hình khác → thu hẹp box). Sửa đúng
số px của `Δloc` vào margin/padding ngay trên khối báo, rồi đo lại.

Đọc kết quả:
- `shot.py` báo "còn N khối opacity:0" → xử lý trước (L-SHOT-01), nếu không mọi so sánh sai.
- `pixeldiff`: sửa từ dải có |Δ| > 3 **trên cùng** trước (lỗi chiều cao cục bộ nằm ngay trên dải đó; sửa
  nó kéo cả phần dưới về đúng). `dx` ≠ 0 → container/padding ngang sai. diff% cao nhưng Δ=0 → kích thước
  chữ/ảnh/màu sai → mở heatmap (Read ảnh `--out`, cắt nhỏ nếu dài) hoặc `compare.py`, rồi `measure.py`
  trên ảnh render (`--scale 1`) cùng vùng để tìm khối gây lệch. Dải "NỘI DUNG KHÁC HẲN" = thiếu khối, ảnh
  khác, slider → kiểm tra, dùng `--mask` nếu là ảnh placeholder/slider có chủ ý.
- `audit.py --spec`: E `XD-POS` = khung lệch vị trí so với XD/Figma (phải 0); W `XD-POS-TEXT` = chữ lệch (xác nhận bằng
  `inkcmp.py`, nhiễu font thì ghi lý do). W `CSS-CLASS-CLASH` = class element trùng component cấp gốc (L-CSS-10).
- `audit.py`: W mã SEM-*/FORM-*/SOURCE-SIZE (semantic) phải sửa hết hoặc nêu lý do giữ trong báo cáo.
- `audit.py`: E phải = 0 (tràn ngang, link/ảnh hỏng, thẻ không đóng, id trùng, lỗi JS). W xem từng mục,
  cái nào đúng theo design thì giữ và nêu trong báo cáo. Lỗi tài nguyên khác domain (GTM, font CDN bị CORS ở
  localhost) báo W `*-EXT`; cần coi là E thì `--strict-external`. E/W có sẵn từ trước (không do mình) → báo, không tự sửa.
- Sau khi làm SP, chạy lại `pixeldiff` PC để chắc PC không đổi.

Mỗi vòng sửa → chạy lại cả khối lệnh trên (mỗi lần `metrics.py iter` = 1 vòng). Mục tiêu đạt:
`max_abs_delta ≤ 3`, `final_drift ≤ 5`, **`xdpos.py` exit 0 (`--tol 2`), `inkcmp.py` Δloc ≤ 1 ở mọi section**,
`audit E = 0`, diff% giảm dần. Nền ảnh có overlay: so màu trung bình asset ↔ design trước (L-IMG-07).
Hover: `shot.py --hover ".selector"` chụp trạng thái hover để đối chiếu spec.

### 7. Self-review theo lessons

Đi qua các mục [!!]/[!] trong `references/lessons.md` liên quan tới trang này, đối chiếu thực tế (không
tự khẳng định chủ quan — L-FLOW-01). Lỗi tự phát hiện và sửa ở bước này ghi
`metrics.py fix --by self --lesson <ID>`.

### 8. Báo cáo + kết thúc run

Liệt kê: file đã sửa/tạo (link), cách đáp ứng từng yêu cầu riêng, **bảng số** (pixeldiff PC/SP: max Δ,
diff%, chiều cao; audit: E/W còn lại và lý do giữ), việc người dùng cần làm (thay ảnh placeholder, link
`#`, action form, phần design không có mà mình tự quyết). Rồi:

```bash
python3 $P/metrics.py end --deliver
```

## Khi người dùng yêu cầu sửa (sau khi đã giao)

1. Đo lại để xác nhận lỗi (không sửa theo phỏng đoán).
2. Tìm ID trong `lessons.md`; chưa có → thêm bài học mới theo mẫu cuối file (lỗi chung mọi dự án), hoặc
   ghi memory project (lỗi chỉ đúng dự án này).
3. Sửa, rồi grep toàn project sửa cùng pattern (L-FLOW-03).
4. `metrics.py fix --by user --after --lesson <ID> --note "..."` (bỏ `--after` nếu chưa giao). Nếu script
   báo bài học đã lặp ≥ 2 lần → nâng mức trong lessons.md và cân nhắc thêm kiểm tra vào `audit.py`.
5. Chạy lại bước 6, báo số trước/sau. Nếu người dùng cho điểm/nhận xét chất lượng:
   `metrics.py review --score N`.

## Cập nhật chính skill (script / SKILL.md / references / README)

Mỗi lần sửa skill — kể cả thêm 1 bài học — BẮT BUỘC thêm 1 mục vào `CHANGELOG.md` (mới nhất ở trên), gồm:
**Thay đổi** (làm gì) · **Lý do** (vấn đề thực tế nào, mã bài học) · **So sánh trước / sau** (hành vi + số liệu
đo được: thời gian, E/W audit, độ lệch px...; chưa đo thì ghi "chưa đo") · **Tương thích** (lệnh cũ còn chạy
không, option giữ hành vi cũ).

1. Trước khi sửa: đo số liệu "trước" trên 1 trang thật (để có cột Trước).
2. Sửa, rồi chạy lại cùng lệnh để có cột Sau.
3. `python3 scripts/changelog.py draft` → khung đã điền danh sách file / option CLI / mã bài học thay đổi;
   tự điền Lý do và bảng so sánh; nâng phiên bản (MAJOR bỏ/đổi hành vi cũ, MINOR thêm script/option/quy trình,
   PATCH sửa lỗi/chữ).
4. `python3 scripts/changelog.py check` (pre-commit hook chạy tự động nếu đã `install-hook`) → commit.

Không ghi tên khách hàng / dự án / đường dẫn máy vào CHANGELOG (repo được chia sẻ).

## Đo hiệu suất

`python3 $P/metrics.py report [--project X] [--csv out.csv]` → mỗi run: thời gian (phút), số vòng
render-sửa, số lần bị yêu cầu sửa (trước/sau giao), diff% vòng đầu → cuối, max Δ, lỗi audit còn lại,
điểm review; cuối bảng là các bài học bị vi phạm nhiều nhất. Dùng để biết skill cải thiện tới đâu và bài
học nào cần biến thành kiểm tra tự động. Dữ liệu chung mọi dự án ở `metrics/runs.jsonl` cạnh skill.
