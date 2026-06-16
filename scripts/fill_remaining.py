#!/usr/bin/env python3
"""
photo-remaining: 39 missing images를 실제 다운로드해서 채움
- unknown-* 참조를 올바른 {country}-{role}.jpg로 교체
- 다운로드 + 리사이즈/최적화
- location-map은 제외
"""

import json, os, re, time, requests, sys
from pathlib import Path
from PIL import Image

REPO = Path(os.environ.get("TEMP", "")) / "trip-blog"
TODO = json.loads((REPO / "docs" / "photo-todo.json").read_text(encoding="utf-8"))
IMG = REPO / "public" / "images"
BLOG = REPO / "src" / "content" / "blog"
HEADERS = {"User-Agent": "TripBlogBot/1.0 (https://trip.lalalakorea.com)"}

COUNTRY_MAP = {
    "가나": "ghana", "네덜란드": "netherlands", "독일": "germany",
    "멕시코": "mexico", "미국": "usa", "벨기에": "belgium",
    "보스니아": "bosnia", "브라질": "brazil", "사우디": "saudi",
    "세네갈": "senegal", "스코틀랜드": "scotland", "알제리": "algeria",
    "에콰도르": "ecuador", "요르단": "jordan", "우즈베키스탄": "uzbekistan",
    "이라크": "iraq", "이집트": "egypt", "체코": "czech",
    "카보베르데": "cape-verde", "코트디부아르": "ivory-coast",
    "콜롬비아": "colombia", "쿠라사오": "curacao", "튀니지": "tunisia",
    "파나마": "panama", "파라과이": "paraguay",
}

FOOD_KW = ["음식","요리","food","브라트부어스트","푸푸","타코","버거","홍합","체바피",
           "슈하스코","카브사","티에부젠","쿠스쿠스","세비체","만사프","플로프",
           "마스구프","팔라펠","카샤파","카리만욜라","소파","맥주","와플","청어","치즈"]


def get_role(alt: str, kind: str) -> str:
    if kind == "hero":
        return "hero"
    al = alt.lower()
    if any(k in al for k in FOOD_KW):
        return "food"
    if any(k in al for k in ["축구","경기장","stadium","유니폼","football","대표팀"]):
        return "football"
    if any(k in al for k in ["수도","도심","시내","시가지","city","skyline","도시","거리","avenue","street"]):
        return "city"
    if any(k in al for k in ["지도","지형","위치","size","satellite","비교한 지도"]):
        return "map"
    if any(k in al for k in ["성","castle","피라미드","pyramid","사원","신전","광장","square","gate","문"]):
        return "landmark"
    if any(k in al for k in ["사막","desert","강","river","열대우림","amazon","highland","해안","coast","산맥","농장","풍경","landscape","하이랜드"]):
        return "nature"
    if any(k in al for k in ["운하","canal"]):
        return "canal"
    if any(k in al for k in ["다리","bridge"]):
        return "bridge"
    if any(k in al for k in ["커피","coffee"]):
        return "coffee"
    return "photo"


def search_wikimedia(query: str):
    params = {"action":"query","format":"json","list":"search",
              "srsearch":query,"srnamespace":"6","srlimit":10}
    try:
        r = requests.get("https://commons.wikimedia.org/w/api.php",
                         params=params, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return None
        files = r.json().get("query",{}).get("search",[])
        for f in files[:8]:
            p2 = {"action":"query","format":"json","titles":f["title"],
                  "prop":"imageinfo","iiprop":"url|size","iiurlwidth":1600}
            r2 = requests.get("https://commons.wikimedia.org/w/api.php",
                              params=p2, headers=HEADERS, timeout=15)
            if r2.status_code != 200:
                continue
            for pid, info in r2.json().get("query",{}).get("pages",{}).items():
                if pid == "-1":
                    continue
                ii = info.get("imageinfo",[])
                if ii and ii[0].get("width",0) >= 600:
                    u = ii[0].get("thumburl") or ii[0].get("url")
                    print(f"    Com: {os.path.basename(f['title'])} ({ii[0]['width']}px)")
                    return u
    except Exception as e:
        print(f"    ⚠️ WMF: {e}")
    return None


def search_pexels(query: str):
    try:
        r = requests.get("https://api.pexels.com/v1/search",
                         params={"query":query,"per_page":5,"orientation":"landscape"},
                         headers=HEADERS, timeout=15)
        if r.status_code == 200:
            for photo in r.json().get("photos",[]):
                src = photo.get("src",{})
                for sz in ["landscape","large","large2x","original"]:
                    if sz in src:
                        u = src[sz]
                        u += "&w=1600" if "?" in u else "?w=1600"
                        print(f"    Pexels: {photo.get('alt','')[:50]}...")
                        return u
    except Exception as e:
        print(f"    Pexels: {e}")
    return None


def download_and_process(url: str, dst: Path, kind: str) -> bool:
    max_w = 1600 if kind == "hero" else 1200
    max_sz = 350*1024 if kind == "hero" else 250*1024
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        if r.status_code != 200:
            return False
        tmp = dst.parent / f"_dl_{dst.name}"
        tmp.write_bytes(r.content)
        im = Image.open(tmp).convert("RGB")
        print(f"    원본: {im.size}, {os.path.getsize(tmp)/1024:.0f}KB")
        if im.width > max_w:
            nh = round(im.height * max_w / im.width)
            im = im.resize((max_w, nh), Image.LANCZOS)
        q = 82
        im.save(dst, "JPEG", quality=q, optimize=True, progressive=True)
        sz = os.path.getsize(dst)
        while sz > max_sz and q > 60:
            q -= 5
            im.save(dst, "JPEG", quality=q, optimize=True, progressive=True)
            sz = os.path.getsize(dst)
        tmp.unlink()
        print(f"    저장: {dst.name} ({im.width}x{im.height}, {sz/1024:.0f}KB, q={q})")
        return True
    except Exception as e:
        print(f"    ❌ 처리 실패: {e}")
        return False


def fix_markdown(post_file: Path, new_web_path: str):
    """Replace any unknown-* or placeholder-* ref with the correct path"""
    content = post_file.read_text(encoding="utf-8")
    lines = content.split("\n")
    new_lines = []
    skip = False
    changed = False
    for i, line in enumerate(lines):
        if skip:
            skip = False
            continue
        # TODO + broken ref pair
        if re.match(r"\s*<!--\s*TODO", line) and i + 1 < len(lines):
            if "/images/" in lines[i + 1]:
                # Just skip TODO, keep next image line (will replace path)
                next_line = lines[i + 1]
                # Replace path
                old_refs = re.findall(r'\]\(/images/[^)]+\)', next_line)
                for old in old_refs:
                    next_line = next_line.replace(old, f"]({new_web_path})")
                    changed = True
                new_lines.append(next_line)
                skip = True
                continue
        # Direct path replace
        if "/images/" in line:
            old_refs = re.findall(r'\]\(/images/[^)]+\)', line)
            for old in old_refs:
                if "placeholder" in old or "unknown" in old:
                    line = line.replace(old, f"]({new_web_path})")
                    changed = True
        new_lines.append(line)
    if changed:
        post_file.write_text("\n".join(new_lines), encoding="utf-8")
        print(f"    ✅ {post_file.name} — 참조 수정: {new_web_path}")


def main():
    targets = [t for t in TODO if t["kind"] != "location-map"]

    # Build proper filenames for all items
    used_names = set()
    items = []
    for item in targets:
        country = "unknown"
        for kr, en in COUNTRY_MAP.items():
            if kr in item["post"]:
                country = en
                break
        role = get_role(item["alt"], item["kind"])
        base = f"{country}-{role}"
        fn = f"{base}.jpg"
        if fn in used_names:
            idx = 2
            while f"{base}-{idx}.jpg" in used_names:
                idx += 1
            fn = f"{base}-{idx}.jpg"
        used_names.add(fn)
        items.append({**item, "proper_file": fn, "country": country})

    # Only missing files
    missing = [p for p in items if not (IMG / p["proper_file"]).exists()]
    print(f"\n📋 다운로드 필요: {len(missing)}장")
    print(f"   hero: {sum(1 for p in missing if p['kind']=='hero')}")
    print(f"   photo: {sum(1 for p in missing if p['kind']=='photo')}")

    # First pass: fix ALL markdown references (replace unknown-* with proper names)
    print("\n🔧 1차: 마크다운 참조 수정 (unknown-* → 올바른 파일명)")
    for p in items:
        pf = BLOG / p["post"]
        if pf.exists():
            fix_markdown(pf, f"/images/{p['proper_file']}")

    # Second pass: download missing files
    print("\n📥 2차: 누락 파일 다운로드")
    success = 0
    for p in missing:
        fn = p["proper_file"]
        alt = p["alt"]
        kind = p["kind"]
        dst = IMG / fn
        if dst.exists():
            success += 1
            continue

        print(f"\n[{kind.upper()}] {alt[:50]} → {fn}")

        # Generate search queries
        queries = [alt]
        # Try specific food names
        if kind == "hero":
            queries.append(f"{p['country']} landscape travel")
            queries.append(f"{p['country']} city flag")
        elif "food" in fn or "요리" in alt or "음식" in alt:
            queries.append(f"{p['country']} traditional cuisine food")
            queries.append(f"{p['country']} food dish")
        elif "football" in fn:
            queries.append(f"{p['country']} football stadium")
            queries.append(f"{p['country']} national team")
        elif "map" in fn or "지도" in alt:
            queries.append(f"{p['country']} satellite map geography")
            queries.append(f"{p['country']} map")
        elif "city" in fn or "도심" in alt or "수도" in alt or "시내" in alt or "시가지" in alt:
            queries.append(f"{p['country']} capital city downtown")
            queries.append(f"{p['country']} city street skyline")
        elif "landmark" in fn or "명소" in alt:
            queries.append(f"{p['country']} famous landmark")
            queries.append(f"{p['country']} tourism attraction")
        elif "nature" in fn or "풍경" in alt:
            queries.append(f"{p['country']} nature landscape")
            queries.append(f"{p['country']} scenery")
        else:
            queries.append(f"{p['country']} travel")
            queries.append(f"{p['country']} photo")

        downloaded = False
        for q in queries:
            print(f"  검색: {q}")
            url = search_wikimedia(q) or search_pexels(q)
            if url:
                if download_and_process(url, dst, kind):
                    downloaded = True
                    success += 1
                    break
                print(f"    처리 실패, 다음 검색어로...")
            time.sleep(0.3)

        if not downloaded:
            print(f"  ❌ 모든 검색 실패: {fn}")
            # Create a minimal placeholder
            placeholder_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600" viewBox="0 0 800 600">
  <rect fill="#f0f0f0" width="800" height="600"/>
  <text fill="#999" font-family="sans-serif" font-size="24" text-anchor="middle" x="400" y="290">Image not available</text>
  <text fill="#bbb" font-family="sans-serif" font-size="14" text-anchor="middle" x="400" y="320">{p['country']} - {p['role']}</text>
</svg>'''
            # We'll keep the reference but mark it
            print(f"  ⚠️ SVG fallback 생성: {fn.replace('.jpg','.svg')}")
            (IMG / fn.replace(".jpg", ".svg")).write_text(placeholder_svg, encoding="utf-8")
            # Also update blog ref to SVG
            pf = BLOG / p["post"]
            if pf.exists():
                content = pf.read_text(encoding="utf-8")
                content = content.replace(f"/images/{fn}", f"/images/{fn.replace('.jpg', '.svg')}")
                pf.write_text(content, encoding="utf-8")

    print(f"\n{'='*50}")
    print(f"✅ 다운로드 완료: {success}/{len(missing)}")
    print(f"   남은 누락: {len(missing)-success}")


if __name__ == "__main__":
    main()
