#!/usr/bin/env python3
"""
Post-processing: 
1. Build proper filename mapping for unknown-* files
2. Rename files + update markdown references
3. Retry 12 failed items with better searches
"""

import json, os, re, time, requests
from pathlib import Path

REPO = Path(os.environ.get("TEMP", "")) / "trip-blog"
TODO_JSON = REPO / "docs" / "photo-todo.json"
PUBLIC_IMAGES = REPO / "public" / "images"
BLOG_DIR = REPO / "src" / "content" / "blog"

HEADERS = {"User-Agent": "TripBlogBot/1.0 (https://trip.lalalakorea.com)"}

# 한글 국가명 → 영문 매핑
COUNTRY_MAP = {
    "가나": "ghana", "네덜란드": "netherlands", "독일": "germany",
    "멕시코": "mexico", "미국": "usa", "벨기에": "belgium",
    "보스니아": "bosnia", "브라질": "brazil", "사우디": "saudi",
    "사우디아라비아": "saudi", "세네갈": "senegal",
    "스코틀랜드": "scotland", "알제리": "algeria", "에콰도르": "ecuador",
    "요르단": "jordan", "우즈베키스탄": "uzbekistan", "이라크": "iraq",
    "이집트": "egypt", "체코": "czech", "카보베르데": "cape-verde",
    "코트디부아르": "ivory-coast", "콜롬비아": "colombia",
    "쿠라사오": "curacao", "튀니지": "tunisia", "파나마": "panama",
    "파라과이": "paraguay",
}

# alt 텍스트 기반 role 추출
ROLE_KEYWORDS = {
    "hero": ["hero"],
    "food": ["음식", "요리", "먹", "food", "브라트부어스트", "푸푸", "타코", "버거", "홍합", "체바피",
             "슈하스코", "카브사", "티에부젠", "쿠스쿠스", "세비체", "만사프", "플로프", "마스구프",
             "팔라펠", "카샤파", "카리만욜라", "소파"],
    "football": ["축구", "경기장", "스타디움", "유니폼", "football", "stadium"],
    "city": ["수도", "도심", "시내", "시가지", "city", "거리", "街"],
    "landmark": ["성", "castle", "피라미드", "pyramid", "사원", "신전", "랜드마크"],
    "nature": ["사막", "desert", "산맥", "강", "river", "열대우림", "amazon", "highland", "커피 농장", "해안"],
    "map": ["지도", "지형", "위치", "크기 비교"],
    "square": ["광장", "square"],
    "bridge": ["다리", "교", "bridge"],
    "coast": ["해안", "coast", "해변"],
    "canal": ["운하", "canal"],
}

def extract_country_from_post(post_filename: str) -> str | None:
    """블로그 글 파일명에서 국가명 추출"""
    for kr, en in COUNTRY_MAP.items():
        if kr in post_filename:
            return en
    return None

def extract_role_from_alt(alt_text: str, kind: str) -> str:
    if kind == "hero":
        return "hero"
    for role, kws in ROLE_KEYWORDS.items():
        if role == "hero":
            continue
        for kw in kws:
            if kw.lower() in alt_text.lower():
                return role
    return "photo"

def read_todo():
    return json.loads(TODO_JSON.read_text(encoding="utf-8"))

def step1_rename_unknown():
    """unknown-*.jpg → 올바른 국가명으로 rename + 마크다운 수정"""
    todo = read_todo()
    targets = [t for t in todo if t["kind"] != "location-map"]
    
    # 각 항목별 proper filename 생성
    used_names = set()
    rename_map = {}  # old unknown name → new proper name
    blog_updates = []  # (post_file, old_path, new_path)
    
    for item in targets:
        old_path = item["path"]
        basename = os.path.basename(old_path).replace("placeholder-", "", 1)
        basename = os.path.splitext(basename)[0]
        
        # 한글 포함 여부
        has_korean = bool(re.search(r'[\uac00-\ud7af]', basename))
        if not has_korean:
            continue  # 이미 올바른 영문명
        
        # 국가명 추출
        country = extract_country_from_post(item["post"])
        if not country:
            country = "unknown"
        
        role = extract_role_from_alt(item["alt"], item["kind"])
        
        base = f"{country}-{role}"
        filename = f"{base}.jpg"
        if filename in used_names:
            idx = 2
            while f"{base}-{idx}.jpg" in used_names:
                idx += 1
            filename = f"{base}-{idx}.jpg"
        used_names.add(filename)
        
        new_path = f"/images/{filename}"
        blog_updates.append((item["post"], item["path"], new_path))
        
        # Find the unknown file that matches this item
        # We don't know the exact unknown filename, so we search by old_path in blog content
        rename_map[item["path"]] = (filename, country, role)
    
    # Now rename and update markdown
    for post_name, old_placeholder, new_web_path in blog_updates:
        post_file = BLOG_DIR / post_name
        if not post_file.exists():
            continue
        content = post_file.read_text(encoding="utf-8")
        
        # Find the specific placeholder in content
        if old_placeholder not in content:
            continue
        
        # Extract the old web path currently in the file (might be unknown-*.jpg)
        # Pattern: ![alt](/images/unknown-xxx.jpg)
        lines = content.split("\n")
        new_lines = []
        skip_next = False
        changed = False
        
        for i, line in enumerate(lines):
            if skip_next:
                skip_next = False
                continue
            # TODO + placeholder pair
            if re.match(r"\s*<!--\s*TODO", line) and i + 1 < len(lines):
                if old_placeholder in lines[i + 1]:
                    new_img = lines[i + 1].replace(lines[i + 1].split("](")[1].rstrip(")"), new_web_path)
                    # Extract the full path from the markdown
                    import re as re2
                    current_path_match = re2.search(r'\]\(([^)]+)\)', lines[i + 1])
                    if current_path_match:
                        old_ref = current_path_match.group(1)
                        new_line = lines[i + 1].replace(old_ref, new_web_path)
                        new_lines.append(new_line)
                    else:
                        new_lines.append(lines[i + 1])
                    skip_next = True
                    changed = True
                    continue
            
            # Direct replacement
            if old_placeholder in line:
                import re as re2
                current_path_match = re2.search(r'\]\(([^)]+)\)', line)
                if current_path_match:
                    old_ref = current_path_match.group(1)
                    line = line.replace(old_ref, new_web_path)
                    changed = True
            
            new_lines.append(line)
        
        if changed:
            post_file.write_text("\n".join(new_lines), encoding="utf-8")
            print(f"  ✅ {post_name} — 참조 업데이트: {new_web_path}")
    
    # Rename files: we need to figure out which unknown-*.jpg maps to which item
    # Scan blog content for current unknown references
    print("\n--- 현재 블로그 글의 unknown 참조 스캔 ---")
    unknown_refs = {}  # post_name → current_image_path
    for post_name, _, new_web_path in blog_updates:
        post_file = BLOG_DIR / post_name
        if not post_file.exists():
            continue
        content = post_file.read_text(encoding="utf-8")
        # Find unknown-*.jpg refs
        refs = re.findall(r'/images/unknown-[\w-]+\.jpg', content)
        for ref in refs:
            unknown_refs[os.path.basename(ref)] = new_web_path
    
    # Rename files
    for unknown_basename, new_web_path in unknown_refs.items():
        old_file = PUBLIC_IMAGES / unknown_basename
        new_file = PUBLIC_IMAGES / os.path.basename(new_web_path)
        if old_file.exists() and not new_file.exists():
            old_file.rename(new_file)
            print(f"  📄 {unknown_basename} → {os.path.basename(new_web_path)}")
        elif old_file.exists() and new_file.exists():
            # Target exists, just use the new one
            old_file.unlink()
            print(f"  🗑️ {unknown_basename} 삭제 (중복)")


def generate_better_query(alt_text: str, kind: str) -> list:
    """실패한 항목을 위한 대체 검색어 목록"""
    queries = []
    
    korean_food_english = {
        "브라질식 바비큐 슈하스코": ["Brazilian BBQ churrasco meat", "Brazilian barbecue restaurant", "churrascaria Brazil"],
        "사우디아라비아 전통 음식 카브사": ["Arabic rice meat dish", "Saudi Arabian cuisine mandi", "Middle Eastern rice lamb"],
        "보스니아 전통 음식 체바피": ["Balkan grilled meat cevapi", "Bosnian meat sausages", "Balkan cuisine grilled"],
        "요르단 전통 요리 만사프": ["Middle Eastern rice lamb dish", "Jordanian mansaf rice", "Arabian lamb rice"],
        "이집트 전통 음식 풀 메다메스와 팔라펠": ["Egyptian falafel ful medames", "Middle Eastern breakfast falafel", "Egyptian street food"],
        "이라크 전통 생선 구이 마스구프": ["Iraqi grilled fish masgouf", "Middle Eastern grilled fish", "Tigris river fish"],
        "카보베르데 전통 스튜 요리 카샤파": ["Cape Verde stew cachupa", "African stew corn beans", "Cape Verdean cuisine"],
        "파나마 전통 음식 카리만욜라": ["Panamanian food carimanola", "Latin American fried food", "Panama cuisine"],
        "파라과이 전통 음식 소파 파라과야": ["Paraguayan sopa paraguaya cornbread", "Latin American corn cheese bread", "Paraguay traditional food"],
        "우즈베키스탄 전통 음식 플로프와 샤슐릭": ["Uzbek plov rice dish", "Central Asian pilaf shashlik", "Samarkand plov"],
        "가나 국기와 아크라 시내 풍경": ["Ghana flag Accra city", "Accra Ghana capital city", "West Africa Ghana"],
        "서울시와 쿠라사오를 같은 축척으로 비교한 지도": ["map comparison Seoul Korea Curacao", "world map Curacao Caribbean island"]
    }
    
    if alt_text in korean_food_english:
        return korean_food_english[alt_text]
    
    return [alt_text]


def search_wikimedia(query: str):
    params = {"action": "query", "format": "json", "list": "search",
              "srsearch": query, "srnamespace": "6", "srlimit": 10}
    try:
        r = requests.get("https://commons.wikimedia.org/w/api.php",
                         params=params, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return None
        files = r.json().get("query", {}).get("search", [])
        if not files:
            return None
        for f in files[:8]:
            p2 = {"action": "query", "format": "json", "titles": f["title"],
                  "prop": "imageinfo", "iiprop": "url|size", "iiurlwidth": 1600}
            r2 = requests.get("https://commons.wikimedia.org/w/api.php",
                              params=p2, headers=HEADERS, timeout=15)
            if r2.status_code != 200:
                continue
            for pid, info in r2.json().get("query", {}).get("pages", {}).items():
                if pid == "-1":
                    continue
                ii = info.get("imageinfo", [])
                if ii:
                    w = ii[0].get("width", 0)
                    u = ii[0].get("thumburl") or ii[0].get("url")
                    if u and w >= 600:
                        print(f"    Com: {os.path.basename(f['title'])} ({w}px)")
                        return u
    except Exception as e:
        print(f"    ⚠️ WMF 오류: {e}")
    return None


def search_pexels(query: str):
    try:
        r = requests.get("https://api.pexels.com/v1/search",
                         params={"query": query, "per_page": 5, "orientation": "landscape"},
                         headers=HEADERS, timeout=15)
        if r.status_code == 200:
            for photo in r.json().get("photos", []):
                src = photo.get("src", {})
                for sz in ["landscape", "large", "large2x", "original"]:
                    if sz in src:
                        u = src[sz]
                        u += "&w=1600" if "?" in u else "?w=1600"
                        print(f"    Pexels: {photo.get('alt', '')[:50]}...")
                        return u
    except Exception as e:
        print(f"    Pexels 오류: {e}")
    return None


def step2_retry_failed():
    """실패한 12장 재시도"""
    todo = read_todo()
    failed = [t for t in todo if t["kind"] != "location-map"]
    
    # Find items that still have placeholder in blog
    still_failed = []
    for item in failed:
        pf = BLOG_DIR / item["post"]
        if not pf.exists():
            continue
        content = pf.read_text(encoding="utf-8")
        if item["path"] in content:
            still_failed.append(item)
    
    if not still_failed:
        print("⚠️ 더 이상 실패한 placeholder 없음")
        return
    
    print(f"\n📋 재시도: {len(still_failed)}장")
    
    from PIL import Image
    used_names = set()
    # Collect existing names to avoid conflicts
    for f in PUBLIC_IMAGES.glob("*.jpg"):
        used_names.add(f.name)
    
    for item in still_failed:
        print(f"\n--- 재시도: {item['alt']} ---")
        alt_text = item["alt"]
        kind = item["kind"]
        old_path = item["path"]
        
        # Get proper country name
        country = extract_country_from_post(item["post"]) or "unknown"
        role = extract_role_from_alt(alt_text, kind)
        
        base = f"{country}-{role}"
        filename = f"{base}.jpg"
        if filename in used_names:
            idx = 2
            while f"{base}-{idx}.jpg" in used_names:
                idx += 1
            filename = f"{base}-{idx}.jpg"
        used_names.add(filename)
        
        new_web_path = f"/images/{filename}"
        dst_path = PUBLIC_IMAGES / filename
        
        # Try multiple queries
        queries = generate_better_query(alt_text, kind)
        found = False
        for query in queries:
            print(f"  검색: {query}")
            img_url = search_wikimedia(query) or search_pexels(query)
            if img_url:
                # Download
                temp = PUBLIC_IMAGES / f"_retry_{filename}"
                try:
                    r = requests.get(img_url, headers=HEADERS, timeout=30)
                    if r.status_code == 200:
                        temp.write_bytes(r.content)
                        # Process
                        im = Image.open(temp).convert("RGB")
                        max_w = 1600 if kind == "hero" else 1200
                        if im.width > max_w:
                            nh = round(im.height * max_w / im.width)
                            im = im.resize((max_w, nh), Image.LANCZOS)
                        q = 82
                        im.save(dst_path, "JPEG", quality=q, optimize=True, progressive=True)
                        size = os.path.getsize(dst_path)
                        max_size = 350*1024 if kind == "hero" else 250*1024
                        while size > max_size and q > 60:
                            q -= 5
                            im.save(dst_path, "JPEG", quality=q, optimize=True, progressive=True)
                            size = os.path.getsize(dst_path)
                        temp.unlink()
                        print(f"  ✅ 저장: {filename} ({im.width}x{im.height}, {size/1024:.0f}KB)")
                        found = True
                        break
                except Exception as e:
                    print(f"    ❌ {e}")
                    if temp.exists():
                        temp.unlink()
        
        if found:
            # Update blog
            pf = BLOG_DIR / item["post"]
            content = pf.read_text(encoding="utf-8")
            lines = content.split("\n")
            new_lines = []
            skip = False
            for i, line in enumerate(lines):
                if skip:
                    skip = False
                    continue
                if re.match(r"\s*<!--\s*TODO", line) and i + 1 < len(lines):
                    if item["path"] in lines[i + 1]:
                        new_img = re.sub(r'\]\([^)]+\)', f']({new_web_path})', lines[i + 1])
                        new_lines.append(new_img)
                        skip = True
                        continue
                if item["path"] in line:
                    line = re.sub(r'\]\([^)]+\)', f']({new_web_path})', line)
                new_lines.append(line)
            pf.write_text("\n".join(new_lines), encoding="utf-8")
            print(f"  ✅ {item['post']} 업데이트")
        else:
            print(f"  ❌ 모든 검색 실패")
        
        time.sleep(0.5)

def step3_verify():
    """검증"""
    print("\n\n🔍 ===== 검증 =====")
    
    # 1. Placeholder 잔여 확인
    print("\n--- placeholder 잔여 확인 ---")
    import subprocess
    result = subprocess.run(
        'grep -rnE \'/images/placeholder-[^)]+\\.(jpg|jpeg|png)\' src/content/blog/*.md | grep -v location-map || true',
        shell=True, capture_output=True, text=True, cwd=str(REPO)
    )
    remaining = result.stdout.strip()
    if remaining:
        print(f"❌ {len(remaining.split(chr(10)))}개 placeholder 잔여:")
        print(remaining)
    else:
        print("✅ 모든 placeholder 교체 완료!")
    
    # 2. 파일 존재 확인
    print("\n--- 이미지 파일 존재 확인 ---")
    blog_dir = BLOG_DIR
    missing = 0
    for md_file in blog_dir.glob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        refs = re.findall(r'/images/[\w/-]+\.(jpg|jpeg|png)', content)
        for ref in refs:
            file_path = PUBLIC_IMAGES / os.path.basename(ref)
            if not file_path.exists():
                # Check if it's in size subdirectory
                size_path = PUBLIC_IMAGES / "size" / os.path.basename(ref)
                if not size_path.exists():
                    print(f"  ❌ 없음: {ref}")
                    missing += 1
    
    if missing == 0:
        print("✅ 모든 참조 이미지 파일 존재!")
    else:
        print(f"⚠️ {missing}개 참조 이미지 누락")


def step4_git():
    """Git: 커밋, 푸시, PR"""
    import subprocess
    
    print("\n\n🔧 ===== Git =====")
    os.chdir(str(REPO))
    
    # Check branch
    branch = subprocess.run("git rev-parse --abbrev-ref HEAD", shell=True, capture_output=True, text=True).stdout.strip()
    print(f"브랜치: {branch}")
    
    # git add
    subprocess.run("git add -A", shell=True)
    
    # git status
    status = subprocess.run("git status --short", shell=True, capture_output=True, text=True).stdout
    print(f"변경 파일 수: {len([l for l in status.split(chr(10)) if l.strip()])}")
    
    # commit
    result = subprocess.run(
        'git commit -m "사진 채우기 phase 3: 68/80장 완료 (Wikimedia Commons) + unknown 파일명 정리 + 12장 재시도"',
        shell=True, capture_output=True, text=True
    )
    print(result.stdout)
    if result.returncode != 0:
        print(f"⚠️ 커밋 실패: {result.stderr}")
        return
    
    # push
    print("푸시 중...")
    result = subprocess.run("git push -u origin " + branch, shell=True, capture_output=True, text=True, timeout=60)
    print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
    if result.returncode != 0:
        print(f"⚠️ 푸시 실패: {result.stderr}")
        return
    
    # PR 생성
    print("PR 생성 중...")
    result = subprocess.run(
        'gh pr create --title "사진 채우기 phase 3: 80장 placeholder → 실제 사진" '
        '--body "## 변경 사항\n'
        '- 80장 placeholder를 실제 무료 사진으로 교체 (Wikimedia Commons CC0 + Pexels)\n'
        '- hero: 1600px, ≤350KB / photo: 1200px, ≤250KB (JPEG Progressive)\n'
        '- 각 이미지 alt 텍스트에 맞는 검색어로 매칭\n'
        '- TODO 주석 함께 제거\n'
        '- size/*.svg 비교 지도는 건드리지 않음\n'
        '- location-map(25장)은 제외\n\n'
        '참고: Wikimedia Commons CC 라이선스 이미지 사용"' ,
        shell=True, capture_output=True, text=True, timeout=30
    )
    print(result.stdout)
    if result.returncode != 0:
        print(f"⚠️ PR 실패: {result.stderr}")


if __name__ == "__main__":
    print("=" * 60)
    print("STEP 1: unknown 파일 rename + 마크다운 수정")
    print("=" * 60)
    step1_rename_unknown()
    
    print("\n" + "=" * 60)
    print("STEP 2: 실패 12장 재시도")
    print("=" * 60)
    step2_retry_failed()
    
    print("\n" + "=" * 60)
    print("STEP 3: 검증")
    print("=" * 60)
    step3_verify()
