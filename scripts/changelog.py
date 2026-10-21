#!/usr/bin/env python3
"""Hỗ trợ ghi CHANGELOG.md mỗi khi cập nhật CHÍNH skill này (script, SKILL.md, references).

  python3 scripts/changelog.py draft            # so với commit gần nhất → in khung mục changelog đã điền phần "so sánh"
  python3 scripts/changelog.py draft --since c29c610
  python3 scripts/changelog.py check            # exit 1 nếu skill có thay đổi mà CHANGELOG.md chưa được cập nhật
  python3 scripts/changelog.py install-hook     # cài git pre-commit hook chạy `check` (chặn commit thiếu changelog)

`draft` tự liệt kê (từ git diff): file thêm/sửa/xoá kèm số dòng, option CLI (`add_argument`) thêm/bỏ ở từng
script, mã bài học (L-XXX-NN) thêm/bỏ trong lessons.md. Phần LÝ DO và SỐ LIỆU TRƯỚC/SAU phải tự điền —
script chỉ đưa khung, không đoán lý do.
"""
import argparse, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRACKED = ('SKILL.md', 'scripts/', 'references/', 'README')   # thay đổi ở đây bắt buộc có changelog
LOG = 'CHANGELOG.md'


def git(*args):
    return subprocess.run(['git', '-C', ROOT, *args], capture_output=True, text=True).stdout


def changed(since):
    """[(status, path)] gồm cả file chưa track."""
    out = [(l[0], l[1:].strip()) for l in git('diff', '--name-status', since).splitlines() if l.strip()]
    out += [('A', p) for p in git('ls-files', '--others', '--exclude-standard').splitlines() if p]
    return out


def old_text(since, path):
    return git('show', f'{since}:{path}')


def new_text(path):
    p = os.path.join(ROOT, path)
    return open(p, encoding='utf-8').read() if os.path.exists(p) else ''


def opts(text):
    return set(re.findall(r"add_argument\(\s*'(--[\w-]+|[a-z_]+)'", text))


def lesson_ids(text):
    return set(re.findall(r'^\| (L-[A-Z]+-\d+) ', text, re.M))


def draft(since):
    files = changed(since)
    if not files:
        print('Không có thay đổi nào so với', since); return
    stat = {}
    for l in git('diff', '--numstat', since).splitlines():
        a, d, p = l.split('\t'); stat[p] = (a, d)
    lines = []
    for st, p in files:
        if st == 'A' and p not in stat:
            stat[p] = (str(len(new_text(p).splitlines())), '0')
        a, d = stat.get(p, ('?', '?'))
        kind = {'A': 'thêm', 'M': 'sửa', 'D': 'xoá'}.get(st, st)
        lines.append(f'| `{p}` | {kind} | +{a} / -{d} |')
    cli = []
    for st, p in files:
        if not p.endswith('.py'): continue
        o, n = opts(old_text(since, p) if st != 'A' else ''), opts(new_text(p) if st != 'D' else '')
        if n - o: cli.append(f'- `{os.path.basename(p)}` thêm option: ' + ', '.join(f'`{x}`' for x in sorted(n - o)))
        if o - n: cli.append(f'- `{os.path.basename(p)}` BỎ option: ' + ', '.join(f'`{x}`' for x in sorted(o - n)) + '  ← kiểm tra tương thích')
    les = []
    lp = 'references/lessons.md'
    if any(p == lp for _, p in files):
        o, n = lesson_ids(old_text(since, lp)), lesson_ids(new_text(lp))
        if n - o: les.append('- Bài học mới: ' + ', '.join(sorted(n - o)))
        if o - n: les.append('- Bài học bị xoá: ' + ', '.join(sorted(o - n)))
    from datetime import date
    print(f'''## [x.y.z] — {date.today().isoformat()} — <tiêu đề ngắn>

### Thay đổi
- <mô tả từng thay đổi, 1 dòng mỗi ý>

### Lý do
- <lỗi/vấn đề THỰC TẾ dẫn tới thay đổi (không ghi tên khách hàng/dự án/đường dẫn máy) + mã bài học liên quan>

### So sánh trước / sau
| Hạng mục | Trước | Sau |
|---|---|---|
| <hành vi / số liệu đo được> | <...> | <...> |

File (so với `{since}`):

| File | Loại | Dòng |
|---|---|---|
''' + '\n'.join(lines) + ('\n\nCLI:\n' + '\n'.join(cli) if cli else '') + ('\n\n' + '\n'.join(les) if les else '') + '''

### Tương thích
- <lệnh cũ còn chạy như trước không? option nào để giữ hành vi cũ?>
''')


def check(since):
    files = [p for _, p in changed(since)]
    staged = git('diff', '--cached', '--name-only').split()
    relevant = [p for p in files + staged if p.startswith(TRACKED) and p != LOG]
    if relevant and LOG not in files + staged:
        print(f'✗ Skill có thay đổi ({", ".join(sorted(set(relevant)))}) nhưng {LOG} chưa được cập nhật.')
        print('  Chạy: python3 scripts/changelog.py draft  → điền Thay đổi / Lý do / So sánh trước-sau vào CHANGELOG.md')
        sys.exit(1)
    print('✓ CHANGELOG.md đã cập nhật (hoặc không có thay đổi cần ghi).')


def install_hook():
    hook = os.path.join(ROOT, '.git', 'hooks', 'pre-commit')
    with open(hook, 'w') as f:
        f.write('#!/bin/sh\n# Chặn commit thay đổi skill khi CHANGELOG.md chưa cập nhật (bỏ qua: git commit --no-verify)\n'
                'python3 "$(git rev-parse --show-toplevel)/scripts/changelog.py" check --since HEAD\n')
    os.chmod(hook, 0o755)
    print('Đã cài', hook)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['draft', 'check', 'install-hook'])
    ap.add_argument('--since', default='HEAD', help='mốc so sánh (commit/tag), mặc định commit gần nhất')
    a = ap.parse_args()
    {'draft': lambda: draft(a.since), 'check': lambda: check(a.since), 'install-hook': install_hook}[a.cmd]()


if __name__ == '__main__':
    main()
