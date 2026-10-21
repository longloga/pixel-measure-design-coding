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
