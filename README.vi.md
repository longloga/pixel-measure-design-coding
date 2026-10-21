# pixel-measure-design-coding

> 日本語版（メイン）: [README.md](README.md)

Skill cho Claude Code: code một trang từ ảnh design (PC + SP) thành HTML/SCSS **khớp design gần 100%**,
rồi **tự kiểm chứng bằng số đo**, không dựa vào cảm nhận bằng mắt.

Claude đo pixel bằng script (font-size, line-height, khoảng cách, màu, bo góc), code theo quy ước của dự án,
chụp trang đã code bằng Chrome, so sánh tự động với design và sửa đến khi lệch ≤ 3px. Cuối cùng chạy kiểm
tra HTML/CSS/responsive/link.

## Cài đặt (1 lần)

```bash
# 1. Đặt thư mục skill vào chỗ Claude Code tìm skill
cp -R pixel-measure-design-coding ~/.claude/skills/

# 2. Thư viện Python
pip3 install pillow numpy playwright
python3 -m playwright install chromium   # bỏ qua nếu máy đã có Google Chrome
```

Kiểm tra: mở Claude Code, gõ `/` và thấy `pixel-measure-design-coding` trong danh sách là được.

## Cách dùng

**Code trang mới từ design**: mở dự án trong VS Code, gửi ảnh design PC + SP và gọi skill:

```
/pixel-measure-design-coding code index.html theo design đính kèm (PC 1440, SP 375)
```

Nên gọi tên skill rõ ràng như trên. Nếu chỉ nói "code lại ảnh này", Claude có thể chọn một skill khác
không có bước kiểm chứng.

**Kiểm tra trang đã code**:

```
/pixel-measure-design-coding kiểm tra index.html so với design này, liệt kê chỗ lệch
```

**Yêu cầu sửa**: càng cụ thể càng ít vòng sửa:

```
[Trang] index.html  [Viewport] SP 375  [Section] お知らせ
[Hiện tại] tiêu đề → list ~40px   [Design] 24px
[Phạm vi] chỉ SP, không đổi PC
```

Claude sẽ báo kết quả bằng bảng số (độ lệch từng section, số lỗi audit). Chưa thấy số thì chưa tính là xong.

## Ảnh design cần chuẩn bị

- Ảnh full-page PNG export từ XD/Figma, **@1x hoặc @2x** (script tự nhận).
- Đủ PC và SP; nếu có bản sửa (調整依頼書) thì gửi **bản mới nhất**.
- Có hover, animation, slider thì gửi kèm ảnh hoặc ghi chú chỉ dẫn.

## Thành phần

| File | Vai trò |
|---|---|
| `SKILL.md` | Quy trình Claude làm theo (8 bước) |
| `references/measurement-rules.md` | Công thức suy font-size / line-height / khoảng cách từ pixel |
| `references/lessons.md` | **Bộ quy tắc rút từ lỗi thực tế**, có ID `L-xxx-nn`, bổ sung dần |
| `scripts/measure.py`, `sections.py`, `colors.py`, `radius.py`, `slice.py`, `crop_assets.py` | Đo design, cắt ảnh |
| `scripts/shot.py` | Chụp trang đã code (tự cuộn để hiện fade-in, chờ font, dừng slider) |
| `scripts/pixeldiff.py` | So sánh design ↔ render tự động, xuất heatmap |
| `scripts/audit.py` | Kiểm tra HTML, responsive (tràn ngang), link/ảnh hỏng, font, lỗi JS |
| `scripts/metrics.py` | Ghi thời gian, số vòng sửa, số lần bị yêu cầu sửa (dữ liệu lưu ở máy mỗi người) |
| `scripts/rects.py`, `rowcmp.py` | So tọa độ từng khối / từng dòng chữ với design (khi header, KV dùng chung khác design) |
| `CHANGELOG.md`, `scripts/changelog.py` | Lịch sử cập nhật skill: thay đổi gì, vì sao, so sánh trước/sau |

Các script chạy độc lập được, ví dụ chỉ kiểm tra lỗi trang:

```bash
python3 ~/.claude/skills/pixel-measure-design-coding/scripts/audit.py index.html
```

## Góp ý & bổ sung bài học

Gặp lỗi Claude lặp lại, hoặc lỗi skill chưa bắt được: **báo cho người duy trì** (kèm mô tả lỗi, ảnh chụp, cách
sửa đúng), đừng sửa trực tiếp bản dùng chung. Lỗi phù hợp sẽ được thêm vào `lessons.md`, hoặc thành kiểm tra
tự động trong `audit.py`, ở phiên bản sau.

Không đưa vào skill: tên khách hàng, ảnh design, đường dẫn dự án, nội dung trang. Quy ước riêng của từng
dự án ghi vào memory / CLAUDE.md của dự án đó.

- Người duy trì: ロン
- Phiên bản và nội dung từng lần cập nhật: xem `CHANGELOG.md`
