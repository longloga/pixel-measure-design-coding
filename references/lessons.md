# Bộ quy tắc rút từ lỗi thực tế (lessons)

File này **lớn dần theo thời gian**. Mỗi lần Claude Code làm sai và người dùng phải yêu cầu sửa (hoặc tự phát
hiện khi review), ghi lỗi bằng `metrics.py fix --lesson <ID>`; nếu lỗi chưa có ID phù hợp → thêm mục mới
vào đây theo mẫu ở cuối file. `metrics.py report` cho biết bài học nào bị vi phạm nhiều nhất → đưa lên mức
**[!!]** hoặc biến thành kiểm tra tự động trong `audit.py`.

Mức độ: **[!!]** đã gây làm lại lớn / lặp nhiều lần · **[!]** quan trọng · không đánh dấu = nên nhớ.
Cột "Tự động" = mã lỗi `audit.py` / chỉ số `pixeldiff.py` bắt được lỗi này (nếu có).

Đọc file này ở bước 0 (trước khi code) và bước 7 (self-review). Không cần thuộc hết — dùng mục lục để
dò nhóm liên quan đến việc đang làm.

---

## 1. Quy trình & phạm vi (L-FLOW)

| ID | Mức | Lỗi đã xảy ra → Quy tắc | Tự động |
|---|---|---|---|
| L-FLOW-01 | [!!] | Tự tuyên bố "đã khớp design / không có vấn đề" mà không đo. → Mọi kết luận phải kèm số: bảng `pixeldiff` (max Δ, diff%), số đo từng thuộc tính so với design. Cấm tự đánh giá chủ quan. | pixeldiff |
| L-FLOW-02 | [!!] | Tự ý bỏ qua artboard/section "trông như bản tham khảo". → Liệt kê TOÀN BỘ artboard/section trước khi code, hỏi người dùng nếu nghi ngờ, không tự loại. | |
| L-FLOW-03 | [!!] | Bị chỉ ra 1 lỗi thì chỉ sửa đúng 1 chỗ đó. → Sau mỗi yêu cầu sửa: grep toàn project tìm cùng pattern (cùng class, cùng kiểu markup, cùng trang khác) và sửa hết, báo lại danh sách chỗ đã sửa. | |
| L-FLOW-04 | [!!] | Đổi/thêm file, thư mục, tên file SCSS/JS khác cấu trúc project. → Viết vào file sẵn có theo quy ước; cần file mới thì hỏi trước. Thư mục ảnh theo quy ước project (r4: `data/media/<theme>/page/<page>/`, `layout/`, `common/`). | |
| L-FLOW-05 | [!] | Spec mơ hồ (link đi đâu, có tab/accordion không, text khi rỗng) → tự đoán và code. → Hỏi lại với ví dụ cụ thể trước khi code phần đó; phần không hỏi được thì ghi rõ trong báo cáo là "tự quyết". | |
| L-FLOW-06 | [!] | Tự đổi text, vị trí xuống dòng, bỏ ảnh, "đơn giản hoá cho dễ code". → Gõ lại text đúng 100% (kể cả 「」“”〜, khoảng trắng full-width), giữ chỗ xuống dòng bằng `<br class="pc">`/`<br class="sp">`. | |
| L-FLOW-07 | | Task dài không báo tiến độ. → Báo ngắn sau mỗi section/mỗi vòng so sánh. | |
| L-FLOW-08 | [!] | "Đã sửa mà không thấy thay đổi" → mất thời gian sửa code tiếp. → Kiểm tra trước: CSS đã compile chưa (timestamp file .css), cache trình duyệt, đúng file được link, upload đủ chưa. | |
| L-FLOW-09 | [!!] | Coi ảnh phụ người dùng gửi kèm chỉ là "ảnh cắt của design chính" → bỏ sót nội dung chỉ có trong ảnh đó (đã gặp thực tế: ảnh crop 1 màn hình có thanh nút 追従 cố định ở đáy với 3 nút, design full-page không thể hiện; chỉ làm 2 nút, người dùng phát hiện sau khi giao). → Trước khi code, lập bảng MỌI ảnh: mục đích (code / tham khảo trạng thái: 追従・hover・mở accordion・animation・表示 khi cuộn) và điểm KHÁC so với ảnh chính (so từng vùng, nhất là mép trên/dưới viewport). Ảnh tham khảo cũng phải được hiện thực và kiểm chứng (chụp đúng trạng thái: cuộn, hover...). **Lặp 2 lần** → `refcheck.py` dò vị trí ảnh phụ trong design chính và in dải chỉ có ở ảnh phụ (đánh dấu mép trên/dưới = thanh cố định). | **refcheck.py** |
| L-FLOW-10 | [!!] | Ghi đè file asset người dùng đã đặt vào project (texture キラキラ bản sạch) bằng file tự tạo, không kiểm tra trước; project không có git nên mất bản của người dùng. → Trước khi ghi bất kỳ file ảnh/asset nào: `ls -la` xem đã tồn tại chưa, mtime có mới hơn lần mình ghi trước không; có thì KHÔNG ghi đè — ghi tên khác hoặc hỏi. | |

## 2. Đo & suy số (L-MEAS) — chi tiết công thức ở `measurement-rules.md`

| ID | Mức | Lỗi → Quy tắc | Tự động |
|---|---|---|---|
| L-MEAS-01 | [!!] | Ước lượng khoảng cách bằng mắt (sai 10–30%). → Mọi số đo lấy từ `measure.py`/`colors.py`/`radius.py`. | |
| L-MEAS-02 | [!] | Sai scale (@1x tưởng @2x) → mọi số gấp đôi/nửa. → Kiểm tra `rộng ảnh / rộng viewport design` trước. `pixeldiff.py` tự suy `dscale`. | pixeldiff |
| L-MEAS-03 | [!] | Lấy margin từ mép mực chữ thay vì mép box → lệch (line-height − cao mực)/2 mỗi bên. | |
| L-MEAS-04 | | Đo font từ dòng chỉ có kana/số → font-size nhỏ hơn thật. → Đo dòng có kanji. | |
| L-MEAS-05 | [!] | Dùng opacity/filter để "làm nhạt" thay vì mã màu thật. → Lấy mã màu bằng `colors.py --pt/--dark`. | |
| L-MEAS-06 | | Không tìm pattern lặp → mỗi section 1 padding riêng lệch nhau vài px. → So offset heading với đầu section ở nhiều section, gom thành 1 rule. | |
| L-MEAS-07 | | Suy letter-spacing từ khoảng cách giữa các ký tự (pitch) → nhiễu, kết quả mâu thuẫn, mất thời gian (đã gặp thực tế). → Code với giá trị base của project trước, rồi `rowcmp.py` so **x kết thúc dòng và vị trí xuống dòng**: dòng render dài hơn/xuống sớm hơn → ls (hoặc font) lớn hơn design. Design có thể dùng ls khác nhau giữa các khối (vd mô tả STEP/list = 0, body = .05em). | rowcmp.py Δx1 |
| L-MEAS-08 | [!!] | Vùng tối/mờ quanh chữ trắng trên ảnh (KV) bị hiểu là một phần của ảnh nền → cắt ảnh rồi "xoá chữ" bằng cách làm mờ, chữ thì không có bóng (người dùng chỉ ra sau khi giao). → Quầng tối bám theo hình chữ là `text-shadow` của chữ: code `text-shadow` (màu bằng var/color-mix), không tính vào ảnh nền. Phân biệt: quầng đi theo từng nét chữ = text-shadow; mảng tối hình chữ nhật = lớp overlay. | |
| L-MEAS-09 | [!] | Chữ số trang trí viền (outline `-webkit-text-stroke`) để weight 300 trong khi design là bold — vòng so sánh chỉ so vị trí/kích thước nên không bắt được (người dùng chỉ ra). → Với chữ lớn (≥40px) so cả **độ dày nét** (zoom 3–4x cạnh nhau); khi fit font-size bằng render thử phải thử cả weight (300/400/500/700), không chỉ size + letter-spacing. | |
| L-MEAS-10 | [!] | Ước lượng font-size từ chiều cao mực + pitch ra 16px/0.08em, thực tế design là 17px/0.06em (lệch xuống dòng ở nhiều khối). → Fit bằng cách render thử nhiều (size, letter-spacing, weight) cùng chuỗi chữ rồi so **độ rộng mực cả dòng** với design (rộng là tiêu chí chính, chiều cao chỉ để loại trừ ±1px). Chuỗi dài (≥20 ký tự) mới tin được. | |
| L-MEAS-11 | [!!] | Đo font/màu/khoảng cách từ ảnh JPG trong khi người dùng có file XD → ~100 thuộc tính lệch 1–2px (17px+0.06em thay vì 18px+0; Shippori 500 thay vì 600; màu chữ #222933 thay vì #1e293b do nhiễu JPG; viền #2c4c72 thay vì #0055b8) — người dùng phát hiện bằng PerfectPixel. → Bước 0b: hỏi file nguồn; có .xd thì `xdspec.py` lấy spec, `xdcmp.py` kiểm chứng. Ảnh nén JPG làm lệch màu và dày nét — không lấy mã màu/viền/độ dày từ JPG khi có file nguồn. **Lặp 3 lần** → `metrics.py start --source png` tự liệt kê file .xd/.fig (dự án + Desktop/Downloads 14 ngày) và yêu cầu hỏi người dùng. | **metrics.py start**, xdspec.py, xdcmp.py |
| L-MEAS-13 | [!!] | Báo "đạt" vì pixeldiff max Δ ≤ 5 / tổng chiều cao khớp, trong khi từng phần tử vẫn lệch 2–6px (logo nhỏ 4px, hàng header thấp 6px, tag thấp 6px, khoảng dưới thẻ, khoảng chữ trong thẻ) và 1 màu sai do nhìn bằng mắt (tag cam thay vì xanh) — người dùng kiểm bằng thông số XD và chỉ ra hàng loạt. pixeldiff theo dải bù trừ lẫn nhau nên không thấy lệch cục bộ. → Có XD thì sau MỖI vòng: (1) `xdcmp.py` cho mọi artboard (size/weight/ls/màu phải = 0 lệch, chỉ chấp nhận lh "auto" của chữ 1 dòng); (2) so rect DOM với rect shape trong `spec.json` cho mọi khối có nền/viền (thẻ, nút, tag, khung) — Δ ≤ 1px; (3) đo ink `measure.py` cho logo/icon/chữ trong header. Màu luôn lấy từ spec hoặc `colors.py --dark`, không đọc bằng mắt. **Lặp lại lần 2** (trang dài 10k px: 8 section lệch 2–13px — label↔heading, padding trong card, banner, card tuyển dụng, chữ trong card link, footer — trong khi pixeldiff `final_drift` chỉ 8px; người dùng phát hiện bằng ảnh design): bước (2) làm tay nên bị bỏ qua. → Nay BẮT BUỘC `xdpos.py` (khung + tâm chữ XD ↔ DOM, Δloc) phải exit 0 với `--tol 2`, mỗi chỗ báo xác nhận bằng `inkcmp.py` trên ảnh design (L-MEAS-15, L-SHOT-11). | xdcmp.py, **xdpos.py**, **inkcmp.py** |
| L-MEAS-12 | [!] | Hai cặp (font-size, letter-spacing) khác nhau cho cùng độ rộng dòng (17px+0.06em ≈ 18px+0) → fit từ ảnh chọn nhầm. → Không có file nguồn: ưu tiên letter-spacing 0 / giá trị tròn của design system, hỏi người dùng khi hai phương án sát nhau; có file nguồn: lấy trực tiếp. | |
| L-MEAS-14 | [!!] | Có link Figma nhưng letter-spacing vẫn lệch (người dùng chỉ ra): file lưu ls theo % (6%) mà code tham khảo của `get_design_context` xuất px đã nhân sẵn (`tracking-[0.96px]` @16px, `1.02px` @17px) → chép thành `1px` / `.96px`, quy đổi em sai, và giữ nguyên px khi SP đổi font-size. Dev Mode không đổi gì (cùng dữ liệu). → Không lấy ls/lh từ `get_design_context`; dùng `figspec.py` (Plugin API, đọc `{unit, value}` từng đoạn chữ) → `letter-spacing` luôn viết em theo cột `ls`; kiểm bằng `xdcmp.py`. | figspec.py, xdcmp.py |
| L-MEAS-15 | [!!] | `xdcmp.py` chỉ so STYLE chữ (size/weight/ls/lh/màu) → "0 lệch" nhưng vị trí dọc vẫn sai 2–13px ở nhiều section (margin-top heading/catch/lead, padding-top card, khoảng ảnh→tiêu đề). → Sau xdcmp luôn chạy `xdpos.py URL spec.json --ab <artboard>`: ghép shape↔DOM (x/w/h) và chữ↔text node, so tâm dòng (XD: `y + size/2` vì y là mép trên em-box), in `Δloc` = lỗi phát sinh ngay giữa 2 mục cùng loại. Tâm chữ lệch sẵn theo metric font (±2px, Shippori 50px ≈ -4px) → chỗ đổi font có thể báo giả: xác nhận bằng `inkcmp.py` (so top→top dòng mực trên ảnh design) rồi mới sửa. Sửa từ Δloc đầu tiên trở xuống, gom 1 vòng. Mục tiêu: xdpos exit 0 (`--tol 2`), inkcmp Δloc ≤ 1 cho mọi section. | xdpos.py, inkcmp.py |

## 3. CSS / SCSS (L-CSS)

| ID | Mức | Lỗi → Quy tắc | Tự động |
|---|---|---|---|
| L-CSS-01 | [!!] | `p { line-height }` trong base đè lên line-height đặt ở cha. → Đặt line-height trực tiếp lên `p` hoặc `p { line-height: inherit }`. | pixeldiff (Δ) |
| L-CSS-02 | [!] | `* { letter-spacing }` trong reset → letter-spacing không kế thừa. → Đặt ở từng phần tử. | |
| L-CSS-03 | [!] | Header height trong settings ≠ design → toàn trang lệch đều. → So dải đầu tiên của `pixeldiff` (drift ≠ 0 ngay từ đầu). | pixeldiff |
| L-CSS-04 | [!] | Dùng `position:absolute` + top/left để "ép" khớp thay vì sửa layout. → Chỉ absolute cho trang trí/chồng lớp thật sự; layout dùng flow/flex/grid. | |
| L-CSS-05 | [!] | Không dùng mixin/biến/utility sẵn có (màu, breakpoint, `.container`, `.pc/.sp`). → Bước 0 phải liệt kê chúng; code mới dùng lại. | |
| L-CSS-06 | [!!] | Đặt tên class sai quy ước (BEM `__`, 3–4 từ). → RSCSS: component 2 từ nối gạch (`case-head`), element 1 từ, variant `-xxx`. | |
| L-CSS-07 | | Phần tử absolute (chữ EN nền) đè lên phần tử tĩnh phía sau. → Cho phần tử cần nổi `position: relative` (+ z-index nếu cần). | |
| L-CSS-08 | | Định nghĩa lại cùng selector ở 2 nơi → khó bảo trì, sửa chỗ này mất chỗ kia. → grep selector trước khi thêm. | |
| L-CSS-09 | | Compile sai style (expanded thay vì compressed, có/không source map) → diff lớn khi commit. → Giữ đúng như file .css đang có. | |
| L-CSS-10 | [!] | Đặt class element chung chung (`.tag`, `.label`, `.btn`...) trùng với component dùng chung của theme → kế thừa ngầm width/font-weight/padding (đã gặp thực tế: thẻ STEP rộng 130px thay vì 76px, chữ đậm thay vì 500; người dùng phát hiện sau khi giao). → Trước khi đặt tên class mới, grep tên đó ở cấp gốc trong CSS (`}.ten{`); trùng thì đổi tên. Sau khi render, `rects.py` có x/w cho các phần tử nhỏ (thẻ, nhãn, nút) + `--styles` để thấy thuộc tính bị kế thừa. **Lặp 3 lần** → nay `audit.py` tự báo. | **audit W CSS-CLASS-CLASH**, rects.py Δw |
| L-CSS-11 | [!] | Thanh trang trí nhỏ (vạch 46×4px trên đầu thẻ) code góc vuông trong khi design bo góc — `radius.py` chỉ đo khối lớn (người dùng chỉ ra). → Zoom 4x mọi phần tử trang trí nhỏ (vạch, tag, badge, chấm) để kiểm tra bo góc; mặc định nghi ngờ có `border-radius` khi đầu vạch trông tròn/nhạt. Sửa 1 chỗ thì grep cùng pattern (L-FLOW-03). | |
| L-CSS-12 | [!] | Core/reset đặt `font-feature-settings: "palt"` cho p/li/div → kana, dấu câu bị co, dòng ngắn hơn design (design không dùng palt). → Đo pitch ký tự kana so với kanji trên design; nếu bằng nhau thì tắt palt cho phạm vi mình code (`font-feature-settings: normal`, kèm `text-spacing-trim: space-all`). | rowcmp.py Δx1 |
| L-CSS-13 | [!] | Tab active cao hơn tab thường bằng cách đổi `height` (+ `transition: all`) → khi click tab, layout nhảy/giật (người dùng chỉ ra). → Giữ chiều cao cố định cho mọi trạng thái; phần "thấp hơn" của tab thường làm bằng `clip-path: inset(Npx 0 0 0 round …)` / `transform`; chỉ transition màu, nền, clip-path. | |
| L-CSS-14 | [!!] | r4-template: `rem()` chia cho base PC (18px) nhưng ở ≤1200 html đổi 15px → mọi `rem(Npx)` không override SP bị nhỏ đi 1/6. Viết `rem(20)` (thiếu px) thì ra `calc(…rem/1px)` không hợp lệ, trình duyệt bỏ qua. → Luôn truyền đơn vị `rem(20px)`; cỡ chữ SP dùng `rem-tb(Npx)` trong media (hoặc mixin xuất cả rem + rem-tb); grep `rem([0-9]+)` trước khi giao. | grep |
| L-CSS-15 | [!] | Tự thêm mixin/hàm tiện ích mới (vd `@include fs()` gộp rem + rem-tb) không có trong template → người khác không biết nguồn, lệch quy ước, mỗi lần gọi sinh 1 khối `@media` riêng (người dùng chỉ ra). → Chỉ dùng mixin/hàm template có sẵn; viết theo pattern của template (PC `font-size: rem(Npx)`, SP gom vào khối `@media` sẵn có của component bằng `rem-tb(Npx)`). Cần helper mới thì hỏi trước. Khi refactor: so computed font-size/line-height mọi phần tử trước/sau (phải = 0 thay đổi). | |
| L-CSS-16 | [!] | Lớp phủ/gradient/blend trên ảnh nền (乗算, 背景のぼかし, gradient hướng chéo) bị bỏ qua hoặc làm sai (phủ thường thay multiply, gradient dọc thay chéo). → Đọc `blend`/`blur`/`grad(...;x1,y1,x2,y2)` trong spec; CSS: `background: gradient, url() ; background-blend-mode: multiply` hoặc pseudo + `mix-blend-mode`, `backdrop-filter`; hướng theo toạ độ (0,0→1,1 = to bottom right). | xdspec.py --summary |
| L-CSS-17 | [!!] | Vòng tròn/blob trang trí mờ (radial gradient) làm sai 3 lần liên tiếp (người dùng chỉ ra 2 lần): (1) đưa vào `background` của section với alpha 100% — quá đậm và bị cắt ở ranh giới section, vì `xdspec` cũ không nhân opacity của group cha (blob 1.0 thay vì 0.21–0.33); (2) tách thành phần tử absolute nhưng nằm TRÊN nền + đường cong của section phía trước (phần tử positioned vẽ sau theo thứ tự DOM); (3) để vậy mà không kiểm vùng chồng lấn. → Đọc mục "Trang trí bán trong suốt" của `xdspec --summary` (opacity hiệu dụng gồm group, `group=`, `z=`). Mỗi group = 1 phần tử `aria-hidden` có nhiều lớp `background` (lớp vẽ sau trong XD đặt TRƯỚC trong CSS) + `opacity` của group; nội dung section `position:relative; z-index:1`. Blob tràn sang section khác: lấy màu pixel design ở vùng chồng lấn — nếu bằng màu nền section kia thì section đó phải nằm trên (`position:relative; z-index:1` cho cả section), rồi so lại màu pixel render = design. Thứ tự `z` trong XD không phản ánh lớp giữa các section trên web, phải kiểm bằng pixel. | xdspec.py --summary (opacity/gop/z) |
| L-CSS-18 | [!] | Đáy KV cong làm bằng `mask` nhiều lớp + `radial-gradient(calc(50% + Npx) …)` → trình duyệt bỏ cả khai báo (computed `mask-image: none`), KV thành hình chữ nhật; ảnh chụp so sánh nhỏ nên không thấy, người dùng chỉ ra. → Sau khi dùng `mask`/`clip-path`/`-webkit-*`, kiểm `getComputedStyle(el).maskImage !== 'none'` (hoặc clipPath) và chụp đúng vùng đó ở viewport thật, zoom. Ưu tiên cách chắc chắn: khung trong rộng hơn N px mỗi bên + `border-radius: 0 0 50% 50% / 0 0 Hpx Hpx`, khung ngoài `overflow:hidden` cắt hai cạnh (elip rộng hơn khung hiển thị như hình cắt trong XD). | |
| L-CSS-19 | [!] | Nhãn nhỏ (tag/category) `display:inline-block` đặt trên dòng tiêu đề → nó nằm trong 1 line box cao bằng line-height của cha (vd 32px) nên tag thấp xuống 6px và khoảng dưới thẻ lệch (người dùng chỉ ra). → Nhãn đứng riêng 1 dòng: `display:block; width:fit-content`. Kiểm: rect DOM của nhãn = rect XD (x,y,w,h). | rects/DOM vs spec |
| L-CSS-20 | [!] | Icon Font Awesome (FA6/7) có bề rộng cố định 1.25em → khoảng icon↔chữ và giữa các mục header lệch 6–10px so với design (người dùng chỉ ra). → `width:auto` cho `<i>` rồi đặt margin theo số đo ink (đo bằng `measure.py --cols`), so từng mốc x (icon, chữ, mục kế) với design. | measure.py --cols |
| L-CSS-21 | [!] | Style trích dẫn (blockquote) viết thành class mới `.quote-box` trong file style chung, trong khi r4-template đã có style mặc định cho thẻ `blockquote` ở `base/_cms.scss` (người dùng chỉ ra: nội dung CMS nhập `<blockquote>` trơn sẽ không ăn design). → Phần tử mà editor CMS xuất ra trực tiếp (`blockquote`, và tương tự cho thẻ mặc định khác) phải chỉnh ngay tại chỗ base đã định nghĩa (`grep -rn "blockquote" sass/` trước khi viết), style lên thẻ — không thêm class riêng. Kiểm: `grep` selector thẻ trong sass trước khi tạo component mới cho phần tử đó. | grep |
| L-CSS-22 | [!] | (1) Hàng flex `align-items:center` gồm tiêu đề cao 58px và tab cao 56px (spec 55px) → tab lệch xuống 1.5px, cả danh sách dưới lệch 2px; (2) logo `<img>` có viền trong suốt phía trên → mực thấp hơn nav bên cạnh 3px dù box cùng `top`. → Chiều cao khung lấy đúng `h` của shape (không làm tròn 55→56); design căn MÉP TRÊN thì `align-self:flex-start`, không để center; phần tử là ảnh/icon thì căn theo MỰC (`inkcmp.py`), bù bằng margin âm có comment lý do. | xdpos.py (Δh, Δloc) |

## 4. Responsive (L-RESP)

| ID | Mức | Lỗi → Quy tắc | Tự động |
|---|---|---|---|
| L-RESP-01 | [!!] | Tràn ngang ở SP (ảnh/khối rộng cố định, `100vw` + scrollbar, phần tử trang trí lòi ra). → Luôn chạy `audit.py`; phải `RESP-OVERFLOW` = 0 ở mọi viewport. | RESP-OVERFLOW, RESP-OVERFLOW-EL |
| L-RESP-02 | [!!] | Khi làm SP lại sửa code PC; hoặc SP override thua specificity của selector PC. → Chỉ thêm trong `@media`; viết selector SP cùng độ đặc hiệu với PC; chụp lại PC sau khi làm SP để chắc PC không đổi (`pixeldiff` PC giữ nguyên). | pixeldiff PC |
| L-RESP-03 | [!!] | Tự viết `@media{display:none}` thay vì dùng `.pc/.tb/.sp/.xs` có sẵn. | |
| L-RESP-04 | [!] | Chỉ kiểm tra 1440 và 375 → vỡ ở 1024/768/1200 (khoảng giữa). → `audit.py` mặc định chạy pc/tb/sp; với layout có `min-width` kiểm thêm width nhỏ nhất. | RESP-OVERFLOW |
| L-RESP-05 | [!] | Drawer menu ẩn ngoài màn hình có `box-shadow` → bóng lọt mép phải. → Chỉ thêm shadow khi mở. | |
| L-RESP-06 | | Chữ < 12px ở SP do co theo tỉ lệ. → Theo design; nếu design < 12px thì giữ, nhưng nêu trong báo cáo. | TEXT-TINY |
| L-RESP-07 | | Thiếu `<meta viewport>` ở trang mới. | RESP-VIEWPORT |
| L-RESP-08 | [!] | Hình trang trí full-width dùng `aspect-ratio` theo chiều rộng → màn ≥1900px hình cao lên, bị cắt còn một nửa (người dùng chỉ ra). → Trang trí kéo theo chiều ngang: cố định chiều cao, chỉ giãn ngang (mask `100% 100%`), hoặc giới hạn `max-width`; chụp thêm 1920 (và 2560) khi có trang trí full-width. | |
| L-RESP-09 | [!] | Tự vẽ lại hình trang trí bằng SVG `preserveAspectRatio="none"` từ đường biên đo trên ảnh → hình méo khi khung đổi tỉ lệ (SP, màn cao), lệch so với design (người dùng chỉ ra). → Xin asset gốc (PNG/SVG xuất từ design); giữ tỉ lệ (`aspect-ratio` + `height:100%`), nếu cần animation bên trong thì tách alpha thành mask. | |

## 5. HTML & liên kết (L-HTML, L-LINK)

| ID | Mức | Lỗi → Quy tắc | Tự động |
|---|---|---|---|
| L-HTML-01 | [!] | Thẻ không đóng / đóng sai thứ tự sau khi sửa nhiều lần. | HTML-UNCLOSED, HTML-STRAY-CLOSE |
| L-HTML-02 | [!] | id trùng (copy section). | HTML-DUP-ID |
| L-HTML-03 | | `<a>` lồng `<a>` (card link chứa nút link). → Dùng 1 link hoặc stretched-link. | HTML-NESTED-A |
| L-HTML-04 | [!] | Cấu trúc chỉ đúng "nhìn", sai nghĩa (div cho list, heading nhảy cấp). → Dùng ul/dl/table/heading đúng cấp. | HTML-HEADING-SKIP |
| L-HTML-05 | | img thiếu alt. | IMG-ALT |
| L-HTML-06 | [!] | Thẻ link dạng card: `<a>` bọc `div`/`p`/heading (người dùng chỉ ra là sai semantic). → `<a>` chỉ chứa nội dung phrasing; card toàn bộ là link thì dùng pattern có sẵn của project (`.hover-all`: `a` phủ cả thẻ, nội dung là heading/p bên ngoài `a`) hoặc span. Kiểm tra: grep `<a[^>]*>\s*<(div|p|h[1-6])`. | |
| L-HTML-07 | [!!] | Chọn thẻ theo "nhìn" thay vì nghĩa (đã gặp thực tế, người dùng yêu cầu kiểm tra semantic sau khi giao): `<small>` để thu nhỏ chữ trong h1, `<section>` cho dải chỉ có 1 câu không heading, `aria-label` trên `div` thường (trình duyệt bỏ qua). → `<small>` = chú thích phụ/bản quyền, chữ nhỏ trang trí dùng `<span class>`; `<section>` phải có heading (không có → `<div>`); vùng cần nhãn dùng thẻ landmark (`<section>`/`<nav>`/`<aside aria-label>`), không gắn `aria-label` lên div/span không role. | SEM-SMALL-STYLE, SEM-SECTION-NOHEAD, SEM-ARIA-GENERIC |
| L-HTML-08 | [!] | KV chứa `<h1>` đặt ngoài `<main>` (template để KV ngoài main) → skip-link 「本文へスキップ」 nhảy qua tiêu đề trang. → Khối chứa h1 nằm trong `<main>`; trang có đúng 1 h1, các section h2, con h3/h4 không nhảy cấp (in outline bằng DOM để kiểm). Khối phụ cố định (CTA bên, nút追従) dùng `<aside aria-label>`. | SEM-H1-OUTSIDE-MAIN, SEM-NO-H1, SEM-NO-MAIN, HTML-HEADING-SKIP |
| L-HTML-09 | [!] | (Sửa đổi theo yêu cầu người dùng) Ghi width/height trên mọi `<img>`/`<source>` → người dùng thấy rườm rà, yêu cầu bỏ và lần sau không thêm. Khi bỏ đã gặp 2 bẫy: (1) SVG xuất có width/height gốc làm tròn lên (167.11→168) → không còn thuộc tính HTML thì ảnh to hơn 1px; (2) ảnh `height:auto` chỉ có `width` (icon SP) → trước khi tải cao 0, khối nhảy 18px khi tải xong. → Mặc định KHÔNG ghi width/height trong HTML; kích thước do CSS. Giữ chỗ bằng CSS: ảnh `height:auto` mà phía dưới còn nội dung → thêm `aspect-ratio` (hoặc khung cha cố định chiều cao); SVG tự xuất: width/height gốc của file = kích thước viewBox (số lẻ, không làm tròn). Kiểm chứng sau khi bỏ: chặn tạm request ảnh, đo `top` của các section, cho tải xong, đo lại → chênh 0px ở mọi viewport; và render cuối không đổi. | IMG-SIZE (I) |
| L-HTML-10 | | Bảng/form thiếu thuộc tính ngữ nghĩa: `<th>` không `scope`, input không có `<label>` liên kết, thiếu `autocomplete` (name/email/tel), bước form (入力/確認/送信) không đánh dấu bước hiện tại. → `th scope="row|col"`; `label for`=id hoặc bọc trong label; `autocomplete="name|email|tel|postal-code"`; danh sách bước `<ol aria-label>` + `aria-current="step"`. | SEM-TH-SCOPE, FORM-LABEL, FORM-AUTOCOMPLETE |
| L-LINK-01 | [!] | Link nội bộ / PDF / ảnh trỏ file không tồn tại, sai path tương đối. | LINK-BROKEN, IMG-MISSING, CSS-URL-MISSING, HTTP-404 |
| L-LINK-02 | | `target=_blank` thiếu `rel="noopener"`. | LINK-BLANK-REL |
| L-LINK-03 | | Còn `href="#"` khi giao mà không báo. → Liệt kê trong báo cáo, hoặc gắn `@link(ID)` (skill internal-link-tagger). | LINK-PLACEHOLDER |
| L-LINK-04 | | `tel:` có khoảng trắng/ký tự Nhật. → `tel:0312345678`. | LINK-TEL |

## 6. Ảnh & font (L-IMG, L-FONT)

| ID | Mức | Lỗi → Quy tắc | Tự động |
|---|---|---|---|
| L-IMG-01 | [!] | Ảnh mờ ở retina (cắt @1x, hiển thị to hơn). → Cắt từ design @2x; ảnh gốc ≥ 2× kích thước hiển thị. | IMG-LOWRES |
| L-IMG-02 | | Ảnh méo do width/height không đúng tỉ lệ. → `object-fit: cover` hoặc sửa kích thước. | IMG-DISTORT |
| L-IMG-03 | [!] | Icon/trang trí làm bằng CSS vẽ tay khác design. → Xuất ảnh thật, đặt bằng pseudo-element; icon font (Font Awesome) thì giữ icon font. | |
| L-IMG-04 | | Đặt tên file ảnh khác quy ước (gạch nối vs gạch dưới). → Xác nhận quy ước trước khi cắt. | |
| L-IMG-05 | [!!] | Cắt ảnh placeholder từ screenshot có chữ/nút đè lên rồi "xoá" bằng inpaint/làm mờ → ảnh có mảng mờ bên trong (KV, nền section, ảnh card), người dùng tưởng là design (người dùng chỉ ra). → Không inpaint/làm mờ. Xoá nội dung đè (ẩn layer chữ/nút/overlay) **trước khi xuất ảnh**: có file nguồn (XD/Figma) thì tự ẩn layer rồi export; chỉ có ảnh tĩnh thì xin người dùng xuất ảnh sạch, trong lúc chờ để ảnh tạm trung tính (nền màu/noimage) và liệt kê trong báo cáo. | |
| L-IMG-06 | [!] | Texture trang trí: (1) `background-size: X% Y%` kéo theo 2 chiều khung → méo khi màn rộng; (2) animate `background-position` khi ảnh vừa khít → lộ khoảng trắng mép; (3) tách mask từ ảnh bằng ngưỡng màu → chỗ texture gần trắng thành lỗ. → Texture đặt ở pseudo-element `inset:-10%` + `background-size: cover`, chuyển động bằng `transform` trong phần dư; mask lấy thành phần lớn nhất + `binary_fill_holes`; kiểm tra ở 1920/2560 và nhiều thời điểm animation (`getAnimations().currentTime`). | |
| L-IMG-07 | [!] | Ảnh nền banner/section cắt từ ảnh design (đã có sẵn lớp phủ màu `multiply 60%`) rồi CSS phủ thêm đúng lớp đó (L-CSS-16) → màu đậm gấp đôi, khác hẳn design (người dùng tưởng ảnh design là bản cũ). → Trước khi phủ overlay: so màu trung bình của file ảnh với vùng đó trên ảnh design (`python3 -c` numpy mean, hoặc `colors.py`); gần bằng nhau (±5) = ảnh đã có màu → xin ảnh gốc (xuất từ XD ẩn lớp phủ) hoặc bỏ overlay CSS và ghi chú. Ảnh gốc thì overlay theo spec (`blend`, `opacity`). | |
| L-FONT-01 | [!] | Font web không load (sai tên family, thiếu weight trong URL Google Fonts) → render bằng font hệ thống, mọi số đo lệch. | FONT-NOT-LOADED |

## 7. JS / tương tác (L-JS)

| ID | Mức | Lỗi → Quy tắc | Tự động |
|---|---|---|---|
| L-JS-01 | [!] | Slider khởi tạo sai hành vi (loop/autoplay/centerMode/số slide SP). → Xác nhận từ design/spec trước khi init. | |
| L-JS-02 | [!] | Quên hover/focus/active, animation có trong spec. → Checklist hover cho mọi link/nút; `shot.py --hover` để chụp trạng thái. | |
| L-JS-03 | | Lỗi JS console (jQuery chưa load, selector null). | JS-ERROR, JS-CONSOLE |
| L-JS-04 | [!!] | Viết lại chức năng đã có trong template (`common.js`, `js/module/*.js`, plugin) — đã gặp thực tế: tự viết tab (お知らせ, コラム) và accordion (menu SP, footer) trong `common.js` trong khi template có `module/tab.js` và `module/jquery.accordion.js` (người dùng chỉ ra là dư thừa). → Bước 0: liệt kê `js/module/`, `js/plugin/` và cách parts/regulation (`parts.html`, `00_parts.html`) gọi chúng (markup bắt buộc: `a[data-href]` + id panel, class trạng thái `.current`/`.active`); lập bảng "tương tác trong design → module có sẵn" trước khi viết JS mới. Chỉ viết mới khi không module nào làm được, và nói rõ lý do trong báo cáo. | |
| L-JS-05 | [!] | Module có sẵn gọi nhiều instance trên 1 trang (vd 2 nhóm tab gọi `.tab()` riêng) → mỗi instance bind click toàn cục, bấm tab nhóm này thì instance kia cuộn trang / xoá trạng thái nhóm khác. → Sau khi dùng module, test bấm từng nhóm và đo `scrollY` trước/sau + trạng thái class của các nhóm khác; lỗi của module thì sửa tối thiểu trong module (comment lý do) và báo người dùng (ảnh hưởng mọi trang dùng module). | |
| L-JS-06 | [!] | Slider SP 1 thẻ + lộ thẻ kế: slick 1.8 dùng chính phần tử làm slide (không bọc) → padding chừa khoảng cộng vào trong thẻ (thẻ 331px thay vì 315px, tiêu đề xuống dòng khác); slide cao theo thẻ cao nhất. → `variableWidth: true` + width thẻ cố định (`calc(100vw - Npx)`) + `margin-right` khoảng cách; `adaptiveHeight: true`; đo lại width/height thẻ bằng DOM. | |

## 8. Kiểm chứng (L-SHOT) — lỗi của chính quy trình so sánh

| ID | Mức | Lỗi → Quy tắc | Tự động |
|---|---|---|---|
| L-SHOT-01 | [!!] | Chụp render khi khối `.fade`/inview chưa hiện → nửa trang trống, so sánh sai hoàn toàn (đã gặp thực tế: trang có fade-in khi cuộn). → `shot.py` mới tự cuộn + tắt transition; nếu báo "còn N khối opacity:0" thì xử lý trước khi so. | shot.py cảnh báo, pixeldiff `bands_mismatch` |
| L-SHOT-02 | [!] | Dùng `chrome --headless --window-size=375` → thực tế rộng ~500px. → Dùng `shot.py` (Playwright). | |
| L-SHOT-03 | | Slider tự chạy → mỗi lần chụp khác nhau, diff dao động. → `shot.py` dừng slick/swiper ở slide 0; còn khác thì `--mask` vùng đó. | |
| L-SHOT-05 | | Trang có khối dài khác design một cách CHỦ Ý (tab cuộn hiện mọi panel, accordion mở sẵn...) → so sánh mất dấu cả phần dưới (đã gặp thực tế: lệch +2600px, cả nửa dưới bị báo sai). → `pixeldiff` tự dò lại và báo "DÒ LẠI"; xác nhận đó là chủ ý rồi đánh giá các dải sau mốc đó. | pixeldiff `resyncs` |
| L-SHOT-04 | | So với design cũ (người dùng đã gửi bản mới / có 調整依頼書). → Xác nhận file design mới nhất và ghi đường dẫn vào ghi chú đo. | |
| L-SHOT-06 | [!] | Trang có GTM/analytics/font CDN → chờ "load"/"networkidle" timeout 30s, script crash, chạy lại nhiều lần (đã gặp thực tế: mất ~10 phút chỉ để chụp được ảnh). → Dùng `_page.open_page` (shot/rects/audit đã dùng): chờ networkidle có hạn `--settle` rồi đi tiếp. Chạy ngoài sandbox ngay từ đầu. | shot.py/rects.py in "chưa networkidle" |
| L-SHOT-07 | [!] | Đo vị trí khi webfont chưa tải xong → xuống dòng khác, số Δ sai cả vòng (đã gặp thực tế). → Luôn chờ `document.fonts.ready` trước khi đo/chụp; script tự viết cũng phải làm vậy. | |
| L-SHOT-08 | [!] | Header/KV dùng chung khác design → pixeldiff lệch dây chuyền cả trang, vô dụng. → `rects.py` căn theo khối mốc trong vùng mình code; ghi tọa độ design của mọi khối 1 lần ở đầu. | rects.py |
| L-SHOT-09 | | Compile SCSS bằng công cụ khác project (thiếu autoprefixer / khác browserslist) → file CSS khác hẳn bản cũ. → Compile ra file tạm, so kích thước + tập selector với CSS hiện có trước khi ghi đè. | |
| L-SHOT-10 | [!] | Phần tử cao theo màn hình (`100vh` KV full màn hình) chụp với viewport cao 900 cố định → cao khác design, pixeldiff lệch cả trang (vài trăm px) dù CSS đúng. → Chụp với `--vp pc=WxH`, H = toạ độ đáy phần tử đó trên design (vd KV đáy 675 → `pc=1400x675`); kiểm thêm 1 lần ở chiều cao màn hình thật (900) bằng mắt. | shot.py `--vp name=WxH` |
| L-SHOT-11 | [!!] | Tin `pixeldiff` dải 200px + `final_drift` nhỏ (8px trên trang 10k px) là "gần đạt": các lệch cục bộ +5 / -4 / +3 bù trừ nhau, dải 200px còn trung bình hoá lệch trong section → bỏ sót hàng loạt margin sai. → pixeldiff chỉ để thấy lệch LỚN và nội dung khác; độ chính xác khoảng cách phải chứng minh bằng `xdpos.py` (có XD/Figma) hoặc `inkcmp.py --box` cho TỪNG section (cột chữ chính, tránh hình trang trí). Báo "đạt" chỉ khi cả hai đạt, không chỉ `final_drift`. | xdpos.py, inkcmp.py |

---

## Cách người dùng yêu cầu sửa cho hiệu quả (mẫu câu)

Yêu cầu càng cụ thể, vòng sửa càng ít. Khi giao lại cho Claude, nên theo dạng:

```
[Trang] index.html  [Viewport] SP 375  [Section] お知らせ
[Hiện tại] khoảng cách tiêu đề → list ~40px
[Design]   24px (xem ảnh đính kèm / XD inspector)
[Phạm vi]  chỉ SP, không đổi PC; kiểm tra các trang khác dùng cùng component
```

Claude khi nhận yêu cầu sửa phải: (1) đo lại xác nhận lỗi bằng script, (2) tìm ID bài học tương ứng ở trên,
(3) sửa + grep sửa cùng pattern (L-FLOW-03), (4) `metrics.py fix --by user --lesson <ID>`, (5) chạy lại
`pixeldiff`/`audit` và báo số trước/sau.

## Thêm bài học mới (mẫu)

Khi gặp lỗi chưa có ID: thêm 1 dòng vào nhóm phù hợp, ID tiếp theo trong nhóm, ghi **lỗi đã xảy ra** (cụ thể
về kỹ thuật, **không ghi tên khách hàng / tên dự án / đường dẫn máy** — file này được chia sẻ) → **quy tắc tránh lặp lại**, và cột Tự động nếu viết được kiểm tra. Nếu lỗi bắt được
bằng máy (DOM/CSS/ảnh) → ưu tiên thêm kiểm tra vào `audit.py` thay vì chỉ ghi chữ. Bài học chỉ đúng cho
1 dự án → ghi vào memory của dự án đó, không ghi vào đây.

| ID | Mức | Lỗi đã xảy ra → Quy tắc | Tự động |
|---|---|---|---|
| L-XXX-NN | | ... → ... | |
