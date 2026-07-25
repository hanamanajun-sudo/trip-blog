---
name: country-comparison-post
description: trip.lalalakorea "나라 비교" 시리즈 신규 글을 처음부터 끝까지 자동으로 만든다. "{나라} 글 써줘", "{나라} 비교 글 작성해줘", "나라 비교 시리즈 다음 글 진행", "{나라} 발행해줘" 같은 요청 시 자동 실행. 팩트체크 → 페르소나 서두 → 본문 작성 → 관련국 내부링크 → 크기비교 지도 SVG 생성 → Unsplash 썸네일 삽입 → 홈 세계지도(WorldMap.astro) 국가 추가 → 빌드 검증 → git 배포까지 전 과정을 사람이 매 단계 지시하지 않아도 순서대로 처리한다.
---

# country-comparison-post 스킬 (trip-blog 프로젝트 전용)

"{나라} vs 한국 크기·인구·여행정보 비교" 글 하나를 발행하는 전체 파이프라인. 인도네시아 글(2026-07-25)에서 처음 검증한 절차를 그대로 스킬화한 것 — **매번 처음부터 방법을 찾지 말고 아래 순서를 그대로 따른다.**

인자로 나라 이름(한국어)을 받는다. 없으면 PROGRESS.md의 "B안 신규 발행 순서" 대기열에서 다음 나라를 사용한다.

## 0단계 — 중복 확인

```bash
grep -rl "{나라영어slug}\|{나라한글}-vs-한국" src/content/blog/*.md
```
이미 있으면 사용자에게 확인 후 중단. `entry_slug`는 `{country}-vs-korea-size-population-travel` 형식(영어, 소문자, 하이픈)으로 정한다 — CLAUDE.md 규칙상 슬러그에 연도 등 시의성 정보 절대 넣지 않는다.

## 1단계 — 크기비교 지도 SVG 생성 (`scripts/make_country_maps.py`)

**a) geodata 존재 확인**
```bash
ls scripts/geodata/{ISO3}.geo.json   # 예: IDN, MYS, IND
```

**b) 없으면 새로 생성.** 원본 Natural Earth 50m 데이터가 없으면 먼저 받는다:
```bash
curl -sL -o /tmp/ne_50m.geojson "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_50m_admin_0_countries.geojson"
```
⚠️ **Windows 경로 함정**: `build_geodata.py`는 기본적으로 `/tmp/ne_50m.geojson`을 그대로 열려고 하는데, 이 프로젝트의 Python(`C:\Python314\python.exe` 등 네이티브 exe)은 bash의 `/tmp`를 못 찾는다. 반드시 실제 Windows 경로로 변환해서 `NE_SRC`에 넘긴다:
```bash
cygpath -w /tmp/ne_50m.geojson   # → C:\Users\...\AppData\Local\Temp\ne_50m.geojson 확인
export NE_SRC="C:/Users/.../AppData/Local/Temp/ne_50m.geojson"   # 위 결과를 슬래시(/)로 바꿔서
python scripts/build_geodata.py {ISO3}
```
⚠️ **`python3` 아님**: 이 환경의 `python3` 명령은 빈 WindowsApps 스텁으로 연결돼서 아무것도 안 한다(에러도 없이 "Python"만 출력하고 종료). 반드시 `python` 명령을 쓴다.

**c) `scripts/make_country_maps.py`에 나라 설정 3곳 추가** (딕셔너리 알파벳/등장 순서 신경 안 써도 됨, 아무 데나 추가):
- `NAMES` 딕셔너리: `"{ISO3}": "{한글국명}"`
- `CAPITALS` 딕셔너리: `"{ISO3}": ("{수도한글}", {수도경도}, {수도위도})`
- `COUNTRIES` 딕셔너리: `"{영어slug}": {"iso": "{ISO3}", "neighbors": [], "ratio": "한국의 약 {N}배", "poi": {"cities": [(...)]}}` — `ratio`는 실제 면적/100,401(한국 면적) 계산값. 한국보다 작은 나라는 `"scenes": ["C", "D"], "smaller": True` 추가.

**d) 생성 실행**
```bash
python scripts/make_country_maps.py {영어slug}
```
`public/images/size/{영어slug}-A-korea-beside.svg` 등 4개 파일이 생기는지 확인. **이 SVG 4종이 이 시리즈의 핵심 차별점**(CLAUDE.md) — AI 이미지 생성이나 스톡 이미지로 절대 대체하지 않는다.

## 2단계 — 팩트체크 (WebSearch)

다음 항목을 실제 웹서치로 확인 (지어내지 않기):
- 면적(㎢), 한국(약 10만㎢) 대비 배수
- 인구(최신), 수도와 인구, 주요 도시 2~3곳
- 1인당 GDP, 통화명
- 인천발 직항 비행시간, 시차(UTC 기준 한국과 차이)
- 치안 특이사항, 대략적인 물가 수준(현지 식당 vs 관광지 가격)
- 역사·문화 특징 3~5개 (독립사, 종교, 민족 구성, 특이한 지리 등)
- 한국인이 많이 찾는 여행지 top 3~5 (검색해서 실제로 언급되는 곳 위주)

## 3단계 — 본문 작성

**entry_slug/title/date/category/description** frontmatter 작성 (category는 `지구 상식`).

**페르소나 서두**: `kakao-chat-intro` 스킬로 랄라·케이 말풍선 대화를 frontmatter 바로 다음, 첫 이미지/본문 전에 삽입. 대사는 이 나라만의 소재로 매번 새로 쓴다(재사용 금지). 말풍선 2~4개, 먼저 말하는 사람 고정하지 않기.

**본문 구조** (CLAUDE.md 나라비교 시리즈 형식 그대로):
1. 도입 — 이 나라를 다루게 된 계기
2. `## {나라} 위치/크기` — 면적, 배수, 주변 지형
3. `## 우리나라가 {나라} 옆에 있을 때에 크기 비교` — 1단계 SVG의 A, B 삽입
4. `## {나라}가 우리나라 옆에 있을 때에 크기 비교` — 1단계 SVG의 C, D 삽입
5. `## {나라} 인구/수도/주요도시`
6. `## {나라} 역사·문화 특징` — 불릿 리스트
7. `## {나라} 여행 정보` — 비행시간/시차, 치안/물가, 음식 소제목
8. `## 한국인이 좋아하는 {나라} 대표 관광지` — top 3~5 + 요약 표 (인도네시아 글 참고)
9. `## 한국 vs {나라} 비교표`
10. 마무리 감상 (반말체, 솔직한 개인 감상) + **관련국 내부링크**

**관련국 내부링크 규칙**: 지리적으로 인접했거나 문화적으로 실제 연관된 **이미 발행된** 글에만 링크. 아직 안 쓴 나라는 하이퍼링크 없이 나라 이름만 텍스트로 언급(끊긴 링크 방지). 여유가 있으면 기존 인기 구버전 글 쪽에도 이 신규 글로 향하는 역링크를 자연스러운 문장으로 추가한다(A안 내부링크 전략과 동일한 원칙).

**팩트 오류 주의**: 거리·수치 비교("서울-OO까지 거리와 맞먹는다" 류)는 반드시 실제 거리를 검색해서 검증한다. 대략적인 어림짐작으로 쓰지 않는다.

## 4단계 — 썸네일 (`add-thumbnail` 스킬 호출)

```
Skill: add-thumbnail
args: {파일slug}
```
⚠️ 이 프로젝트에서 `thumbnail` frontmatter 필드는 글 상세 페이지의 큰 히어로 이미지가 **아니라** OG 메타 이미지(`BlogPost.astro`) + 홈/카테고리/관련글 목록 카드(`[...page].astro`, `category/[category].astro`, `RelatedPosts.astro`)에 쓰인다. 카드용 저해상도가 아니라 **OG 기준 1200x630**으로 받아야 한다. frontmatter에 `thumbnail:` 추가 + 본문 최상단에도 같은 이미지를 `![...](thumbnail경로 "설명")`로 삽입한다.

## 5단계 — 홈 세계지도 반영 (`src/components/WorldMap.astro`)

**a) 좌표 계산.** 이 SVG는 `viewBox="0 0 1000 500"`의 단순 선형 변환이지만 공식이 문서화돼 있지 않으므로, 지리적으로 가까운 **정확한 지점(수도급)** 기존 핀 2개를 찾아 역산한다:
```
grep -A1 'data-name="{근처나라1}"' src/components/WorldMap.astro
grep -A1 'data-name="{근처나라2}"' src/components/WorldMap.astro
```
`x = a*경도 + b`, `y = c*위도 + d` 형태의 1차방정식 두 개를 세워 a,b,c,d를 구한 뒤, 새 나라 수도의 경도/위도를 대입해 cx, cy를 계산한다. (참고: 싱가포르 103.85E,1.35N→cx788.9,cy246.4 / 필리핀(마닐라) 120.98E,14.6N→cx838.9,cy216.4 로 검증된 계수: a≈2.918, b≈485.84, c≈-2.264, d≈249.46 — 동남아·동아시아 국가는 이 계수를 그대로 재사용 가능. 다른 대륙은 그 대륙 근처의 핀 2개로 새로 역산할 것.)

**b) 지도 핀 추가**: 지리적으로 가까운 기존 나라 `<a class="map-pin-link">` 블록 바로 뒤에 동일한 구조로 삽입:
```html
<a href="/entry/{영어slug}" class="map-pin-link" data-name="{한글국명}" data-title="{title 그대로}" aria-label="{한글국명} 비교 글 보기">
  <circle class="pin-outer" cx="{계산값}" cy="{계산값}" r="7" fill="#1e40af" opacity="0.2"/>
  <circle class="pin-dot" cx="{계산값}" cy="{계산값}" r="3.5" fill="#1e40af" stroke="white" stroke-width="1"/>
</a>
```

**c) 대륙 패널 버튼 목록에 추가**: 해당 대륙 `data-panel="{대륙}"` 블록 안, 한글 가나다순 정렬 위치에 삽입:
```html
<a href="/entry/{영어slug}" class="inline-flex items-center rounded-lg px-3 py-1.5 text-sm font-medium border transition-all active:scale-95 hover:shadow-sm" style="background:#fef3c7;color:#92400e;border-color:#fcd34d">{한글국명}</a>
```

**d) 카운트 갱신** (3곳):
- 최상단 `aria-label="{N}개국 비교 글 위치를..."` — 전체 국가 수 +1
- `<p class="text-[11px] ...">총 {N}개국 · 6개 대륙</p>` — 전체 국가 수 +1
- 해당 대륙 `<span class="text-xs ...">({N}개국)</span>` — 그 대륙 수 +1

## 6단계 — 검증 및 배포

```bash
npm run build   # 에러 없이 완료되는지 확인, 새 글 페이지가 목록에 나오는지 확인
git status --short   # 이번에 작업한 파일만 골라서 add (기존에 있던 무관한 미커밋 파일 섞이지 않게 주의)
git add {새 글 .md} {지도 SVG 4개} {geodata 새 파일 있으면} scripts/make_country_maps.py src/components/WorldMap.astro public/images/{썸네일}
git commit -m "feat: {나라} 신규 글 발행 (크기비교 지도 + 홈 세계지도 반영)"
git push origin master
```
push 전 `git fetch && git log --oneline HEAD..origin/master`로 원격에 새 커밋(다른 경로/CMS 편집)이 있는지 확인하고, 있으면 merge 후 다시 build 확인하고 push한다. **배포(git push)는 사용자가 명시적으로 "배포해줘"라고 할 때만 실행** — 그 전 단계(1~6단계의 build까지)는 자동으로 진행해도 되지만 push는 매번 확인받는다.

## PROGRESS.md 기록

작업 끝나면 PROGRESS.md에 오늘 날짜 섹션(없으면 최상단에 신규 추가)으로: 어떤 나라를 어떤 절차로 만들었는지, geodata를 새로 만들었는지, 어떤 파일들을 건드렸는지 간단히 기록하고 "다음 발행 순서" 대기열에서 이번 나라를 제거/체크한다.
