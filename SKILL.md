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
| `compare.py` | ghép cạnh nhau 1 đoạn để xem bằng mắt |
| `audit.py` | **kiểm tra tự động** HTML/CSS/responsive/link/ảnh/font/JS, exit 1 nếu còn lỗi E |
| `metrics.py` | **ghi hiệu suất**: start/iter/fix/end/review/report |

Tài liệu: `references/measurement-rules.md` (công thức suy số đo) và `references/lessons.md` (bộ quy tắc
từ lỗi thực tế, có ID `L-xxx-nn` — dùng để ghi metrics và để self-review).

## Quy trình

### 0. Bắt đầu: điều tra project + mở run đo hiệu suất

```bash
python3 $P/metrics.py start --page index --source png --note "top PC+SP"   # chạy trong thư mục project
```

Đọc `references/lessons.md` (ít nhất các mục [!!]) và memory của project (quy ước riêng: thư mục ảnh,
font, thứ tự trang...).

Điều tra project: settings Sass, breakpoint, mixin, CSS base (`_core.scss`/reset: thường set
`p { line-height }`, `* { letter-spacing }`), class tiện ích (`.container`, `.pc`/`.tb`/`.sp`/`.xs`), JS
chung (slide menu, smooth scroll, accordion, inview), cách compile (Live Sass/koala/dart-sass, compressed
hay expanded — giữ đúng như CSS đang có), cách xem trang (file:// hay cần server vì path bắt đầu bằng `/`).
Code phải đọc như code xung quanh: đặt tên theo quy ước project (RSCSS: component 2 từ, element 1 từ,
variant `-xxx`), dùng biến màu có sẵn. Yêu cầu cấu trúc của người dùng ("tiêu đề dùng h2.top", "dùng
flex", "bỏ qua section X") tuân thủ tuyệt đối.

### 1. Xác định scale và cắt ảnh để xem

Ảnh full-page dài sẽ bị thu nhỏ khi Read → không đọc được chữ. Kiểm tra kích thước: PC rộng 2880 → @2x
của 1440; 1440 → @1x; SP 750 → @2x của 375 (lỗi sai scale: L-MEAS-02). Liệt kê **mọi** artboard/ảnh
design nhận được (L-FLOW-02) và xác nhận đó là bản mới nhất (L-SHOT-04).

```bash
python3 $P/slice.py design_pc.png crops/ --scale 2 --step 900
python3 $P/slice.py design_sp.png crops/ --scale 2 --step 2000 --grid 3
```

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

### 5. Viết HTML → SCSS

Thứ tự: HTML toàn trang → SCSS PC → SCSS SP trong cùng selector (`@media (max-width: $screen-tb)`). Khi
làm SP **không sửa code PC** và chú ý specificity (L-RESP-02); ẩn/hiện dùng `.pc/.sp` sẵn có (L-RESP-03).
Dùng giá trị đã đo, không làm tròn "cho đẹp" trừ khi lệch ≤ 2px. Không ép bằng `position:absolute`
(L-CSS-04). Chỗ số đo chỉ ra mối quan hệ (ảnh thẳng hàng tiêu đề) thì comment ngắn lý do.
Bẫy CSS hay gặp: xem lessons nhóm L-CSS (line-height của `p` bị base đè, letter-spacing không kế thừa,
header height ≠ design, absolute đè phần tử tĩnh, shadow drawer lọt mép).

### 6. Compile → render → so sánh tự động → kiểm tra → lặp

```bash
# compile theo cách project dùng, ví dụ:
npx -y sass --no-source-map --style=compressed sass/import.scss css/import.css
python3 $P/shot.py file:///abs/path/index.html --out $S/shots --vp pc=1440 --vp sp=375
python3 $P/pixeldiff.py design_pc.png $S/shots/pc.png --out $S/d_pc.png --json $S/pd_pc.json
python3 $P/pixeldiff.py design_sp.png $S/shots/sp.png --band 150 --out $S/d_sp.png --json $S/pd_sp.json
python3 $P/audit.py index.html --json $S/audit.json --quiet-info
python3 $P/metrics.py iter --pixeldiff $S/pd_pc.json --pixeldiff $S/pd_sp.json --audit $S/audit.json
```

Đọc kết quả:
- `shot.py` báo "còn N khối opacity:0" → xử lý trước (L-SHOT-01), nếu không mọi so sánh sai.
- `pixeldiff`: sửa từ dải có |Δ| > 3 **trên cùng** trước (lỗi chiều cao cục bộ nằm ngay trên dải đó; sửa
  nó kéo cả phần dưới về đúng). `dx` ≠ 0 → container/padding ngang sai. diff% cao nhưng Δ=0 → kích thước
  chữ/ảnh/màu sai → mở heatmap (Read ảnh `--out`, cắt nhỏ nếu dài) hoặc `compare.py`, rồi `measure.py`
  trên ảnh render (`--scale 1`) cùng vùng để tìm khối gây lệch. Dải "NỘI DUNG KHÁC HẲN" = thiếu khối, ảnh
  khác, slider → kiểm tra, dùng `--mask` nếu là ảnh placeholder/slider có chủ ý.
- `audit.py`: E phải = 0 (tràn ngang, link/ảnh hỏng, thẻ không đóng, id trùng, lỗi JS). W xem từng mục,
  cái nào đúng theo design thì giữ và nêu trong báo cáo.
- Sau khi làm SP, chạy lại `pixeldiff` PC để chắc PC không đổi.

Mỗi vòng sửa → chạy lại cả khối lệnh trên (mỗi lần `metrics.py iter` = 1 vòng). Mục tiêu đạt:
`max_abs_delta ≤ 3`, `final_drift ≤ 5`, `audit E = 0`, diff% giảm dần.
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

## Đo hiệu suất

`python3 $P/metrics.py report [--project X] [--csv out.csv]` → mỗi run: thời gian (phút), số vòng
render-sửa, số lần bị yêu cầu sửa (trước/sau giao), diff% vòng đầu → cuối, max Δ, lỗi audit còn lại,
điểm review; cuối bảng là các bài học bị vi phạm nhiều nhất. Dùng để biết skill cải thiện tới đâu và bài
học nào cần biến thành kiểm tra tự động. Dữ liệu chung mọi dự án ở `metrics/runs.jsonl` cạnh skill.
