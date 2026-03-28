# -*- coding: utf-8 -*-
"""
블로그 글 오류 일괄 수정 스크립트

1. **** 별표 패턴 수정 (굵게 태그 충돌로 생긴 잔여 **가 화면에 그대로 노출되는 문제)
2. 티스토리 관련글 링크 → 깔끔한 관련 글 박스로 변환
3. null 바이트 / 깨진 문자 제거
"""

import os
import re

BLOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'content', 'blog')


# ─────────────────────────────────────────────────────────────
# 1. **** 별표 패턴 수정
# ─────────────────────────────────────────────────────────────
def fix_asterisks(text):
    """
    **bold1****bold2** → **bold1 bold2**
    **bold** **bold** (연속 굵게) → 하나로 합치기
    ****text**** → **text**
    """
    # 패턴: 닫는 ** 바로 다음에 여는 ** (공백 없이 또는 공백 포함)
    # **A****B** → **A B**
    # 반복 적용
    result = text

    # 1) ****를 ' ' 또는 ''로 교체 (heading 내부에서)
    # ** 뒤에 ** 가 바로 오면 제거 (중간 연결)
    result = re.sub(r'\*\*\*\*', '**SPLIT**', result)

    # **SPLIT** 이 heading 내에서 **...** 패턴 사이에 있으면 공백으로
    # 예: ### **텍스트**SPLIT****텍스트** → ### **텍스트 텍스트**
    # 전체 bold 패턴 내에서 **SPLIT** 처리

    # 우선 전체에서 **SPLIT** → 공백으로
    result = result.replace('**SPLIT**', ' ')

    # 중복 공백 정리 (heading 줄에서만)
    lines = result.splitlines()
    fixed_lines = []
    for line in lines:
        if line.strip().startswith('#') or '**' in line:
            # 여러 공백을 하나로
            line = re.sub(r'  +', ' ', line)
            # ** ** (빈 bold) 제거
            line = re.sub(r'\*\* \*\*', ' ', line)
            # 닫는 ** 바로 다음 여는 ** → 공백
            line = re.sub(r'\*\*([^*\n]+)\*\* \*\*([^*\n]+)\*\*', r'**\1 \2**', line)
            # 여전히 남아있는 **** → 제거
            line = re.sub(r'\*\*\*\*', '', line)
        fixed_lines.append(line)

    return '\n'.join(fixed_lines)


# ─────────────────────────────────────────────────────────────
# 2. 티스토리 관련글 링크 정리
# ─────────────────────────────────────────────────────────────
def fix_tistory_links(text):
    """
    [2022.04.28 - [지구 상식] - 글제목](url)
    → > 📌 **관련 글**: [글제목](내부경로)

    trip.lalalakorea.com URL → 내부 /entry/ 상대경로로 변환
    """
    result = text

    # "블로그 내 관련글" 헤더 제거 (단독 줄)
    result = re.sub(r'\n\*?\*?\[?블로그 내 관련글\]?\*?\*?\n', '\n', result)
    result = re.sub(r'\n> 블로그 내 관련글 추천\s*\n', '\n', result)

    # [날짜 - [카테고리] - 글제목](url) 패턴 변환
    # 예: [2022.04.28 - [지구 상식] - 우루과이 vs 한국 비교()](https://trip.lalalakorea.com/entry/...)
    def replace_tistory_link(m):
        date_cat_title = m.group(1)  # "2022.04.28 - [지구 상식] - 글제목"
        url = m.group(2)

        # 제목만 추출 (마지막 " - " 이후)
        title_match = re.search(r' - ([^-].+)$', date_cat_title)
        if title_match:
            title = title_match.group(1).strip()
        else:
            title = date_cat_title

        # trip.lalalakorea.com URL → /entry/... 상대경로
        url = re.sub(r'https://trip\.lalalakorea\.com', '', url)

        return f'\n> 📌 **관련 글**: [{title}]({url})\n'

    # 패턴 1: [날짜 - [카테고리] - 제목](url)
    result = re.sub(
        r'\[(\d{4}\.\d{2}\.\d{2} - \[.+?\] - [^\]]+)\]\((https://trip\.lalalakorea\.com[^)]+)\)',
        replace_tistory_link,
        result
    )

    # 패턴 2: blockquote 안에 있는 경우 > [날짜...](url)
    result = re.sub(
        r'> \[(\d{4}\.\d{2}\.\d{2} - \[.+?\] - [^\]]+)\]\((https://trip\.lalalakorea\.com[^)]+)\)',
        replace_tistory_link,
        result
    )

    # 연속된 관련글 줄바꿈 정리
    result = re.sub(r'(\n> 📌[^\n]+\n)\n+(\n> 📌)', r'\1\2', result)

    return result


# ─────────────────────────────────────────────────────────────
# 3. null 바이트 / 깨진 문자 제거
# ─────────────────────────────────────────────────────────────
def fix_null_bytes(raw_bytes):
    """null 바이트 제거 후 UTF-8 디코딩"""
    # null 바이트 제거
    cleaned = raw_bytes.replace(b'\x00', b'')
    # UTF-8 디코딩 (오류 무시)
    return cleaned.decode('utf-8', errors='replace')


def remove_broken_chars(text):
    """대체 문자(U+FFFD) 연속된 것 제거"""
    # 3개 이상 연속된 대체 문자 제거
    text = re.sub(r'(\ufffd){2,}', '', text)
    # 홀로 남은 1개도 제거
    text = text.replace('\ufffd', '')
    return text


# ─────────────────────────────────────────────────────────────
# 메인 처리
# ─────────────────────────────────────────────────────────────
def process_file(fpath):
    """파일 읽고 3가지 수정 적용"""
    # raw bytes로 읽기 (null 바이트 처리 위해)
    raw = open(fpath, 'rb').read()

    # 3. null 바이트 먼저 제거
    text = fix_null_bytes(raw)

    # 깨진 문자 제거
    text = remove_broken_chars(text)

    # 1. **** 별표 수정
    text = fix_asterisks(text)

    # 2. 티스토리 관련글 링크 정리
    text = fix_tistory_links(text)

    # 끝부분 불필요한 공백 정리
    text = text.rstrip() + '\n'

    return text


def main():
    files = sorted([f for f in os.listdir(BLOG_DIR) if f.endswith('.md')])
    modified = 0

    print(f"총 {len(files)}개 파일 처리 시작...\n")

    for fname in files:
        fpath = os.path.join(BLOG_DIR, fname)

        original_raw = open(fpath, 'rb').read()
        original_text = original_raw.decode('utf-8', errors='replace')

        new_text = process_file(fpath)

        if new_text != original_text:
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(new_text)

            # 변경 내용 요약
            changes = []
            if b'\x00' in original_raw:
                null_count = original_raw.count(b'\x00')
                changes.append(f'null bytes 제거({null_count}개)')
            if '\ufffd' in original_text:
                changes.append('깨진문자 제거')
            if '****' in original_text:
                changes.append('**** 수정')
            if re.search(r'\d{4}\.\d{2}\.\d{2} - \[', original_text):
                changes.append('티스토리링크 정리')

            print(f"✅ {fname}: {', '.join(changes) if changes else '공백/포맷 정리'}")
            modified += 1

    print(f"\n🎉 완료! {modified}개 파일 수정됨")


if __name__ == '__main__':
    main()
