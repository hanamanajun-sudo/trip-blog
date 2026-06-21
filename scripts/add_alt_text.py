#!/usr/bin/env python3
"""
Script 2: 이미지 alt 텍스트 자동 생성
모든 .md 파일에서 alt가 비어있는 이미지에 한국어 alt 텍스트 채우기
"""

import re
import os
import glob

BLOG_DIR = "/home/user/trip-blog/src/content/blog"
MAX_ALT_LEN = 100


def parse_frontmatter(content):
    """Parse frontmatter and return (frontmatter_str, body_str, meta_dict)"""
    if not content.startswith("---"):
        return None, content, {}

    end = content.find("\n---", 3)
    if end == -1:
        return None, content, {}

    fm_str = content[:end + 4]
    body = content[end + 4:]

    meta = {}
    for line in fm_str.split("\n"):
        m = re.match(r'^(\w+):\s*"?(.*?)"?\s*$', line.strip())
        if m:
            meta[m.group(1)] = m.group(2).strip('"').strip("'")

    return fm_str, body, meta


def clean_heading(heading_text):
    """Remove markdown formatting from heading text"""
    # Remove **, *, __, _, ##, ###, etc.
    text = re.sub(r'\*+', '', heading_text)
    text = re.sub(r'_+', '', text)
    text = re.sub(r'#+\s*', '', text)
    # Remove markdown links [text](url)
    text = re.sub(r'\[([^\]]*)\]\([^\)]*\)', r'\1', text)
    return text.strip()


def find_preceding_heading(body, img_match_start):
    """
    Find the last H2 or H3 heading before img_match_start in body.
    Returns heading text (cleaned) or None.
    """
    text_before = body[:img_match_start]
    lines = text_before.split("\n")

    last_heading = None
    for line in lines:
        stripped = line.strip()
        # Match H2 or H3
        m = re.match(r'^#{2,3}\s+(.+)', stripped)
        if m:
            last_heading = clean_heading(m.group(1))

    return last_heading


def make_alt(title, heading):
    """Generate alt text from title and optional heading."""
    clean_title = re.sub(r'\[([^\]]*)\]\([^\)]*\)', r'\1', title)
    clean_title = clean_title.strip()

    if heading:
        alt = f"{clean_title} - {heading}"
    else:
        alt = f"{clean_title} 관련 이미지"

    # Trim to 100 chars
    if len(alt) > MAX_ALT_LEN:
        alt = alt[:MAX_ALT_LEN]

    return alt


def process_file(fpath, dry_run=False):
    """Process a single file. Returns (changed, num_replaced)."""
    with open(fpath, "r", encoding="utf-8") as f:
        original = f.read()

    fm_str, body, meta = parse_frontmatter(original)
    if fm_str is None:
        return False, 0

    title = meta.get("title", "")
    if not title:
        return False, 0

    # Pattern: ![]( /images/...) — empty alt, path starts with /images/
    # May have space before /images/ or not
    empty_alt_pattern = re.compile(r'!\[\]\(\s*(/images/[^\)]+)\)')

    count = len(empty_alt_pattern.findall(body))
    if count == 0:
        return False, 0

    replaced = 0
    new_body = body

    # We need to process replacements tracking offset shifts
    # Use finditer on the ORIGINAL body to find positions, then rebuild
    matches = list(empty_alt_pattern.finditer(body))

    # Process in reverse order to preserve positions
    for m in reversed(matches):
        img_path = m.group(1).strip()
        heading = find_preceding_heading(body, m.start())
        alt = make_alt(title, heading)

        replacement = f"![{alt}]({img_path})"
        new_body = new_body[:m.start()] + replacement + new_body[m.end():]
        replaced += 1

    if new_body == body:
        return False, 0

    if not dry_run:
        new_content = fm_str + new_body
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(new_content)

    return True, replaced


def main():
    print("=" * 60)
    print("작업 2: 이미지 alt 텍스트 자동 생성")
    print("=" * 60)

    files = sorted(glob.glob(os.path.join(BLOG_DIR, "*.md")))

    # Dry run
    print("\n--- 변경 예상 ---")
    total_files = 0
    total_imgs = 0
    for fpath in files:
        changed, num = process_file(fpath, dry_run=True)
        if changed:
            total_files += 1
            total_imgs += num
            fname = os.path.basename(fpath)
            print(f"  {fname}: {num}개 이미지 alt 추가 예정")

    print(f"\n예상: {total_files}개 파일, {total_imgs}건 alt 텍스트 추가")

    # Execute
    print("\n--- 실행 중 ---")
    done_files = 0
    done_imgs = 0
    for fpath in files:
        changed, num = process_file(fpath, dry_run=False)
        if changed:
            done_files += 1
            done_imgs += num

    print(f"\n완료: {done_files}개 파일, {done_imgs}건 alt 텍스트 추가")


if __name__ == "__main__":
    main()
