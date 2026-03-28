# -*- coding: utf-8 -*-
"""
내부 링크 삽입 스크립트
각 글의 본문에서 다른 글 제목의 키워드를 찾아 내부 링크를 추가합니다.
"""

import os
import re
import json

BLOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'content', 'blog')

STOPWORDS = {
    '여행지', '여행', '정보', '방법', '이유', '추천', '비교', '소개', '특징',
    '이야기', '생각', '경험', '리뷰', '후기', '정리', '요약', '안내', '가이드',
    '장점', '단점', '차이', '선택', '결정', '준비', '확인', '관련', '기준',
    '종류', '내용', '지역', '나라', '도시', '장소', '위치', '지도', '면적',
    '인구', '문화', '역사', '날씨', '계절', '음식', '숙소', '호텔', '항공',
    '비용', '가격', '할인', '예약', '준비물', '짐싸기', '교통', '이동',
    '패키지', '자유', '여정', '일정', '코스', '루트', '포함', '추가',
    '국내', '해외', '한국', '세계', '아시아', '유럽', '아메리카', '아프리카',
    '최고', '최적', '최신', '최근', '처음', '마지막', '전통', '현대', '직접',
    '개인', '가족', '커플', '친구', '혼자', '투어', '어린이', '노인',
    '바다', '산', '도심', '자연', '도시', '마을', '섬나라',
}

def read_frontmatter(content):
    """YAML frontmatter 파싱"""
    if not content.startswith('---'):
        return {}, content
    end = content.find('\n---', 3)
    if end == -1:
        return {}, content
    fm_text = content[4:end]
    body = content[end+4:].lstrip('\n')
    fm = {}
    for line in fm_text.splitlines():
        if ':' in line:
            key, _, val = line.partition(':')
            fm[key.strip()] = val.strip().strip('"')
    return fm, body

def get_keywords(title):
    """제목에서 4글자 이상 한국어 키워드 추출"""
    clean = re.sub(r'\(.*?\)', '', title)
    clean = re.sub(r'[?!.,\[\]vs\+\-]+', ' ', clean)
    words = re.findall(r'[가-힣]{4,}', clean)
    result = []
    for w in words:
        if w not in STOPWORDS:
            result.append(w)
    # 중복 제거하되 순서 유지
    seen = set()
    unique = []
    for w in result:
        if w not in seen:
            seen.add(w)
            unique.append(w)
    return unique

def is_in_code_block(text, pos):
    """현재 위치가 코드 블록 안인지 확인"""
    before = text[:pos]
    code_blocks = before.count('```')
    return code_blocks % 2 == 1

def is_in_existing_link(text, pos):
    """현재 위치가 기존 링크 안인지 확인"""
    # [...](url) 패턴 내부인지
    before = text[:pos]
    after = text[pos:]
    # 닫힌 대괄호가 열린 것보다 많으면 링크 텍스트 안
    open_brackets = before.count('[') - before.count(']')
    if open_brackets > 0:
        return True
    # 직전에 ](/...  같은 패턴이 있는지 (링크 URL 안)
    if re.search(r'\]\([^)]*$', before):
        return True
    return False

def is_in_heading(text, pos):
    """현재 위치가 제목(##) 라인인지 확인"""
    line_start = text.rfind('\n', 0, pos) + 1
    line_content = text[line_start:pos]
    return line_content.strip().startswith('#')

def insert_links_in_body(body, links_to_add):
    """
    body 텍스트에 내부 링크를 첫 번째 등장 위치에 삽입
    links_to_add: [(keyword, url, title), ...]
    """
    result = body
    inserted_count = 0

    for keyword, url, link_title in links_to_add:
        if inserted_count >= 4:
            break

        # 이미 해당 url 링크가 있으면 스킵
        if url in result:
            continue

        # 키워드 첫 번째 등장 찾기 (단어 경계: 앞뒤가 한국어가 아닌 경우)
        pattern = keyword

        for m in re.finditer(re.escape(pattern), result):
            pos = m.start()
            end_pos = m.end()

            # 코드블록, 기존 링크, 제목 안이면 스킵
            if is_in_code_block(result, pos):
                continue
            if is_in_existing_link(result, pos):
                continue
            if is_in_heading(result, pos):
                continue

            # 삽입
            result = result[:pos] + f'[{keyword}]({url})' + result[end_pos:]
            inserted_count += 1
            break

    return result, inserted_count

def main():
    # 1. 모든 포스트 읽기
    posts = []
    for fname in sorted(os.listdir(BLOG_DIR)):
        if not fname.endswith('.md'):
            continue
        fpath = os.path.join(BLOG_DIR, fname)
        with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        fm, body = read_frontmatter(content)
        if not fm.get('title'):
            continue
        post_id = fname.replace('.md', '')
        entry_slug = fm.get('entry_slug', post_id)
        posts.append({
            'id': post_id,
            'title': fm.get('title', ''),
            'entry_slug': entry_slug,
            'category': fm.get('category', ''),
            'keywords': get_keywords(fm.get('title', '')),
            'body': body,
            'fm_raw': content[:len(content)-len(body)],  # frontmatter 포함 원본 헤더
            'fpath': fpath,
        })

    print(f"총 {len(posts)}개 포스트 로드 완료\n")

    # 2. 링크 후보 생성 (keyword → entry_slug 매핑)
    # 키워드 길이 기준 내림차순 정렬 (긴 키워드 우선)
    keyword_map = {}  # keyword -> (entry_slug, title)
    for p in posts:
        for kw in p['keywords']:
            if kw not in keyword_map:
                keyword_map[kw] = (f"/entry/{p['entry_slug']}", p['title'])

    # 3. 각 포스트에 링크 삽입
    total_links = 0
    modified_files = 0
    log = []

    for post in posts:
        body = post['body']

        # 이 포스트에 추가할 링크 후보 찾기
        candidates = []
        for kw, (url, link_title) in keyword_map.items():
            # 자기 자신 글로의 링크는 제외
            if f"/entry/{post['entry_slug']}" == url:
                continue
            if f"/entry/{post['id']}" == url:
                continue
            # 본문에 키워드가 있는지 확인
            if kw in body:
                # 이미 링크가 있는지 확인
                if url in body:
                    continue
                candidates.append((kw, url, link_title))

        if not candidates:
            continue

        # 키워드 길이 내림차순 (긴 것 우선), 최대 4개
        candidates.sort(key=lambda x: len(x[0]), reverse=True)
        candidates = candidates[:4]

        # 링크 삽입
        new_body, count = insert_links_in_body(body, candidates)

        if count > 0 and new_body != body:
            # 파일 쓰기
            # frontmatter 재구성
            original_content = open(post['fpath'], 'r', encoding='utf-8', errors='replace').read()
            fm_end = original_content.find('\n---', 3) + 4
            fm_part = original_content[:fm_end]
            new_content = fm_part + '\n' + new_body

            with open(post['fpath'], 'w', encoding='utf-8') as f:
                f.write(new_content)

            total_links += count
            modified_files += 1
            log.append({
                'file': post['id'],
                'title': post['title'],
                'links_added': count,
                'keywords': [c[0] for c in candidates[:count]]
            })
            print(f"✅ {post['id']}.md ({post['title'][:30]}...) → {count}개 링크 추가")

    print(f"\n🎉 완료! {modified_files}개 파일, 총 {total_links}개 내부 링크 추가")

    # 로그 저장
    log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'internal_links_log.json')
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(log, f, ensure_ascii=False, indent=2)
    print(f"📄 로그 저장: {log_path}")

if __name__ == '__main__':
    main()
