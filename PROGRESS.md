# PROGRESS.md — 작업 기록

---

## 2026-06-26 작업

### 오늘 한 일

#### 1. 쿠팡 파트너스 배너 연동
- `src/components/CoupangBanner.astro` 신규 작성
- 고객 관심 기반 추천 300×250 다이나믹 배너 삽입
- 공정위 필수 고지문 배너 위에 항상 표시
- `ENABLED = true/false` 한 줄로 전체 ON/OFF 가능 (애드센스 신청 전 끄기용)
- 모든 글 본문 아래에 자동 삽입

#### 2. About 페이지 신규 생성 (`/about`)
- 랄라(하늘색, 호기심 여행자·감상 담당) + 케이(초록색, 팩트·데이터 담당) 가상 2인 캐릭터
- 가상 캐릭터임을 투명하게 명시
- 광고·제휴 고지 포함 (애드센스 심사 대비)
- 푸터 바로가기에 링크 추가
- 내부 스타일 가이드처럼 읽히는 '대화 예시' 블록 피드백 반영해 즉시 삭제

#### 3. 사이트 표기 전면 통일
- 헤더 로고, 푸터 브랜드, 저작권, 글 `<title>`, RSS, JSON-LD 등
- `lalalakorea` → `trip.lalalakorea` 전체 정리

#### 4. 카테고리 비공개 처리
- `커피` (42.md), `유튜버 되기 자료` (81.md) → `draft: true`
- 목록·카테고리·entry·사이트맵·RSS에서 자동 제외
- 트래픽 없는 단일 글 카테고리가 사이트 일관성 해침

#### 5. RSS 제목 수정
- `lalalakorea` → `trip.lalalakorea` (피드 채널 제목 + `<head>` link title)

#### 6. 글 레이아웃 순서 최적화
- 공유 버튼: 쿠팡 배너 아래, 같은 카테고리 글 위로 이동
- 작성자 박스(랄라·케이): 목록으로 돌아가기 아래 최하단으로 이동
  - 이유: 공유→이전/다음→목록 행동 후 브랜드 인상을 마지막에 남기는 구조

#### 7. 위로가기 플로팅 버튼
- 우하단 고정 (`bottom-6 right-6`)
- 스크롤 300px 이상 시 등장, 클릭 시 smooth scroll 최상단 이동
- 모든 페이지에 전역 적용

---

### 완료된 항목
- [x] 쿠팡 배너 연동 + 공정위 고지문 + ON/OFF 토글
- [x] About 페이지 (랄라·케이 2인 캐릭터)
- [x] trip.lalalakorea 표기 전면 통일
- [x] 커피·유튜버 카테고리 비공개
- [x] RSS 제목 수정
- [x] 글 레이아웃 순서 최적화 (공유버튼·작성자박스 위치)
- [x] 위로가기 플로팅 버튼

---

### 다음에 할 일 (나중에 검토)
- [ ] **Task B**: WorldMap 인라인 SVG(171KB) → `/public/world-map.svg` 분리 후 비동기 로드 (홈 HTML 경량화)
- [ ] **Task C**: 이미지 1,394장(약 239MB) WebP 변환 (약 50% 용량 절감)
- [ ] Pretendard 폰트 `font-display: swap` 적용 (FOUT 방지)
- [ ] 다크 모드 지원
- [ ] 콘텐츠 전략 실행 (전세금→해외집 시리즈, 한반도에 나라 넣기 시리즈)
- [ ] 애드센스 신청 전 쿠팡 배너 `ENABLED = false` 처리
- [ ] 애드센스 승인 후 쿠팡 배너 재활성화 여부 결정

---

## 2026-06-19 작업

### 오늘 한 일

#### 1. 사이트 전면 진단 및 1차 개선 (기술SEO·성능·접근성)
- React 통합 제거 — 미사용 번들 정리 (gzip 약 61KB 절감, client JS 0건)
- 사이트맵 확장: 40개 → 145개 URL (홈 + 페이지네이션 6 + 카테고리 8 + 글 140)
- 전역 JSON-LD 추가: WebSite + Organization 스키마
- 페이지네이션에 `rel="prev"` / `rel="next"` 추가
- `robots.txt`에 `/admin/`, `/api/` 차단 규칙 추가
- `vercel.json` 캐시 헤더 추가: `_astro/*`(1년 immutable), `/images/*`(30일), `/favicon.svg`(7일)
- 모바일 카테고리 드롭다운 JS 토글 수정 (터치 환경 `group-hover` 미동작 대응)
- WorldMap 키보드 접근성 추가 (Enter/Space, focus-visible)

#### 2. Task A — 이미지 CLS(레이아웃 이동) 수정
- `src/plugins/rehype-img-size.mjs` rehype 플러그인 신규 작성
- 빌드 시 `/images/...` 마크다운 이미지의 실제 픽셀 크기를 읽어 `width`/`height` 속성 자동 주입
- `astro.config.mjs`에 `rehypePlugins: [rehypeImgSize]` 연결
- `image-size` 패키지 추가
- 원본 .md 파일은 손대지 않고 빌드 단계에서만 처리

### 완료된 항목
- [x] React 제거 (번들 경량화)
- [x] 사이트맵 145개 URL 생성
- [x] WebSite / Organization 구조화 데이터
- [x] rel prev/next
- [x] robots.txt admin/api 차단
- [x] vercel.json 캐시 헤더
- [x] 모바일 카테고리 드롭다운 수정
- [x] WorldMap 키보드 접근성
- [x] Task A: 이미지 width/height 자동 주입 (CLS 개선)
