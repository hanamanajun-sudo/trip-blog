#!/usr/bin/env python3
"""
Script 1: 나라 비교 글 내부링크 강화
각 나라 비교 글의 본문에서 다른 나라 이름이 평문으로 나올 때 해당 글로 링크 추가
"""

import re
import os
import glob

BLOG_DIR = "/home/user/trip-blog/src/content/blog"

def parse_frontmatter(content):
    """Parse frontmatter and return (frontmatter_str, body_str, meta_dict)"""
    if not content.startswith("---"):
        return None, content, {}

    end = content.find("\n---", 3)
    if end == -1:
        return None, content, {}

    fm_str = content[:end + 4]  # include closing ---
    body = content[end + 4:]

    meta = {}
    for line in fm_str.split("\n"):
        m = re.match(r'^(\w+):\s*"?(.*?)"?\s*$', line.strip())
        if m:
            meta[m.group(1)] = m.group(2).strip('"').strip("'")

    return fm_str, body, meta


def extract_country_name(title):
    """
    Extract country name from title like 'OO vs 한국 비교(...)'
    Returns country name or None
    """
    # Match patterns like '나라 vs 한국' or '나라이름 vs 한국'
    m = re.match(r'^(.+?)\s+vs\s+한국', title)
    if m:
        country = m.group(1).strip()
        return country
    return None


def build_country_mapping(blog_dir):
    """
    Build {country_name: /entry/slug} mapping from all vs-Korea posts
    """
    mapping = {}
    files = glob.glob(os.path.join(blog_dir, "*.md"))

    for fpath in files:
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()

        fm_str, body, meta = parse_frontmatter(content)
        if not meta:
            continue

        title = meta.get("title", "")
        country = extract_country_name(title)
        if not country:
            continue

        # Get slug from entry_slug, falling back to file id
        entry_slug = meta.get("entry_slug", "")
        if entry_slug:
            slug = entry_slug
        else:
            # Use file basename without extension
            slug = os.path.splitext(os.path.basename(fpath))[0]

        url = f"/entry/{slug}"
        mapping[country] = url

    return mapping


def add_links_to_body(body, country_map, current_country):
    """
    Add internal links to country names in body text.
    - Skip current country
    - Skip already-linked occurrences
    - Skip headings
    - Link only first occurrence per country
    - Don't link partial words (preceded/followed by Korean or alpha chars)
    """
    lines = body.split("\n")
    result_lines = []
    linked_countries = set()  # track which have been linked already

    for line in lines:
        # Skip heading lines
        stripped = line.lstrip()
        if stripped.startswith("#"):
            result_lines.append(line)
            continue

        # Process each country that hasn't been linked yet
        new_line = line
        for country, url in country_map.items():
            if country == current_country:
                continue
            if country in linked_countries:
                continue

            # Check if this country appears (unlinked) in this line
            # Pattern: country name not preceded/followed by Korean or alpha chars
            # and not already inside [...](...)

            # We need to find raw occurrences not inside a markdown link
            # Strategy: scan for country name occurrences, check context

            # Build a pattern that matches the country not already in a link
            # Negative lookbehind for [ and ] to avoid matching inside link text
            # Also check word boundaries for Korean/alpha

            pattern = re.compile(
                r'(?<!\[)(?<!\]\()(?<!\w)' + re.escape(country) + r'(?!\w)(?!\])'
            )

            # Also need to avoid matching inside existing [...](...)
            # Let's do it by finding all positions and checking if they're inside a link

            def is_inside_link(text, start, end):
                """Check if position start..end is inside an existing markdown link"""
                # Find all markdown links in the text
                for m in re.finditer(r'\[([^\]]*)\]\([^\)]*\)', text):
                    if m.start() <= start and end <= m.end():
                        return True
                # Also check if it's inside URL part [...]( HERE )
                for m in re.finditer(r'\]\(([^\)]*)\)', text):
                    if m.start(1) <= start and end <= m.end(1):
                        return True
                return False

            # Find first occurrence not inside a link
            found_pos = None
            for m in pattern.finditer(new_line):
                if not is_inside_link(new_line, m.start(), m.end()):
                    found_pos = m
                    break

            if found_pos:
                # Replace only this first occurrence
                start = found_pos.start()
                end = found_pos.end()
                replacement = f"[{country}]({url})"
                new_line = new_line[:start] + replacement + new_line[end:]
                linked_countries.add(country)

        result_lines.append(new_line)

    return "\n".join(result_lines)


def process_file(fpath, country_map, dry_run=False):
    """Process a single file. Returns (changed, num_links_added)."""
    with open(fpath, "r", encoding="utf-8") as f:
        original = f.read()

    fm_str, body, meta = parse_frontmatter(original)
    if fm_str is None:
        return False, 0

    title = meta.get("title", "")
    current_country = extract_country_name(title)

    # Only process vs-Korea posts
    if not current_country:
        return False, 0

    new_body = add_links_to_body(body, country_map, current_country)

    if new_body == body:
        return False, 0

    # Count added links
    added = 0
    for country in country_map:
        if country == current_country:
            continue
        url = country_map[country]
        link_pattern = f"[{country}]({url})"
        # Count how many new links were added
        in_new = new_body.count(link_pattern)
        in_old = body.count(link_pattern)
        added += max(0, in_new - in_old)

    if not dry_run:
        new_content = fm_str + new_body
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(new_content)

    return True, added


def main():
    print("=" * 60)
    print("작업 1: 나라 비교 글 내부링크 강화")
    print("=" * 60)

    # Build country mapping
    country_map = build_country_mapping(BLOG_DIR)
    print(f"\n매핑된 나라 수: {len(country_map)}개")
    for country, url in sorted(country_map.items()):
        print(f"  {country} → {url}")

    files = sorted(glob.glob(os.path.join(BLOG_DIR, "*.md")))

    # Dry run first
    print("\n--- 변경 예상 ---")
    total_files = 0
    total_links = 0
    for fpath in files:
        changed, num = process_file(fpath, country_map, dry_run=True)
        if changed:
            total_files += 1
            total_links += num
            fname = os.path.basename(fpath)
            print(f"  {fname}: +{num}개 링크 예정")

    print(f"\n예상: {total_files}개 파일, {total_links}건 링크 추가")

    # Actually process
    print("\n--- 실행 중 ---")
    done_files = 0
    done_links = 0
    for fpath in files:
        changed, num = process_file(fpath, country_map, dry_run=False)
        if changed:
            done_files += 1
            done_links += num

    print(f"\n완료: {done_files}개 파일, {done_links}건 링크 추가")


if __name__ == "__main__":
    main()
