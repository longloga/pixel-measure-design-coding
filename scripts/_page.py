"""Helper dùng chung: mở trang bền vững với script bên thứ 3 (GTM, analytics, font CDN).

Vấn đề cũ: `goto()` chờ sự kiện "load"/"networkidle" không giới hạn mềm → trang có GTM/quảng cáo
hay request treo làm timeout 30s rồi CRASH, phải chạy lại nhiều lần.
Cách mới (không giảm chức năng): vẫn chờ networkidle như cũ nhưng có hạn (`settle_ms`); quá hạn thì
tiếp tục với DOM đã sẵn sàng thay vì crash, và luôn chờ webfont (document.fonts.ready) — đo/ chụp trước
khi font tải xong sẽ sai vị trí xuống dòng.
"""
import os

CHROME_CANDS = ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
                '/usr/bin/google-chrome', '/usr/bin/chromium']


def launch(p):
    exe = next((c for c in CHROME_CANDS if os.path.exists(c)), None)
    return p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()


def open_page(pg, url, settle_ms=8000, nav_timeout=60000):
    """Trả về None nếu tải trọn vẹn, hoặc chuỗi cảnh báo nếu phải dừng chờ networkidle giữa chừng."""
    note = None
    pg.goto(url, wait_until='domcontentloaded', timeout=nav_timeout)
    try:
        pg.wait_for_load_state('load', timeout=settle_ms)
        pg.wait_for_load_state('networkidle', timeout=settle_ms)
    except Exception:
        note = f'trang chưa "networkidle" sau {settle_ms}ms (thường do GTM/analytics) → tiếp tục với DOM đã sẵn sàng'
    try:
        pg.evaluate('document.fonts.ready.then(() => true)')
    except Exception:
        pass
    return note
