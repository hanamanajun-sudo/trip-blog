#!/usr/bin/env python3
"""
빌드 후 한국어 URL 경로에 페이지 복사
예: dist/116/index.html → dist/entry/8000미터가-.../index.html
"""
import os, re, shutil

blog_dir = "src/content/blog"
dist_dir = "dist"
count = 0

for filename in sorted(os.listdir(blog_dir)):
    if not filename.endswith('.md'):
        continue
    numeric_slug = filename[:-3]

    with open(f"{blog_dir}/{filename}", 'r', encoding='utf-8') as f:
        content = f.read()

    match = re.search(r'^entry_slug:\s*["\']?([^"\'}\n]+)["\']?', content, re.MULTILINE)
    if not match:
        continue

    entry_slug = match.group(1).strip()

    # 숫자 slug와 같으면 이미 entry/[slug].astro가 처리함
    if entry_slug == numeric_slug:
        continue

    src_html = f"{dist_dir}/{numeric_slug}/index.html"
    dst_dir_path = f"{dist_dir}/entry/{entry_slug}"
    dst_html = f"{dst_dir_path}/index.html"

    if not os.path.exists(src_html):
        print(f"SKIP (source not found): {src_html}")
        continue

    os.makedirs(dst_dir_path, exist_ok=True)
    shutil.copy2(src_html, dst_html)
    count += 1
    print(f"OK: /entry/{entry_slug}")

print(f"\n총 {count}개 한국어 URL 페이지 생성 완료")
