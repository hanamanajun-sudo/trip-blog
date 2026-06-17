# 작업 지시서 — 블로그 사진 채우기 (phase 3)

> trip.lalalakorea.com (Astro v4 + Vercel). 나라 비교 시리즈 글에 비어 있는 **사진 placeholder 80장**을
> 적절한 무료 사진으로 채운다: **다운로드 → 리사이즈/최적화 → 올바른 위치에 삽입**.
> **전제: 이 작업은 외부 네트워크(특히 이미지 다운로드)가 허용된 환경에서 실행해야 한다.**

---

## 0. 목표 한 줄
각 placeholder 자리의 `alt` 설명에 딱 맞는 무료 사진을 받아, 용량을 줄여 `public/images/`에 저장하고,
마크다운의 placeholder 경로를 실제 사진 경로로 교체한다. 빌드 통과 후 커밋·푸시·PR.

## 1. 저장소 컨텍스트
- 글: `src/content/blog/*.md` (frontmatter `entry_slug`로 URL `/entry/{slug}`)
- 이미지: `public/images/` → 사이트에서 `/images/...`로 서빙
- 작업 목록(필독):
  - `docs/photo-todo.json` — 기계용. 각 항목 `{post, title, kind, alt, path}` (kind: `hero`/`photo`/`location-map`)
  - `docs/photo-todo.md` — 사람용(글별 표)
- 개발 브랜치: **`claude/sharp-planck-f5xge0`** 에서 작업, `master`로 PR
- 빌드: `npm install && npm run build` (오류 0이어야 함)
- Python `Pillow` 사용 가능(리사이즈용). Node `sharp`나 ImageMagick `convert`도 무방.

## 2. 작업 범위
- ✅ **대상: `kind`가 `hero`(25장) + `photo`(55장) = 총 80장**
- ❌ **제외: `kind`가 `location-map`(25장)** — 이건 사진이 아니라 '대륙 내 국가 위치 지도'다.
  사진으로 채우지 말 것. (별도 작업 — 손대지 말고 그대로 둔다.)
- 크기 비교 지도(`/images/size/*.svg`)는 **이미 완성**돼 있다. 건드리지 말 것.

## 3. 이미지 소싱 규칙 (라이선스 안전 최우선)
**반드시 상업적 사용 가능·무료 출처만 사용.** 우선순위:
1. **Unsplash** (Unsplash License, 출처표기 불필요) — 1순위
2. **Pexels / Pixabay** (무료, 상업적 가능)
3. **Wikimedia Commons** (랜드마크/유적에 강함; CC0·CC-BY 등 — 라이선스 확인, CC-BY면 출처 표기 권장)

권장 방식 — **Unsplash API(무료 Access Key 발급)**:
```
GET https://api.unsplash.com/search/photos?query={영문 키워드}&per_page=5&orientation=landscape&client_id={ACCESS_KEY}
→ results[].urls.regular  (다운로드용 https://images.unsplash.com/... URL)
→ results[].user.name     (제작자, 기록용)
```
- 받은 `urls.regular`(또는 `urls.raw` + `?w=1600&q=80`)를 다운로드.
- API 가이드라인상 다운로드 시 `results[].links.download_location`에 `client_id` 붙여 GET 1회 호출(트리거)도 해주면 매너.
- API 키가 없으면: 사진 페이지(`unsplash.com/photos/...`)의 `og:image`(=`images.unsplash.com/...`)를 받아도 됨.

**금지**: 구글 이미지 무단, 저작권 불명 이미지, 워터마크/스톡 미리보기, 연예인·로고 등 권리 문제 소지.

## 4. 다운로드 → 리사이즈/최적화 → 저장
**규격(용량 절감 필수):**
| 종류 | 최대 가로 | 포맷 | 품질 | 목표 용량 |
| --- | --- | --- | --- | --- |
| hero | 1600px | JPEG(progressive) | ~82 | ≤ 350KB |
| photo | 1200px | JPEG(progressive) | ~82 | ≤ 250KB |
- EXIF 등 메타데이터 제거, RGB 변환.

**Pillow 예시:**
```python
from PIL import Image
def save_web(src_path, dst_path, max_w):
    im = Image.open(src_path).convert("RGB")
    if im.width > max_w:
        im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
    im.save(dst_path, "JPEG", quality=82, optimize=True, progressive=True)
# 저장 후 os.path.getsize로 용량 확인, 너무 크면 quality 78~80으로 재저장
```

**파일명 규칙(중요 — 한글 파일명 쓰지 말 것):**
- 새 파일명 = `{country}-{role}.jpg` (전부 소문자 ASCII)
  - `country` = 그 글 `entry_slug`의 앞부분 (예: `germany-vs-korea-...` → `germany`)
  - `role` = 자리 성격: `hero` / `city`(수도·도시) / `food` / `landmark`(유적·명소) / `nature` / `football` 등 alt로 판단
  - 같은 role이 둘이면 `-2` 추가 (예: `germany-landmark-2.jpg`)
- 저장 위치: `public/images/{country}-{role}.jpg`
- 마크다운 경로: `/images/{country}-{role}.jpg`

## 5. 마크다운 교체
각 글에서 **placeholder 경로 문자열만** 새 경로로 교체. **`alt` 텍스트(대괄호 안)는 그대로 유지**.
```
# before
![독일 전통 음식 브라트부어스트 소시지와 맥주](/images/placeholder-germany-food.jpg)
# after
![독일 전통 음식 브라트부어스트 소시지와 맥주](/images/germany-food.jpg)
```
- placeholder 위에 남아 있는 `<!-- TODO: ... -->` 주석이 있으면 함께 제거(깔끔하게).
- 위치를 옮기지 말고 **있던 자리 그대로** 교체만 한다.

## 6. 글별 검색어 가이드
- 기본: 각 항목 `alt`(한국어)를 영어 키워드로 옮겨 검색.
  - 예) "독일 전통 음식 브라트부어스트 소시지와 맥주" → `bratwurst sausage beer`
  - 예) "암스테르담 운하와 자전거" → `amsterdam canal bicycle`
  - 예) "노이슈반슈타인 성" → `neuschwanstein castle`
- **랜드마크·도시·음식은 고유명사로 구체적으로** 검색(나라명+대상). 풍경은 `{나라} landscape`.
- 사람 얼굴이 크게 나오거나 정치적·종교적으로 민감한 사진은 피하고, 풍경/도시/음식/건축 위주로.
- 분위기는 기존 글 톤(밝고 깔끔한 여행 사진)에 맞춘다.

## 7. 검증(끝나고 반드시)
1. `npm run build` → **exit 0** (에러 없음).
2. 사진 placeholder 잔여 0 확인:
   ```
   grep -rnE '/images/placeholder-[^)]+\.(jpg|jpeg|png)' src/content/blog/*.md | grep -v location-map
   # (출력 없어야 함)
   ```
3. 글이 참조하는 모든 `/images/*.jpg`가 `public/images/`에 실제 존재하는지 대조.
4. 새 이미지 용량이 목표 이하인지 확인(`ls -la`), 초과분은 재압축.

## 8. Git 워크플로
- 브랜치 `claude/sharp-planck-f5xge0`에서 작업.
- 의미 단위(또는 글 묶음 단위)로 커밋. 메시지는 한국어로 명확히.
- `git push -u origin claude/sharp-planck-f5xge0` (네트워크 실패 시 2s,4s,8s,16s 백오프 재시도).
- 완료 후 `master`로 PR 생성(설명에 출처/장수 요약). 머지는 사람이 한다.
- 커밋에 모델 식별자/비밀키를 넣지 말 것. Unsplash Access Key는 코드·커밋에 하드코딩 금지(환경변수 사용).

## 9. 워크플로 요약(루프)
```
docs/photo-todo.json 로드 → kind != location-map 만 필터(80개)
for 각 항목:
    country = entry_slug 앞부분, role = alt로 판단 → 새 파일명 결정
    Unsplash 검색(alt→영문 키워드) → 적합 1장 선택 → 다운로드
    Pillow로 리사이즈/최적화 → public/images/{country}-{role}.jpg 저장(용량 확인)
    해당 글에서 old placeholder 경로 → 새 경로로 치환(alt 유지, TODO 주석 제거)
검증(빌드·grep·용량) → 커밋·푸시 → PR
```

## 10. 워크드 예시 (독일 글, `독일-vs-...md`)
| 자리(alt) | 검색어 | 새 파일명 |
| --- | --- | --- |
| 독일 베를린 브란덴부르크 문과 라인강 풍경 (hero) | `brandenburg gate berlin` | `germany-hero.jpg` |
| 독일 베를린 브란덴부르크 문과 도심 전경 | `berlin cityscape` | `germany-city.jpg` |
| 눈 덮인 알프스 산기슭 노이슈반슈타인 성 | `neuschwanstein castle winter` | `germany-landmark.jpg` |
| 독일 축구 국가대표팀 관련 | `germany football fans flag` | `germany-football.jpg` |
| 독일 전통 음식 브라트부어스트 소시지와 맥주 | `bratwurst beer` | `germany-food.jpg` |

끝. 막히는 부분(라이선스 애매/검색 안 맞음)은 그 자리만 비워두고(placeholder 유지) 로그로 남길 것 — 깨진 이미지보다 낫다.
