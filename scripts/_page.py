"""共通ヘルパー: サードパーティスクリプト（GTM、アナリティクス、フォント CDN）があっても安定してページを開く。

旧来の問題: `goto()` が "load"/"networkidle" を上限なしで待つため、GTM・広告・応答しないリクエストのある
ページで 30 秒タイムアウトしてクラッシュし、何度もやり直す必要があった。
新方式（機能は削らない）: 従来どおり networkidle を待つが上限（`settle_ms`）を設け、超えたらクラッシュせず
DOM 準備済みの状態で続行する。また必ず Web フォント（document.fonts.ready）を待つ — フォント読み込み前に
計測／撮影すると改行位置がずれるため。
"""
import os

CHROME_CANDS = ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
                '/usr/bin/google-chrome', '/usr/bin/chromium']


def launch(p):
    exe = next((c for c in CHROME_CANDS if os.path.exists(c)), None)
    return p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()


def open_page(pg, url, settle_ms=8000, nav_timeout=60000):
    """完全に読み込めた場合は None、networkidle 待ちを途中で打ち切った場合は警告文字列を返す。"""
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
