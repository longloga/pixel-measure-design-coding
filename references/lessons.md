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

## 5. HTML & liên kết (L-HTML, L-LINK)

| ID | Mức | Lỗi → Quy tắc | Tự động |
|---|---|---|---|
| L-HTML-01 | [!] | Thẻ không đóng / đóng sai thứ tự sau khi sửa nhiều lần. | HTML-UNCLOSED, HTML-STRAY-CLOSE |
| L-HTML-02 | [!] | id trùng (copy section). | HTML-DUP-ID |
| L-HTML-03 | | `<a>` lồng `<a>` (card link chứa nút link). → Dùng 1 link hoặc stretched-link. | HTML-NESTED-A |
| L-HTML-04 | [!] | Cấu trúc chỉ đúng "nhìn", sai nghĩa (div cho list, heading nhảy cấp). → Dùng ul/dl/table/heading đúng cấp. | HTML-HEADING-SKIP |
| L-HTML-05 | | img thiếu alt. | IMG-ALT |
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
| L-FONT-01 | [!] | Font web không load (sai tên family, thiếu weight trong URL Google Fonts) → render bằng font hệ thống, mọi số đo lệch. | FONT-NOT-LOADED |

## 7. JS / tương tác (L-JS)

| ID | Mức | Lỗi → Quy tắc | Tự động |
|---|---|---|---|
| L-JS-01 | [!] | Slider khởi tạo sai hành vi (loop/autoplay/centerMode/số slide SP). → Xác nhận từ design/spec trước khi init. | |
| L-JS-02 | [!] | Quên hover/focus/active, animation có trong spec. → Checklist hover cho mọi link/nút; `shot.py --hover` để chụp trạng thái. | |
| L-JS-03 | | Lỗi JS console (jQuery chưa load, selector null). | JS-ERROR, JS-CONSOLE |
| L-JS-04 | | Viết lại chức năng đã có trong `common.js`/module (accordion, tab, smooth scroll). → Tìm trước khi viết. | |

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
