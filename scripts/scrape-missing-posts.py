#!/usr/bin/env python3
"""
Tistory 누락 글 자동 수집 스크립트
================================
사용법:
  1. PowerShell에서 아래 명령어 실행:
     pip install requests beautifulsoup4 html2text
  2. 스크립트 실행:
     python scripts/scrape-missing-posts.py
"""

import requests
import re
import os
import time
from urllib.parse import quote

MISSING_SLUGS = [
    "갠지스-호떡-왜-기름-색이-저럴까-이름의-유래",
    "나고야-최고급-리조트-어디-일본-여행",
    "넷플릭스-드라마-오자크는-어디주-오자크-정보",
    "동남아시아-여행하기-좋은-시기-몇월-평균기온",
    "발칸반도-위치와-발칸반도-나라들은",
    "세계4대-문명-어디야-지도-강-이름",
    "수에즈-운하-위치-어느나라-소유-역사-통행료-등-정보-모음",
    "열돔-현상-뜻-3줄-요약-원인",
    "이탈리아-친퀘테레-마을-여행-정보-모음가는법지도",
    "일본-열도라는데-열도-뜻-군도제도-차이",
    "일본-현-개수-각-현-종류-위치-특징",
    "파나마-운하-위치-어느나라-소유-역사-통행료-정보-모음",
    "프랑스-섬도시-몽생미셸-어디",
    "하트시그널3-롯데월드교복-대여어디-데이트-추천",
    "해외-호텔-예약-하기-팁-9가지-저렴하게-예약-방법-꿀팁",
    "해외미국-팁-얼마-줘야해-여행✈팁-문화-정리",
    "대만-숨은-여행지-일월담르웨탄-정보추천",
]

BASE_URL = "https://trip.lalalakorea.com/entry/"
OUTPUT_DIR = "src/content/blog"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'ko-KR,ko;q=0.9',
}


def fetch_post(slug):
    encoded = quote(slug, safe='-✈')
    url = BASE_URL + encoded
    print(f"  URL: {url}")
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.encoding = 'utf-8'
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"  ❌ 실패: {e}")
        return None


def parse_post(html, slug):
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, 'html.parser')

    # ── 제목: h2.title-article 또는 og:title ──
    title = None
    el = soup.select_one('h2.title-article')
    if el:
        title = el.get_text(strip=True)
    if not title:
        el = soup.select_one('meta[property="og:title"]')
        if el:
            title = el.get('content', '').split('::')[0].strip()
    if not title:
        title = slug.replace('-', ' ')

    # ── 날짜: article:published_time 메타태그 ──
    date = '2022-01-01'
    el = soup.select_one('meta[property="article:published_time"]')
    if el:
        raw = el.get('content', '')
        m = re.search(r'(\d{4})-(\d{2})-(\d{2})', raw)
        if m:
            date = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"

    # ── 카테고리: window.T.entryInfo의 categoryLabel ──
    category = '여행'
    m = re.search(r'"categoryLabel"\s*:\s*"([^"]+)"', html)
    if m:
        category = m.group(1)
    else:
        # 폴백: article-header 안의 p.category
        el = soup.select_one('.article-header p.category')
        if el:
            category = el.get_text(strip=True)

    # ── 본문: div.tt_article_useless_p_margin ──
    content_el = soup.select_one('div.tt_article_useless_p_margin')
    if not content_el:
        # 폴백
        for sel in ['.article-view .contents_style', '#article-view-content-div',
                    '.entry-content', '.tt_article_useless_p_br']:
            el = soup.select_one(sel)
            if el and len(el.get_text(strip=True)) > 50:
                content_el = el
                break

    if content_el:
        # 불필요한 요소 제거
        for tag in content_el.select('script, style, .another_category, .revenue_unit_wrap, ins, .ad-area, #ad_unit'):
            tag.decompose()

        try:
            import html2text
            h2t = html2text.HTML2Text()
            h2t.ignore_links = False
            h2t.ignore_images = False
            h2t.body_width = 0
            content_md = h2t.handle(str(content_el))
        except ImportError:
            # html2text 없을 때 기본 변환
            content_md = str(content_el)
            content_md = re.sub(r'<br\s*/?>', '\n', content_md)
            content_md = re.sub(r'<p[^>]*>', '\n', content_md)
            content_md = re.sub(r'</p>', '\n', content_md)
            content_md = re.sub(r'<h([1-6])[^>]*>(.*?)</h\1>', lambda m: '#' * int(m.group(1)) + ' ' + m.group(2) + '\n', content_md)
            content_md = re.sub(r'<[^>]+>', '', content_md)
            content_md = re.sub(r'\n{3,}', '\n\n', content_md)
    else:
        content_md = "<!-- 내용을 가져오지 못했습니다. Tistory에서 직접 복사해주세요. -->"

    return title, date, category, content_md.strip()


def save_post(num, slug, title, date, category, content):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, f"{num}.md")

    # 제목 내 따옴표 이스케이프
    title_safe = title.replace('"', '\\"')
    category_safe = category.replace('"', '\\"')

    frontmatter = f'''---
entry_slug: "{slug}"
title: "{title_safe}"
date: {date}
category: "{category_safe}"
---

{content}
'''
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(frontmatter)
    print(f"  ✅ 저장: {num}.md  ({title_safe[:40]})")


def get_start_number():
    # 117번부터 덮어쓰기 (잘못 생성된 파일 교체)
    return 117


# ── 메인 실행 ──
print("=" * 50)
print("  Tistory 누락 글 자동 수집")
print("=" * 50)
print()

next_num = get_start_number()
success = 0
fail = 0

for slug in MISSING_SLUGS:
    print(f"📥 [{next_num}] {slug}")
    html = fetch_post(slug)

    if html:
        title, date, category, content = parse_post(html, slug)
        save_post(next_num, slug, title, date, category, content)
        next_num += 1
        success += 1
    else:
        fail += 1
        print(f"  ⚠️  건너뜀 (나중에 수동으로 추가해주세요)")

    time.sleep(1)  # 서버 부하 방지
    print()

print("=" * 50)
print(f"  완료: 성공 {success}개 / 실패 {fail}개")
print()
print("다음 단계 (PowerShell):")
print('  git add src/content/blog/')
print('  git commit -m "누락 글 추가: Tistory에서 자동 수집"')
print('  git push')
print("=" * 50)
