# PROGRESS.md — 2026-06-19 작업 기록

## 오늘 한 일

### 1. 사이트 전면 진단 및 1차 개선 (기술SEO·성능·접근성)
- React 통합 제거 — 미사용 번들 정리 (gzip 약 61KB 절감, client JS 0건)
- 사이트맵 확장: 40개 → 145개 URL (홈 + 페이지네이션 6 + 카테고리 8 + 글 140)
- 전역 JSON-LD 추가: WebSite + Organization 스키마
- 페이지네이션에 `rel="prev"` / `rel="next"` 추가
- `robots.txt`에 `/admin/`, `/api/` 차단 규칙 추가
- `vercel.json` 캐시 헤더 추가: `_astro/*`(1년 immutable), `/images/*`(30일), `/favicon.svg`(7일)
- 모바일 카테고리 드롭다운 JS 토글 수정 (터치 환경 `group-hover` 미동작 대응)
- WorldMap 키보드 접근성 추가 (Enter/Space, focus-visible)

### 2. Task A — 이미지 CLS(레이아웃 이동) 수정
- `src/plugins/rehype-img-size.mjs` rehype 플러그인 신규 작성
- 빌드 시 `/images/...` 마크다운 이미지의 실제 픽셀 크기를 읽어 `width`/`height` 속성 자동 주입
- `astro.config.mjs`에 `rehypePlugins: [rehypeImgSize]` 연결
- `image-size` 패키지 추가
- 원본 140개 .md 파일은 손대지 않고 빌드 단계에서만 처리

## 완료된 항목
- [x] React 제거 (번들 경량화)
- [x] 사이트맵 145개 URL 생성
- [x] WebSite / Organization 구조화 데이터
- [x] rel prev/next
- [x] robots.txt admin/api 차단
- [x] vercel.json 캐시 헤더
- [x] 모바일 카테고리 드롭다운 수정
- [x] WorldMap 키보드 접근성
- [x] **Task A: 이미지 width/height 자동 주입 (CLS 개선)** — 빌드 검증 완료, 커밋·푸시 완료

## 다음에 할 일 (나중에 검토)
- [ ] **Task B**: WorldMap 인라인 SVG(171KB) → `/public/world-map.svg` 분리 후 비동기 로드 (홈 HTML 경량화)
- [ ] **Task C**: 이미지 1,394장(약 239MB) WebP 변환 (약 50% 용량 절감)
- [ ] Pretendard 폰트 `font-display: swap` 적용 (FOUT 방지)
- [ ] 다크 모드 지원
- [ ] 제목 길이 최적화 (일부 105자 → 60자 이하 권장)
- [ ] 콘텐츠 전략 실행 (전세금→해외집 시리즈, 한반도에 나라 넣기 시리즈)
- [ ] E-E-A-T / 작성자 프로필 강화
- [ ] Search Console 인증 (현재 BaseLayout에 주석 처리)
