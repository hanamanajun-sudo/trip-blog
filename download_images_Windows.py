# -*- coding: utf-8 -*-
#!/usr/bin/env python3
r"""
🖼️ Tistory 이미지 로컬 저장 스크립트 (Windows 버전)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
실행 방법:
  1. PowerShell 또는 CMD 열기
  2. trip-blog 폴더로 이동
  3. 스크립트 실행:
     python download_images_Windows.py
"""

import os
import re
import json
import hashlib
import urllib.request
import urllib.error
from pathlib import Path

# ─── 경로 설정 (자동 감지, Windows 호환) ───────────────────────────────
SCRIPT_DIR = Path(__file__).parent.resolve()
BLOG_DIR = SCRIPT_DIR / "src" / "content" / "blog"
PUBLIC_IMAGES = SCRIPT_DIR / "public" / "images"
JSON_FILE = SCRIPT_DIR / "tistory_images_to_download.json"

print(f"📁 스크립트 위치: {SCRIPT_DIR}")
print(f"📁 블로그 파일: {BLOG_DIR}")
print(f"📁 이미지 저장: {PUBLIC_IMAGES}\n")

# 경로 존재 확인
if not BLOG_DIR.exists():
    print("❌ 오류: src/content/blog 폴더가 없어요!")
    print(f"   현재 위치: {SCRIPT_DIR}")
    print("   trip-blog 폴더 안에서 실행해주세요.")
    exit(1)

CDN_PATTERN = re.compile(
    r'(https?://(?:blog\.kakaocdn\.net|img\d*\.daumcdn\.net|[^/]*tistory[^/]*\.net)[^\s\)\"\'\]]+)',
    re.IGNORECASE
)
EXT_PATTERN = re.compile(r'/img\.(jpg|jpeg|png|gif|webp)', re.IGNORECASE)

def get_extension(url):
    m = EXT_PATTERN.search(url)
    if m:
        return '.' + m.group(1).lower()
    path = url.split('?')[0]
    if '.' in path.split('/')[-1]:
        ext = path.split('/')[-1].rsplit('.', 1)[-1].lower()
        if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
            return '.' + ext
    return '.png'

def get_filename(url):
    clean_url = url.split('?')[0]
    h = hashlib.md5(clean_url.encode()).hexdigest()[:8]
    return h + get_extension(url)

def download_image(url, dest_path):
    """이미지 다운로드"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Referer': 'https://www.tistory.com/',
        'Accept': 'image/avif,image/webp,image/apng,image/*,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9',
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        print(f"    ⬇️  다운로드 중...", end=" ", flush=True)
        with urllib.request.urlopen(req, timeout=20) as resp:
            content = resp.read()
            if len(content) < 500:
                print(f"\r    ❌ 실패: 파일 너무 작음 ({len(content)}bytes)")
                return False, f"파일 너무 작음"
            with open(dest_path, 'wb') as f:
                f.write(content)
            size_kb = len(content) // 1024
            print(f"\r    ✅ 저장됨: {size_kb}KB")
            return True, f"{size_kb}KB"
    except urllib.error.HTTPError as e:
        print(f"\r    ❌ HTTP {e.code} 오류")
        return False, f"HTTP {e.code}"
    except urllib.error.URLError as e:
        print(f"\r    ❌ 연결 오류")
        return False, f"연결 오류"
    except Exception as e:
        print(f"\r    ❌ 오류: {str(e)[:40]}")
        return False, str(e)[:40]

def replace_urls_in_file(md_file, url_map):
    """마크다운 파일에서 CDN URL을 로컬 경로로 교체"""
    content = md_file.read_text(encoding='utf-8')
    original = content
    for cdn_url, local_path in url_map.items():
        content = content.replace(cdn_url, local_path)
    if content != original:
        md_file.write_text(content, encoding='utf-8')
        return True
    return False

def main():
    print("=" * 70)
    print("🖼️  Tistory CDN 이미지 로컬 저장 시작 (Windows)")
    print("=" * 70 + "\n")

    # JSON 파일에서 URL 목록 읽기
    if not JSON_FILE.exists():
        print("❌ tistory_images_to_download.json 파일이 없어요!")
        print(f"   찾는 위치: {JSON_FILE}")
        print("   trip-blog 폴더 안에 있는지 확인해주세요.")
        return

    try:
        data = json.loads(JSON_FILE.read_text(encoding='utf-8'))
    except json.JSONDecodeError:
        print("❌ JSON 파일이 손상되었어요. 다시 생성해보세요.")
        return

    total_images = sum(len(v) for v in data.values())
    print(f"📋 처리 대상: {len(data)}개 파일, {total_images}개 이미지\n")

    total_success = 0
    total_fail = 0
    total_skip = 0
    fail_list = []

    for file_num, images in sorted(data.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 999):
        md_file = BLOG_DIR / f"{file_num}.md"
        if not md_file.exists():
            print(f"⚠️  {file_num}.md 파일 없음\n")
            continue

        img_dir = PUBLIC_IMAGES / file_num
        img_dir.mkdir(parents=True, exist_ok=True)

        print(f"📄 {file_num}.md ({len(images)}개 이미지)")

        url_map = {}
        file_success = 0
        file_fail = 0

        for idx, item in enumerate(images, 1):
            url = item['url']
            filename = item['filename']
            dest_path = img_dir / filename
            local_path = f"/images/{file_num}/{filename}"

            # 이미 존재하면 스킵
            if dest_path.exists() and dest_path.stat().st_size > 500:
                print(f"  [{idx}/{len(images)}] ⏭️  이미 있음: {filename}")
                url_map[url] = local_path
                total_skip += 1
                file_success += 1
                continue

            print(f"  [{idx}/{len(images)}] {filename}")
            ok, info = download_image(url, dest_path)
            if ok:
                url_map[url] = local_path
                total_success += 1
                file_success += 1
            else:
                fail_list.append(f"{file_num}.md / {filename}: {info}")
                total_fail += 1
                file_fail += 1

        # URL 교체
        if url_map:
            changed = replace_urls_in_file(md_file, url_map)
            if changed:
                print(f"  ✏️  {file_num}.md URL 교체 완료 ({file_success}개 이미지)\n")
            else:
                print(f"  ℹ️  {file_num}.md URL 교체됨\n")

    print("\n" + "=" * 70)
    print(f"✅ 완료!")
    print(f"   ✓ 성공: {total_success}개 다운로드")
    print(f"   ⏭️  스킵: {total_skip}개 (이미 존재)")
    print(f"   ❌ 실패: {total_fail}개")

    if fail_list:
        print(f"\n⚠️  실패한 이미지:")
        for f in fail_list[:10]:
            print(f"   - {f}")
        if len(fail_list) > 10:
            print(f"   ... 외 {len(fail_list) - 10}개")
        print("\n💡 해결 방법:")
        print("   1. 인터넷 연결 확인")
        print("   2. VPN 사용 시 끄고 다시 시도")
        print("   3. 다시 실행 (실패한 것만 자동으로 재시도됨)")
    else:
        print("\n🎉 모든 이미지 저장 완료!")
        print("\n📝 다음 단계:")
        print("   1. PowerShell에서 실행:")
        print("      git add .")
        print("      git commit -m '이미지 로컬 저장 (137개)'")
        print("   2. 또는 VS Code에서 Source Control에서 커밋")

    print("=" * 70)

if __name__ == "__main__":
    main()
