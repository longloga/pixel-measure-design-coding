# Quy tắc suy ra số đo từ pixel

Tất cả đơn vị là CSS px (đã chia scale).

## Font-size

- Chữ Nhật (Noto Sans JP, Mincho): chiều cao nét mực của dòng có kanji ≈ **0.90–0.93 × font-size**.
  Ví dụ dòng cao 37 → 40px; 17 → 18px; 15 → 16px; 20 → 20–22px.
- Dòng chỉ có kana/dấu câu thì nét thấp hơn → ưu tiên đo dòng có kanji.
- Font Latin (Poppins, chữ hoa/số): cap height ≈ **0.70 × font-size**. Chữ EN nền cao 100 → 140px.
- Kiểm tra chéo bằng độ rộng: `bước mỗi ký tự = (x_phải - x_trái + ~nửa ký tự cuối) / số ký tự`;
  `bước = font-size × (1 + letter-spacing)`. Chữ toàn khoảng (CJK) có advance = 1em.

## Line-height

- `line-height = khoảng cách y giữa đầu 2 dòng liên tiếp` (không phải chiều cao dòng mực).
- Khoảng cách đoạn: nếu gap giữa 2 đoạn = 2 × line-height → có 1 dòng trống (margin = 1 line);
  nếu ví dụ 66 với line-height 36 → `p + p { margin-top: 30px }`.
- Vị trí box từ vị trí mực: `box_top ≈ ink_top - (line-height - ink_height) / 2`.

## Khoảng cách giữa khối

- Đo từ **box** chứ không phải từ mực: margin = box_top(khối dưới) - box_bottom(khối trên), với box tính
  theo công thức trên. Box ảnh/card thì mực = box.
- Tìm hằng số lặp lại giữa các section (ví dụ heading mực luôn ở +118 so với đầu section, nội dung luôn
  cách heading ~56px) → 1 rule chung + override cho ngoại lệ.

## Chữ EN lớn trang trí (Poppins, line-height: 1)

- Với line-height 1: từ đỉnh box tới baseline ≈ 0.85em, tới đỉnh chữ hoa ≈ 0.15em
  (Poppins ascent 1.05, descent 0.35). Dùng để tính `top`/`padding-top` cho dòng sub nằm đè lên chân chữ EN.
- Lề trái của glyph (side bearing) ~0.04em → `left` lùi thêm vài px so với vị trí mực.

## Màu

- Lấy màu nền/khối đặc bằng `--pt` ở giữa khối. Màu chữ dùng `--dark` (pixel tối nhất) vì viền chữ bị
  anti-alias.
- Nền gradient ngang: so màu cột trái và phải từ `sections.py`.

## Bo góc

- `radius ≈ d / 0.2929`, d = số px đi theo đường chéo từ góc đến khi chạm pixel khác nền.
- Ảnh chụp có vùng trắng tại góc → kết quả lớn bất thường, bỏ qua, lấy theo các góc khác.

## Ellipse / oval

- Đo x mép trái ở nhiều y. Với tâm y_c, bán trục ry = height/2:
  `x_offset = rx × (1 - sqrt(1 - ((y - y_c)/ry)^2))`. rx ≈ x mép tại hàng gần đỉnh trừ x mép tại tâm.
  → `border-radius: rx / 50%`.

## Phần tử tràn container

- Container nội dung C (vd 1080), viewport V. Ảnh cách mép màn hình 30px:
  `margin-right: calc((C - 100vw) / 2 + 30px)`. Ảnh bắt đầu ở tâm + 13px rộng tới mép-30:
  `width: calc(50vw - 43px)`. Kiểm tra lại ở viewport hẹp nhất (min-width của layout).
