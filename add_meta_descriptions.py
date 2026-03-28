# -*- coding: utf-8 -*-
"""
메타 description 일괄 추가 스크립트
각 글의 본문 첫 의미있는 문장에서 120~155자 description 자동 생성
"""

import os
import re

BLOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'content', 'blog')

def clean_text(text):
    """마크다운 제거 후 순수 텍스트 추출"""
    # 코드 블록 제거
    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'`[^`]+`', '', text)
    # 이미지 제거
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    # 링크 → 텍스트만 남기기
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    # 제목 # 제거
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    # HTML 태그 제거
    text = re.sub(r'<[^>]+>', '', text)
    # blockquote > 제거
    text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)
    # 굵게/기울임 * 제거
    text = re.sub(r'\*{1,3}([^*]+)\*{1,3}', r'\1', text)
    # 수평선 제거
    text = re.sub(r'^[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)
    # 불필요한 URL 제거
    text = re.sub(r'https?://\S+', '', text)
    # 여러 줄바꿈 → 공백
    text = re.sub(r'\n+', ' ', text)
    # 여러 공백 → 하나
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def generate_description(title, body_text, max_len=155):
    """본문에서 메타 description 생성"""
    cleaned = clean_text(body_text)

    # 너무 짧거나 의미없는 경우 제목 기반으로 생성
    if len(cleaned) < 20:
        return f"{title}에 대한 정보를 정리했습니다. 위치, 특징, 여행 정보까지 한눈에 확인하세요."[:max_len]

    # max_len 내에서 자르되 단어/문장 경계에서 자르기
    if len(cleaned) <= max_len:
        return cleaned

    # 문장 끝 기준으로 자르기 (마침표, 물음표, 느낌표)
    sentence_end = re.search(r'[.。!?！？]', cleaned[60:max_len-10])
    if sentence_end:
        cut_pos = 60 + sentence_end.end()
        return cleaned[:cut_pos].strip()

    # 쉼표 기준
    comma_pos = cleaned.rfind(',', 80, max_len - 5)
    if comma_pos > 0:
        return cleaned[:comma_pos].strip() + '.'

    # 공백 기준 (단어 중간 자르기 방지)
    space_pos = cleaned.rfind(' ', 100, max_len - 5)
    if space_pos > 0:
        return cleaned[:space_pos].strip() + '.'

    return cleaned[:max_len-1].strip() + '.'

def read_frontmatter_and_body(content):
    """frontmatter와 body 분리"""
    if not content.startswith('---'):
        return None, None, content
    end = content.find('\n---', 3)
    if end == -1:
        return None, None, content
    fm_text = content[4:end]
    body = content[end+4:].lstrip('\n')
    return fm_text, end, body

def add_description_to_frontmatter(content, description):
    """frontmatter에 description 필드 추가"""
    if not content.startswith('---'):
        return content

    end = content.find('\n---', 3)
    if end == -1:
        return content

    fm_part = content[:end]
    rest = content[end:]

    # description 이스케이프 처리 (따옴표 포함시)
    desc_escaped = description.replace('"', '\\"')

    # category 줄 다음에 삽입 (없으면 frontmatter 끝에)
    if 'category:' in fm_part:
        cat_end = fm_part.find('\n', fm_part.find('category:'))
        if cat_end == -1:
            cat_end = len(fm_part)
        new_fm = fm_part[:cat_end] + f'\ndescription: "{desc_escaped}"' + fm_part[cat_end:]
    else:
        new_fm = fm_part + f'\ndescription: "{desc_escaped}"'

    return new_fm + rest

def main():
    files = sorted([f for f in os.listdir(BLOG_DIR) if f.endswith('.md')])
    total = len(files)
    added = 0
    skipped = 0

    print(f"총 {total}개 파일 처리 시작...\n")

    results = []

    for fname in files:
        fpath = os.path.join(BLOG_DIR, fname)
        with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()

        # 이미 description 있으면 스킵
        fm_text, end_pos, body = read_frontmatter_and_body(content)
        if fm_text is None:
            skipped += 1
            continue

        if 'description:' in fm_text:
            skipped += 1
            continue

        # 제목 추출
        title_match = re.search(r'^title:\s*"?([^"\n]+)"?', fm_text, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else ''

        # description 생성
        description = generate_description(title, body)

        # 너무 짧으면 제목으로 보완
        if len(description) < 30:
            description = f"{title} - 위치, 면적, 인구, 특징, 여행 정보를 한눈에 정리했습니다."[:155]

        # frontmatter에 추가
        new_content = add_description_to_frontmatter(content, description)

        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(new_content)

        added += 1
        results.append({'file': fname, 'desc': description})
        print(f"✅ {fname}: {description[:60]}...")

    print(f"\n🎉 완료! {added}개 파일에 description 추가 ({skipped}개 스킵)")

    # 결과 샘플 출력
    print("\n📋 생성된 description 샘플 (처음 5개):")
    for r in results[:5]:
        print(f"  [{r['file']}] ({len(r['desc'])}자) {r['desc']}")

if __name__ == '__main__':
    main()
