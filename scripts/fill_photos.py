#!/usr/bin/env python3
"""
trip-blog 사진 채우기 (phase 3) — 단일 스크립트 자동화
1. photo-todo.json 로드 → location-map 제외 (80장)
2. Wikimedia Commons / Pexels 검색 → 다운로드
3. Pillow 리사이즈/최적화 → public/images/ 저장
4. 마크다운 placeholder 경로 교체 + TODO 주석 제거
"""

import json
import os
import re
import time
from pathlib import Path

import requests
from PIL import Image

REPO = Path(os.environ.get("TEMP", "")) / "trip-blog"
TODO_JSON = REPO / "docs" / "photo-todo.json"
PUBLIC_IMAGES = REPO / "public" / "images"
BLOG_DIR = REPO / "src" / "content" / "blog"

# 제한
MAX_WIDTH_HERO = 1600
MAX_WIDTH_PHOTO = 1200
JPEG_QUALITY = 82
MAX_SIZE_HERO = 350 * 1024
MAX_SIZE_PHOTO = 250 * 1024
DELAY = 0.3

HEADERS = {"User-Agent": "TripBlogBot/1.0 (https://trip.lalalakorea.com)"}

KNOWN_ROLES = {
    'hero', 'city', 'food', 'football', 'landmark', 'nature', 'coast',
    'canal', 'bridge', 'square', 'coffee', 'map', 'accra', 'photo',
    'amsterdam', 'berlin', 'brussels', 'saopaulo', 'tashkent', 'amman',
    'prague', 'edinburgh', 'quito', 'sahara', 'highland', 'nile-satellite',
    'willemstad', 'abidjan', 'praia', 'asuncion', 'riyadh', 'dakar',
    'sarajevo', 'baghdad', 'teotihuacan', 'neuschwanstein', 'newyork',
    'amazon', 'churrasco', 'azteca-stadium', 'mexico-city', 'seoul-size',
    'geography'
}


def korean_to_english_keywords(alt_text: str, kind: str) -> str:
    """한글 alt 텍스트를 영어 검색 키워드로 변환"""
    keyword_map = {
        "가나 국기와 아크라 시내 풍경": "ghana flag accra cityscape",
        "가나 수도 아크라 도심 전경": "accra ghana city downtown",
        "가나 전통 음식 푸푸와 라이트 수프": "fufu light soup ghana food",
        "암스테르담 운하와 자전거가 있는 풍경": "amsterdam canal bicycle",
        "암스테르담 중심부의 운하와 건물들": "amsterdam canals buildings",
        "네덜란드 전통 음식 치즈와 청어 절임 하링": "holland cheese herring food",
        "독일 베를린 브란덴부르크 문과 라인강 풍경": "Brandenburg Gate Berlin Germany",
        "독일 베를린 브란덴부르크 문과 도심 전경": "Berlin Germany cityscape",
        "눈 덮인 알프스 산기슭에 솟아 있는 노이슈반슈타인 성": "Neuschwanstein Castle winter",
        "독일 축구 국가대표팀 관련 이미지": "Germany national football team fans",
        "독일 전통 음식 브라트부어스트 소시지와 맥주": "Bratwurst sausage beer German food",
        "멕시코 테오티우아칸 피라미드와 알록달록한 과나후아토 도시 전경": "Teotihuacan pyramids Mexico",
        "멕시코시티의 소칼로 광장과 대성당 전경": "Mexico City Zocalo Cathedral",
        "멕시코 테오티우아칸의 태양의 피라미드": "Teotihuacan Pyramid of the Sun",
        "멕시코시티 에스타디오 아스테카 전경": "Estadio Azteca Mexico City stadium",
        "멕시코 길거리 타코와 과카몰리": "Mexican tacos guacamole street food",
        "뉴욕 맨해튼의 스카이라인": "New York Manhattan skyline",
        "뉴욕 타임스스퀘어의 번화한 거리": "Times Square New York crowded",
        "미국식 수제 버거": "American hamburger burger food",
        "벨기에 브뤼셀 그랑플라스 광장": "Brussels Grand Place Belgium",
        "벨기에 브뤼셀의 도심 전경": "Brussels Belgium city",
        "벨기에 전통 음식인 홍합 요리와 와플": "Belgian mussels waffles food",
        "사라예보의 구시가지 풍경": "Sarajevo old town Bosnia",
        "사라예보의 바시차르시야 구시가지": "Sarajevo Bascarsija old bazaar",
        "보스니아 전통 음식 체바피": "Cevapi Bosnian food grilled meat",
        "브라질 리우데자네이루 예수상과 코파카바나 해변": "Rio de Janeiro Christ Redeemer Copacabana",
        "상파울루의 빽빽한 도시 전경": "Sao Paulo Brazil city skyline",
        "끝없이 펼쳐진 아마존 열대우림과 강": "Amazon rainforest river aerial",
        "브라질식 바비큐 슈하스코": "Churrasco Brazilian BBQ meat",
        "사우디아라비아 리야드의 스카이라인": "Riyadh Saudi Arabia skyline",
        "사우디아라비아 리야드 도심": "Riyadh Saudi Arabia city",
        "사우디아라비아 전통 음식 카브사": "Kabsa Saudi Arabian food rice meat",
        "세네갈 다카르의 해안 풍경": "Dakar Senegal coastline",
        "세네갈 수도 다카르의 도심 풍경": "Dakar Senegal city street",
        "세네갈 전통 음식 티에부젠": "Thieboudienne Senegalese fish rice food",
        "에든버러 성과 스카이라인": "Edinburgh Castle Scotland skyline",
        "에든버러 구시가지 전경": "Edinburgh old town Scotland",
        "스코틀랜드 하이랜드의 풍경": "Scottish Highlands landscape",
        "알제리 수도 알제의 지중해 해안 전경": "Algiers Algeria Mediterranean coast",
        "알제리 전통 음식 쿠스쿠스": "Couscous Algerian food",
        "에콰도르 키토 구시가지 전경": "Quito Ecuador old town",
        "에콰도르 키토의 시가지 전경": "Quito Ecuador city streets",
        "에콰도르 전통 음식 세비체": "Ceviche Ecuadorian food",
        "요르단 페트라의 알카즈네 신전 전경": "Petra Jordan Treasury Al-Khazneh",
        "요르단 수도 암만의 도심 풍경": "Amman Jordan city",
        "요르단 전통 요리 만사프": "Mansaf Jordanian rice lamb food",
        "사마르칸트 레기스탄 광장의 푸른 모스크": "Samarkand Registan Square Uzbekistan",
        "타슈켄트 도심의 현대적인 거리": "Tashkent Uzbekistan modern city",
        "우즈베키스탄 전통 음식 플로프와 샤슐릭": "Plov shashlik Uzbek food",
        "이라크 바그다드의 야경": "Baghdad Iraq night cityscape",
        "이라크 바그다드의 시내 풍경": "Baghdad Iraq city street",
        "이라크 전통 생선 구이 마스구프": "Masgouf Iraqi grilled fish food",
        "기자의 피라미드와 스핑크스 전경": "Giza pyramids Sphinx Egypt",
        "나일강 주변에만 초록빛이 보이고 나머지는 사막인 이집트 위성 사진": "Nile river Egypt satellite desert",
        "이집트 전통 음식 풀 메다메스와 팔라펠": "Ful medames falafel Egyptian food",
        "프라하 구시가지 광장 전경": "Prague old town square Czech",
        "프라하 카를 교와 프라하 성": "Prague Charles Bridge castle",
        "체코 전통 음식과 맥주": "Czech food beer traditional",
        "카보베르데의 화산섬 해안 풍경": "Cape Verde volcanic island coastline",
        "카보베르데 수도 프라이아의 도심 풍경": "Praia Cape Verde city",
        "카보베르데 전통 스튜 요리 카샤파": "Cachupa Cape Verde stew food",
        "코트디부아르 아비장의 스카이라인": "Abidjan Ivory Coast skyline",
        "코트디부아르 최대 도시 아비장의 거리 풍경": "Abidjan Ivory Coast street",
        "코트디부아르 전통 음식 풀레 야사": "Poulet Yassa Ivory Coast chicken food",
        "콜롬비아 안데스 산맥의 커피 농장 풍경": "Colombia Andes coffee plantation",
        "콜롬비아 축구 국가대표팀 유니폼": "Colombia national football team jersey",
        "콜롬비아 전통 음식 반데하 파이사와 커피": "Bandeja paisa Colombian food coffee",
        "쿠라사오 수도 빌렘스타트의 알록달록한 파스텔 건물": "Willemstad Curacao colorful buildings",
        "서울시와 쿠라사오를 같은 축척으로 비교한 지도": "map comparison Seoul Curacao size",
        "쿠라사오 수도 빌렘스타트의 펜덴트 다리와 파스텔 건물": "Willemstad Curacao pontoon bridge",
        "쿠라사오 전통 음식과 해산물 요리": "Curacao seafood food traditional",
        "튀니지 시디 부 사이드의 파란 지붕과 흰 벽 마을 풍경": "Sidi Bou Said Tunisia blue white village",
        "튀니지 남부 사하라 사막 모래 언덕": "Sahara desert dunes Tunisia",
        "튀니지 전통 음식 쿠스쿠스": "Couscous Tunisian food",
        "파나마 운하 전경": "Panama Canal view",
        "파나마 지협의 좁은 폭과 운하를 보여주는 지형 이미지": "Panama isthmus geography aerial",
        "파나마 전통 음식 카리만욜라": "Carimanola Panamanian food",
        "파라과이 수도 아순시온 전경": "Asuncion Paraguay city",
        "아순시온의 파라과이 강변 풍경": "Asuncion Paraguay river waterfront",
        "파라과이 전통 음식 소파 파라과야": "Sopa paraguaya Paraguayan cornbread food",
    }
    if alt_text in keyword_map:
        return keyword_map[alt_text]
    return alt_text


def generate_filename(old_path: str, kind: str, used_names: set) -> str:
    """old_path(/images/placeholder-xxx.jpg)에서 country+role 추출"""
    basename = os.path.basename(old_path).replace("placeholder-", "", 1)
    basename = os.path.splitext(basename)[0]
    has_korean = bool(re.search(r'[\uac00-\ud7af]', basename))
    parts = basename.rsplit("-", 1)

    if has_korean:
        country = "unknown"
    elif len(parts) >= 2 and parts[1].lower() in KNOWN_ROLES:
        country = re.sub(r'[^a-z0-9-]', "", parts[0].lower())
    else:
        country = re.sub(r'[^a-z0-9-]', "", basename.lower())
    if not country:
        country = "unknown"

    if kind == "hero":
        role = "hero"
    elif not has_korean and len(parts) >= 2:
        lp = parts[1].lower()
        if lp in KNOWN_ROLES:
            role = lp
        elif lp in ("food", "cuisine", "dish", "meal"):
            role = "food"
        elif lp in ("football", "soccer", "stadium", "jersey"):
            role = "football"
        elif lp in ("city", "downtown", "skyline", "street", "urban"):
            role = "city"
        elif lp in ("landmark", "castle", "pyramid", "gate", "cathedral", "temple"):
            role = "landmark"
        elif lp in ("nature", "landscape", "river", "forest", "mountain", "sea", "coast", "desert", "highland"):
            role = "nature"
        elif lp in ("map", "geography", "satellite", "size"):
            role = "map"
        else:
            role = "photo"
    else:
        role = "photo"

    base = f"{country}-{role}"
    filename = f"{base}.jpg"
    if filename in used_names:
        idx = 2
        while f"{base}-{idx}.jpg" in used_names:
            idx += 1
        filename = f"{base}-{idx}.jpg"
    used_names.add(filename)
    return filename


def search_wikimedia(query: str) -> str | None:
    params = {
        "action": "query", "format": "json",
        "list": "search", "srsearch": query,
        "srnamespace": "6", "srlimit": 8,
    }
    try:
        resp = requests.get("https://commons.wikimedia.org/w/api.php",
                            params=params, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            return None
        files = resp.json().get("query", {}).get("search", [])
        if not files:
            return None
        for f in files[:5]:
            p2 = {
                "action": "query", "format": "json",
                "titles": f["title"], "prop": "imageinfo",
                "iiprop": "url|size", "iiurlwidth": 1600,
            }
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
                        print(f"    Wikimedia: {os.path.basename(f['title'])} ({w}px)")
                        return u
    except Exception as e:
        print(f"    ⚠️ Wikimedia 오류: {e}")
    return None


def search_pexels(query: str) -> str | None:
    try:
        resp = requests.get(
            "https://api.pexels.com/v1/search",
            params={"query": query, "per_page": 5, "orientation": "landscape"},
            headers=HEADERS,
            timeout=15,
        )
        if resp.status_code == 200:
            for photo in resp.json().get("photos", []):
                src = photo.get("src", {})
                for sz in ["landscape", "large", "large2x", "original"]:
                    if sz in src:
                        u = src[sz]
                        u += "&w=1600" if "?" in u else "?w=1600"
                        print(f"    Pexels: {photo.get('alt', '')[:50]}...")
                        return u
    except Exception as e:
        print(f"    ⚠️ Pexels 오류: {e}")
    return None


def search_image(query: str) -> str | None:
    u = search_wikimedia(query)
    return u if u else search_pexels(query)


def download_image(url: str, save_path: Path) -> bool:
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        if r.status_code == 200:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            save_path.write_bytes(r.content)
            return True
    except Exception as e:
        print(f"    ⚠️ 다운로드 실패: {e}")
    return False


def process_image(src_path: Path, dst_path: Path, kind: str) -> bool:
    max_w = MAX_WIDTH_HERO if kind == "hero" else MAX_WIDTH_PHOTO
    max_size = MAX_SIZE_HERO if kind == "hero" else MAX_SIZE_PHOTO
    try:
        im = Image.open(src_path).convert("RGB")
        ow, oh = im.size
        print(f"    원본: {ow}x{oh}, {os.path.getsize(src_path) / 1024:.0f}KB")
        if im.width > max_w:
            nh = round(im.height * max_w / im.width)
            im = im.resize((max_w, nh), Image.LANCZOS)
        q = JPEG_QUALITY
        im.save(dst_path, "JPEG", quality=q, optimize=True, progressive=True)
        size = os.path.getsize(dst_path)
        while size > max_size and q > 60:
            q -= 5
            im.save(dst_path, "JPEG", quality=q, optimize=True, progressive=True)
            size = os.path.getsize(dst_path)
        print(f"    저장: {dst_path.name} ({im.width}x{im.height}, {size / 1024:.0f}KB, q={q})")
        return True
    except Exception as e:
        print(f"    ⚠️ 처리 실패: {e}")
        return False


def replace_placeholder_in_markdown(post_file: Path, old_path: str, new_path: str):
    content = post_file.read_text(encoding="utf-8")
    lines = content.split("\n")
    new_lines = []
    skip_next = False
    for i, line in enumerate(lines):
        if skip_next:
            skip_next = False
            continue
        if re.match(r"\s*<!--\s*TODO", line) and i + 1 < len(lines):
            if old_path in lines[i + 1]:
                new_img = lines[i + 1].replace(old_path, new_path)
                new_lines.append(new_img)
                skip_next = True
                continue
        if old_path in line:
            line = line.replace(old_path, new_path)
        new_lines.append(line)
    post_file.write_text("\n".join(new_lines), encoding="utf-8")
    print(f"    ✅ {post_file.name} — 교체 완료")


def process_item(item: dict, used_names: set) -> dict:
    result = {"item": item, "status": "pending", "file": None, "error": None}
    post_file = BLOG_DIR / item["post"]
    alt_text = item["alt"]
    kind = item["kind"]
    old_path = item["path"]

    print(f"\n{'=' * 60}")
    print(f"[{kind.upper()}] {alt_text}")
    print(f"  글: {item['post']}")

    filename = generate_filename(old_path, kind, used_names)
    dst_path = PUBLIC_IMAGES / filename
    new_web_path = f"/images/{filename}"
    print(f"  → {filename}")

    query = korean_to_english_keywords(alt_text, kind)
    print(f"  검색어: {query}")

    img_url = search_image(query)
    if not img_url:
        result["status"] = "failed"
        result["error"] = "검색 실패"
        print(f"  ❌ 검색 실패")
        return result

    print(f"  URL: {img_url[:80]}...")

    temp_path = PUBLIC_IMAGES / f"_temp_{filename}"
    if not download_image(img_url, temp_path):
        result["status"] = "failed"
        result["error"] = "다운로드 실패"
        return result

    if not process_image(temp_path, dst_path, kind):
        result["status"] = "failed"
        result["error"] = "이미지 처리 실패"
        if temp_path.exists():
            temp_path.unlink()
        return result
    if temp_path.exists():
        temp_path.unlink()

    if post_file.exists():
        replace_placeholder_in_markdown(post_file, old_path, new_web_path)
    else:
        print(f"  ⚠️ 글 파일 없음: {post_file}")

    result["status"] = "done"
    result["file"] = str(dst_path)
    print(f"  ✅ 완료")
    time.sleep(DELAY)
    return result


def main():
    PUBLIC_IMAGES.mkdir(parents=True, exist_ok=True)
    todo_data = json.loads(TODO_JSON.read_text(encoding="utf-8"))
    targets = [t for t in todo_data if t["kind"] != "location-map"]

    print(f"\n📋 총 대상: {len(targets)}장 (hero {sum(1 for t in targets if t['kind'] == 'hero')} + photo {sum(1 for t in targets if t['kind'] == 'photo')})")
    print(f"   제외: location-map {len(todo_data) - len(targets)}장\n")

    used_names = set()
    results = []
    for item in targets:
        r = process_item(item, used_names)
        results.append(r)
        done = sum(1 for x in results if x["status"] == "done")
        failed = sum(1 for x in results if x["status"] == "failed")
        print(f"\n📊 진행: {done}/{len(targets)} 완료, {failed} 실패")

    print(f"\n{'=' * 60}")
    print(f"📊 최종 결과")
    print(f"   성공: {sum(1 for r in results if r['status'] == 'done')}/{len(targets)}")
    print(f"   실패: {sum(1 for r in results if r['status'] == 'failed')}")
    failed_items = [r for r in results if r["status"] == "failed"]
    if failed_items:
        print(f"\n❌ 실패 목록:")
        for f in failed_items:
            print(f"   - {f['item']['alt']}: {f['error']}")
    print(f"\n✅ 작업 완료")


if __name__ == "__main__":
    main()
