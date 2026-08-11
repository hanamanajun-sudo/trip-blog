# PROGRESS.md — 작업 기록

---

## 2026-08-11/12 작업 — Vercel → Cloudflare Workers 이전 완료

### 배경
lalalakorea.com(같은 계정의 자매 사이트)이 2026-08-08/09에 먼저 Cloudflare Workers로 이전 완료. 그 경험(런타임 fs 의존성 제거, 25MiB 파일 제한, Windows 빌드 이슈, page 라우팅 버그, DNS 컷오버 절차)을 참고해 trip.lalalakorea.com도 동일하게 이전.

### 오늘 한 일
1. **스택 확인** — trip-blog는 Astro v5.18(`output: 'static'`) + `@astrojs/vercel`, Decap CMS용 서버 라우트 3개(`api/oauth.ts`, `api/oauth/callback.ts`, `api/decap-config.ts`, 전부 `prerender = false`)가 있어 순수 정적 사이트는 아님. lalalakorea(Next.js)와 스택이 달라 문제 유형도 다름 — fs 런타임 의존성 문제는 없었고(Astro 콘텐츠 컬렉션이라 빌드 시점에 이미 정적화됨), 핵심은 3개 API 라우트의 `process.env` 처리와 `vercel.json` 변환이었음
2. **어댑터 교체** — `@astrojs/vercel` → `@astrojs/cloudflare`. 최신 14.x는 astro 7 요구(설치 실패) → astro 5.7+와 호환되는 `12.6.13`으로 버전 고정 (lalalakorea의 opennextjs-cloudflare 버전 고정 이슈와 동일 패턴)
3. **env 접근 방식 변경** — Cloudflare Workers 런타임엔 `process.env`가 없음 → `oauth.ts`/`callback.ts`를 `import { env } from 'cloudflare:workers'` 방식으로 교체
4. **vercel.json → Cloudflare 방식 변환** — redirects 6개 → `public/_redirects`(플레이스홀더 이미지, 태그, `/m/entry/` 등, 전부 301), headers 4개 → `public/_headers`(admin noindex, `_astro` 1년 캐시, images 30일 캐시, favicon 7일 캐시)
5. **Workers 배포 구성** — `wrangler.jsonc` 신규 작성 (Pages 아님, lalalakorea와 동일하게 Workers 방식). `public/.assetsignore`에 `_worker.js` 추가해 서버 코드가 정적 자산으로 그대로 노출되는 것 방지. `compatibility_date`를 미래 날짜로 잘못 넣었다가 배포 시점 API가 거부 → 과거 날짜로 수정
6. **프리뷰 검증 후 배포** — `trip-lalalakorea.hanamanajun.workers.dev`에서 홈/RSS/CMS 설정/admin/리다이렉트/캐시헤더/OAuth 시크릿 전달까지 curl로 전수 확인
7. **GitHub OAuth 시크릿 등록** — Vercel엔 `KEYSTATIC_GITHUB_CLIENT_ID`/`SECRET`으로 등록돼 있던 값을 `wrangler secret put`으로 Worker에 재등록 (사용자가 직접 값 입력, Claude는 시크릿 값 자체를 다루지 않음 — `vercel env pull`은 자동 권한 분류기가 시크릿 유출 위험으로 차단함)
8. **실제 도메인 OAuth 로그인 테스트의 한계 발견** — DNS 컷오버 전에 workers.dev 프리뷰에서 미리 전체 로그인 흐름을 테스트하려 했으나 불가능함을 확인: GitHub OAuth App은 콜백 URL을 하나만 등록 가능(`trip.lalalakorea.com` 고정)이라, 다른 도메인(workers.dev)에서 열면 GitHub이 애초에 인증 페이지 진입을 막음. 즉 이런 구조에서는 실제 로그인 테스트는 DNS 컷오버 후에만 가능 — 다음에 유사 마이그레이션 시 참고할 것
9. **git 브랜치 전략** — master에 바로 커밋하지 않고 `cloudflare-migration` 브랜치 사용(lalalakorea의 `cloudflare-migration-prep`과 동일 패턴). 이유: master에 바로 push하면 Vercel이 다음 배포 때 cloudflare 어댑터로 재빌드를 시도해 DNS 컷오버 전까지의 Vercel 롤백 안전망이 깨짐
10. **DNS 컷오버** — `wrangler.jsonc`에 `routes: [{pattern: "trip.lalalakorea.com", custom_domain: true}]` 추가 후 `wrangler deploy`. lalalakorea 때와 동일하게 "기존 외부 DNS 레코드가 있어 실패" 에러 발생 → Cloudflare 대시보드에서 기존 `trip` CNAME(→ vercel-dns) 레코드를 사용자가 직접 삭제 → 재배포로 커스텀 도메인 연결 성공. Claude의 wrangler 토큰은 zone read-only라 DNS 레코드 삭제는 대시보드에서 사용자가 직접 수행해야 했음
11. **서치콘솔 검증 확인** — `google-site-verification` TXT 레코드는 서브도메인(`trip`)이 아니라 apex(`lalalakorea.com`)에 있는 Domain 타입 속성이라 `trip` CNAME 삭제와 무관하게 보존됨을 nslookup으로 확인
12. **merge 시점 원격 충돌 처리** — master push 시도 시 원격에 Decap CMS 자동 커밋(콘텐츠 수정 수십 건, 새 글/이미지)이 먼저 올라와 있어 거부됨 → 강제 push 대신 `git merge origin/master`로 안전하게 통합(충돌 없음) → 병합된 최신 콘텐츠까지 포함해 재빌드·재배포 후 push
13. **최종 검증** — 사용자가 브라우저에서 `https://trip.lalalakorea.com/admin/`으로 실제 GitHub 로그인 끝까지 성공 확인 (팝업 → 인증 → CMS 글 목록 진입)

### 완료된 항목
- [x] `@astrojs/cloudflare@12.6.13` 설치 + `astro.config.mjs` 어댑터 교체
- [x] `oauth.ts`/`callback.ts` env 접근 방식을 `cloudflare:workers`로 교체
- [x] `vercel.json` redirects/headers → `public/_redirects`/`public/_headers`
- [x] `wrangler.jsonc` 작성, `package.json`에 `cf:preview`/`cf:deploy` 스크립트 추가
- [x] workers.dev 프리뷰 배포 + 전체 라우트 curl 검증
- [x] GitHub OAuth 시크릿(`KEYSTATIC_GITHUB_CLIENT_ID`/`SECRET`) Worker에 재등록
- [x] `cloudflare-migration` 브랜치 → master merge, 원격 콘텐츠 커밋과 충돌 없이 통합
- [x] **실제 도메인 이전 완료** — `trip.lalalakorea.com`을 Cloudflare Worker 커스텀 도메인으로 연결, 기존 `trip` CNAME(Vercel) 삭제
- [x] 서치콘솔 apex TXT 레코드 무영향 확인
- [x] 실제 브라우저 GitHub OAuth 로그인 최종 확인 (사용자 확인 완료)

### 다음에 할 일
- [ ] **Vercel 프로젝트(trip-blog) 삭제 검토** — lalalakorea와 동일하게 2주 정도 안정성 지켜본 뒤 정지/삭제 검토 (목표 시점: 2026-08-26 전후). 그때까지 `vercel.json`, `@astrojs/vercel` 의존성은 롤백 안전망으로 유지
- [ ] **서치콘솔 모니터링** — 호스팅 변경 후 1~2주간 크롤 오류·색인 상태 확인
- [ ] **CLAUDE.md 갱신** — "Astro v4 + Vercel" 문구를 "Astro v5 + Cloudflare Workers"로 수정 필요

---

## 2026-07-25 작업

### 오늘 한 일

#### 1. 서치 콘솔 색인 누락 원인 전수 진단
- [페이지] 탭 6개 카테고리(크롤링됨-미색인 284건, 404 236건, 리디렉션 104건, 대체페이지 13건, 403 2건, robots차단 2건, 발견됨-미크롤링 2건) 전수 분석
- 라이브 사이트 직접 검증(curl, robots.txt/sitemap-index.xml 원본 대조)으로 결론: **전부 티스토리→Astro/Cloudflare 이관 잔재이거나 구글의 정상 동작**, 실제 발행 글의 저품질/미색인 문제 아님
  - 404·크롤링됨-미색인: 티스토리 URL 패턴(`/entry/`, `/m/entry/`, `/tag/`, `/category/`, 숫자 퍼머링크, 랜덤 shortlink) 대다수
  - 리디렉션 104건: 트레일링 슬래시 308 리디렉션, 사이트맵·RSS·canonical 전부 정상이라 사이트 문제 아님
  - 403/robots차단: 죽은 티스토리 지도 플러그인·방명록 URL, 사실상 무해
- [실적] 탭 3개월 데이터로 최종 검증: 트래픽 4월 대비 7~8배 성장(일 15→100~180클릭), Top 페이지 전부 "나라 비교" 시리즈 글 — 실제 콘텐츠는 색인·트래픽 모두 건강함을 확인

#### 2. 콘텐츠 개선 실행 기획 수립 (A안/B안)
- **A안(내부링크)**: 구버전 한글 슬러그 글(49개, 트래픽 높음) → 신규 영어 슬러그 글(29개, 트래픽 낮음) 지역별 클러스터링 후 상호 내부링크 계획
  - 중동/아프리카/중남미/유럽/아시아/북미·오세아니아 6개 클러스터로 구분, 클러스터별 발신처(기존 인기글)·수신처(신규 저트래픽글) 매핑
  - 1단계: 클릭 상위 15개 구버전 글에 신규 글 링크 추가 → 2단계: 신규 29개 글에 역링크 추가
- **B안(신규 발행)**: 검색어 데이터 기반 미커버 인기 국가 우선순위 목록 + CTR 낮은 기존 글 제목 최적화 대상 도출

---

#### 3. A안 1단계 실행 — 구버전 인기글 → 신규 저트래픽 글 내부링크
- 18개 고트래픽 한글 슬러그 글(47,91,48,85,90,107,76,51,32,58,69,98,53,44,56,70,28,54.md)에 지역·문맥 기반 자연스러운 내부링크 문장 추가
- 신규 영어 슬러그 글 29개 전체가 최소 1개 이상 내부링크를 받도록 커버리지 완성 (기존 스코틀랜드·파키스탄 링크 포함)
- 지리적/문화적으로 실제 연관된 국가끼리만 연결(예: 포르투갈→브라질은 기존 서술에 있던 문장에 링크만 추가, 뉴질랜드→호주도 기존 문장 활용)

#### 4. 사용자 피드백 반영 + B안 착수
- `58.md`(뉴질랜드) "뉴질랜드와 호주 헷갈린다" 문장이 부자연스럽다는 피드백 → 워킹홀리데이 문맥으로 자연스럽게 교체
- `123.md`(수에즈 운하) — 실적 상위권 글인데 이집트 비교글 링크가 없어서 "이집트 소유이다" 문장에 `/entry/egypt-vs-korea-size-population-travel` 링크 추가
- `121.md`(발칸반도) 제목·설명 리라이팅 완료 — 노출 19,838회/클릭 77건(CTR 0.39%, 평균순위 8.5)로 데이터상 최우선 CTR 개선 대상이었음. 제목을 키워드 전진 배치 + 간결화, 설명도 축약. **entry_slug는 그대로 유지**(CLAUDE.md 규칙: slug는 절대 변경 금지)
- 나라 비교글 지도 이미지 생성 방식 조사 완료 (아래 별도 기록)

#### 5. 나라 비교글 지도 이미지 생성 방식 조사 결과
- `scripts/make_country_maps.py`: 람베르트 정적방위도법 기반, 외부 라이브러리 없이 표준 라이브러리만 사용하는 **완전 프로그래밍 방식** SVG 생성기 확인 (`scripts/geodata` 실제 국경 좌표 사용). 커밋 이력상 이전 Claude 세션이 작성.
  - 이 스크립트로 만들어진 나라(25개, `public/images/size/`에 SVG 존재): 알제리·벨기에·보스니아·브라질·카보베르데·콜롬비아·퀴라소·체코·에콰도르·이집트·독일·가나·이라크·코트디부아르·요르단·멕시코·네덜란드·파나마·파라과이·사우디아라비아·스코틀랜드·세네갈·튀니지·미국·우즈베키스탄
  - **이란·태국·파키스탄·호주 4개국은 이 스크립트로 만들어지지 않음** — 실제 이미지 파일명이 `177549190949.png` 같은 유닉스 타임스탬프 패턴(AI 이미지 생성 도구의 전형적 자동 명명 방식)이라 별도의 외부 AI 이미지 생성 도구로 제작된 것으로 추정. Claude(나)는 이 환경에서 이미지 생성 도구 자체가 없어 어떤 지도 이미지도 직접 만든 적 없음.
  - 구버전 49개 글(47.md 등)의 이미지는 `d10c88f8.png` 같은 8자리 해시 파일명 — 티스토리 이관 시 그대로 가져온 이미지로 추정, 스크립트/AI 생성과 무관.

#### 6. 사용자 재피드백 반영
- `58.md`(뉴질랜드) 문장 재수정: "호주와 헷갈린다"는 어색한 표현 삭제 → 워킹홀리데이 문맥으로 교체
- `123.md`(수에즈 운하) "이집트 소유이다" 문장에 이집트 비교글 링크 추가 (실적 상위권 글에 빠져있던 연결)
- `121.md`(발칸반도) 제목·설명 리라이팅 실행 (노출 19,838/클릭 77/CTR 0.39%/평균순위 8.5 — 최우선 CTR 개선 대상)

#### 7. 인도네시아 신규 글 작성 — B안 1번째
- `scripts/make_country_maps.py`에 인도네시아(IDN) 설정 추가 (NAMES/CAPITALS/COUNTRIES 딕셔너리)
- `scripts/geodata/IDN.geo.json` 신규 생성 — Natural Earth 50m 데이터를 GitHub 미러(nvkelso/natural-earth-vector)에서 받아 `build_geodata.py IDN` 실행
  - **주의(다음 세션 참고)**: Windows에서 `NE_SRC` 경로를 bash의 `/tmp/...` 그대로 주면 Python(네이티브 exe)이 못 찾음 → `cygpath -w`로 변환한 실제 Windows 경로(`C:/Users/.../AppData/Local/Temp/...`)를 넘겨야 함. 또한 이 저장소 환경엔 `python3`가 아니라 `python` 명령으로 실행해야 함 (`python3`는 빈 WindowsApps 스텁으로 연결됨)
- `python scripts/make_country_maps.py indonesia` 실행 → SVG 4종(`public/images/size/indonesia-*.svg`) 생성 완료
- 신규 글 발행: `인도네시아-크기-비교-및-인구-여행-정보-한국-면적의-19배라고.md`
  - entry_slug: `indonesia-vs-korea-size-population-travel`
  - 웹서치로 팩트체크(면적 191.7만㎢/한국의 19배, 인구 2억8790만·세계4위, 자카르타, 1인당GDP 5,362달러, 비행시간 7시간, 시차 1~2시간 등)
  - 기존 태국 글로 내부링크 연결, 아직 없는 말레이시아는 링크 없이 텍스트로만 예고(끊긴 링크 방지)

#### 8. 인도네시아 글 썸네일 + 홈 세계지도 반영 + 배포
- `add-thumbnail` 스킬로 Unsplash에서 발리 계단식 논 사진 확보 (1200x630, 165KB로 압축) → `public/images/indonesia-thumb.jpg`
  - frontmatter에 `thumbnail` 필드 추가 + 본문 상단에도 이미지 삽입
  - 주의: 이 프로젝트에서 `thumbnail` 필드는 글 상세 페이지에 큰 히어로로 렌더링되지 않고 **OG 메타 이미지 + 목록/관련글 카드**에만 쓰임 (`BlogPost.astro`/`RelatedPosts.astro`/`[...page].astro`/`category/[category].astro`) — 그래서 카드용 작은 크기가 아니라 OG 기준(1200x630)으로 받음
- `src/components/WorldMap.astro`(홈 세계지도)에 인도네시아 추가
  - 기존 싱가포르·필리핀 핀 좌표로 좌표계 역산(선형회귀) 후 자카르타 좌표(cx=797.6, cy=263.5) 계산해 핀 추가
  - 아시아 대륙 패널 국가 버튼 목록에도 가나다순 위치(이스라엘-일본 사이)에 추가
  - 국가 수 카운트 갱신: 전체 75→76개국, 아시아 22→23개국
- `npm run build` 2회 정상 완료 확인 (에러 없음)
- git add/commit/push로 배포 완료 (이번 세션 관련 파일만 스테이징, 기존에 있던 무관한 `quality-*.json`/`quality-stage1.md`는 제외)
- push 시 원격에 다른 경로(CMS로 추정)로 올라온 커밋들(스코틀랜드·사우디아라비아·이집트 글 수정)과 충돌 없이 머지 완료 → 재빌드 확인 후 최종 푸시 (071465a)

#### 9. 인도네시아 글 팩트 오류 수정 + 관광지 섹션 추가 + 파이프라인 스킬화
- 사용자 팩트체크 지적 반영: "동서 길이 5,100km가 서울-로마 거리와 맞먹는다"는 오류 수정 → 실제로는 서울-뭄바이 거리에 해당(로마는 약 8,975km로 거의 2배). 서울-뭄바이로 정정.
- `## 한국인이 좋아하는 인도네시아 대표 관광지` 섹션 신규 추가 (발리·길리 아일랜드·브로모 화산·코모도-라부안 바조·족자카르타 top5 + 요약표), 사용자가 준 리스트를 블로그 반말체·톤으로 재작성
- **`.claude/skills/country-comparison-post/SKILL.md` 신규 생성** — 인도네시아 글 작업 과정에서 검증된 전체 파이프라인(중복확인 → 지도SVG생성 → 팩트체크 → 페르소나서두+본문작성 → 관련국 내부링크 → 썸네일 → 홈 세계지도 반영 → 빌드검증 → 배포)을 프로젝트 스킬로 문서화. 앞으로 "{나라} 글 써줘" 요청 시 이 스킬이 자동 트리거되어 매 단계를 다시 설명할 필요 없음.
  - Windows 경로 함정(NE_SRC, python3 스텁), WorldMap 좌표 역산 계수(싱가포르·필리핀 기준 a≈2.918,b≈485.84,c≈-2.264,d≈249.46) 등 이번에 얻은 노하우를 스킬 안에 그대로 기록해둠

---

### 완료된 항목
- [x] 서치콘솔 색인 누락 원인 전수 진단 (크롤링됨-미색인·404·리디렉션·대체페이지·403·robots차단·발견됨 6개 카테고리 + 실적 데이터로 최종 검증 — 전부 티스토리 이관 잔재/정상 동작, 실제 콘텐츠는 색인·트래픽 건강함을 확인)
- [x] 콘텐츠 개선 실행 기획(A안 내부링크/B안 신규발행) 수립 및 PROGRESS.md 기록
- [x] A안 1단계: 구버전 고트래픽 글 18곳에 신규 저트래픽 글(영어 슬러그 29개) 내부링크 추가 — 29개 전체 커버리지 완성
- [x] 사용자 피드백 반영: 뉴질랜드(58.md) 어색한 문장 교체, 수에즈운하(123.md)→이집트 링크 추가, 발칸반도(121.md) 제목·설명 리라이팅
- [x] 나라 비교글 지도 이미지 생성 방식 조사 (스크립트 생성 25개국 vs 외부 AI 도구 생성 4개국 vs 티스토리 이관 이미지 구분)
- [x] 인도네시아 신규 글 발행 — 지도 SVG 4종 신규 생성(geodata 포함), 팩트체크, 관련국 내부링크, Unsplash 썸네일, 홈 세계지도(WorldMap.astro) 핀·목록·카운트 반영
- [x] 인도네시아 글 팩트 오류 수정(서울-로마→서울-뭄바이 거리) + "한국인이 좋아하는 대표 관광지" 섹션 추가
- [x] `.claude/skills/country-comparison-post` 스킬 신규 생성 — 나라비교 글 발행 전 과정(지도생성·팩트체크·내부링크·썸네일·홈지도반영·빌드·배포) 자동화
- [x] 오늘 변경사항 전체 `npm run build` 검증 후 git 커밋·푸시 2회 (원격 CMS 커밋과 충돌 없이 머지)

---

### 다음에 할 일
- [ ] 신규 발행 순서: **말레이시아(다음)** → 인도 → 아일랜드 → 덴마크 → 헝가리 → 칠레 → 페루 → 아랍에미리트 (`country-comparison-post` 스킬로 진행)
- [ ] 신규 발행 추가 2건: (1) 일본 현(都道府県)별 상세 정보 글 (2) 영국 구성국가 상세(잉글랜드·스코틀랜드·웨일스·북아일랜드) 글
- [ ] A안 2단계: 신규 29개 영어 슬러그 글 쪽에서도 구버전 인기글로 역링크 추가 검토
- [ ] 배포된 내부링크 20곳 + 인도네시아 신규글 실제 사이트 렌더링(지도 SVG 포함) 육안 확인
- [ ] `country-comparison-post` 스킬을 실제로 다음 나라(말레이시아)에 적용해보고 스킬 문서 보완할 부분 있는지 점검

---

## 2026-07-19 작업

### 오늘 한 일

#### 1. 신규 글 작성 — 해외 리조트 BEST6
- 더쿠 화제글을 소재로 신규 글 작성: "더쿠에서 화제 된 '천국처럼 느껴졌던 해외 리조트(숙소)' BEST6 파헤쳐보기"
- 괌 두짓타니, 발리 아야나·더카욘정글, 푸꾸옥 리젠트, 끄라비 라야바디, 칸쿤 스칼렛아르떼 6곳의 위치·특징·주변 지역 정보 상세 작성
- 웹서치로 팩트체크 (아야나 수영장 개수, 라야바디 부지 면적·해변 명칭 등 오류 수정) + content-review 스킬로 검증
- 6곳 공식 홈페이지 링크 삽입 (새 창 열기)
- entry_slug: `dreamy-overseas-luxury-resorts-best6-guide`, category: 해외 여행

#### 2. 이미지 작업
- Unsplash에서 6개 리조트 분위기 사진 다운로드·압축 후 배치
- 사용자가 업로드한 위치 지도 이미지 8장 배치 (광역 지도 + 리조트 핀 지도, 발리·푸꾸옥은 2장씩 구성)

#### 3. 랄라·케이 페르소나 도입
- about 페이지에만 있던 랄라(감상 담당)·케이(팩트 담당) 캐릭터를 블로그 글 본문에 처음으로 적용
- 초기 버전: 카카오톡 채팅앱 스타일(헤더바+시계+아바타) → "상투적 위젯처럼 보인다"는 피드백으로 헤더·시계·아바타 없는 심플 말풍선으로 단순화
- 랄라 말풍선 배경색이 사이트 배경색(`#F0F9FF`)과 겹쳐 안 보이던 버그 발견 및 수정 (흰 배경+테두리로 대비 확보)
- 다음에 재사용할 수 있도록 `kakao-chat-intro` 글로벌 스킬 신규 제작 (`~/.claude/skills/kakao-chat-intro/`)

#### 4. 요금 정보 추가 (SEO)
- 6개 리조트의 실제 1박 요금대를 Agoda·Booking.com·KAYAK 등에서 웹서치로 조사해 반영
- 조사 중 기존 서술 오류 발견·정정: "리젠트 푸꾸옥이 가성비 좋다" → 실제로는 전객실 풀빌라라 6곳 중 비싼 축(약 50만~130만원)임을 확인 후 본문·비교표 전부 수정
- 요금 정보를 볼드 문단(`**1박 요금대:**`) → `### OO 가격` H3 소제목으로 전환 (가격 관련 롱테일 검색 노출 강화 목적)
- 요약표에 "1박 요금대" 열 신규 추가 + 환율·출처 각주

---

### 완료된 항목
- [x] 해외 리조트 BEST6 신규 글 작성·발행 (커밋·푸시 완료)
- [x] 리조트 6곳 분위기 사진 + 위치 지도 8장 삽입
- [x] 랄라·케이 카톡 스타일 말풍선 인트로 적용 (심플 버전으로 확정, 대비 버그 수정)
- [x] `kakao-chat-intro` 글로벌 스킬 제작
- [x] 6개 리조트 1박 요금대 조사·반영 및 H3 소제목 전환

---

### 다음에 할 일
- [ ] 배포 후 trip.lalalakorea.com에서 실제 렌더링 육안 확인 (지도 위치, 말풍선 대비, 요금 H3 노출)
- [ ] `kakao-chat-intro` 스킬을 다른 기존 글에도 적용할지 결정 (현재는 이 글에만 적용됨, 모든 글에 기계적으로 넣지 않기로 함)
- [ ] quality-stage1.md 기준 이미지 없는/글자수 부족 글 보강 작업 이어가기
- [ ] 신규 글 작성 이어가기 (나라 비교 시리즈 등)

---

## 2026-06-29 작업

### 오늘 한 일

#### 1. About 페이지 전면 개편
- 기존 단순 소개 텍스트 → **랄라/케이 두 캐릭터 대화(말풍선) 스타일**로 전면 재작성
- git 히스토리 전체 확인 — 이전에 커밋된 두 캐릭터 버전 없음 확인 → 새로 작성
- 캐릭터 설정:
  - **랄라** (L, sky-blue) — 호기심 여행자, 솔직한 감상 담당
  - **케이** (K, emerald-teal) — 팩트 수집가, 면적·인구·시차·물가 수치 정리 및 비교표 담당
- 아바타: 글 하단 "이 글을 쓴 사람들" 박스와 동일한 그라데이션 L/K 뱃지로 통일
- 가상 캐릭터 면책 문구 포함

#### 2. About 페이지 연락처 변경
- 이메일(`hanamanajun@gmail.com`) → **카카오톡 검색 @infoepic** 으로 변경

#### 3. 애드센스 승인 확인
- 사용자가 애드센스 승인을 받았음을 공유
- BaseLayout에 `ca-pub-6443201130119317` 자동광고 스크립트 이미 삽입되어 있음 확인

#### 4. japansafe.infoepic.com 배너 추가 (총 6개 글)
일본 관련 모든 글 하단에 주황색 테두리 배너 삽입:
- [일본 지진 대처] 행동 요령 및 대피소 찾기
- 일본 현 개수? 각 현 특징 (127.md)
- 일본 vs 한국 비교 땅 면적, 지도, 인구수 (100.md)
- 일본 열도의 진짜 뜻과 군도·제도 차이점 (126.md)
- [일본 여행 추천] 월별 여행지 가이드 및 날씨
- 나고야 최고급 리조트 어디? (118.md)

#### 5. 비공개(draft) 글 현황 파악
총 12개 비공개 글 확인 → 모두 발행 안 하기로 결정
`4, 6, 7, 12, 14, 16, 21, 22, 42, 50, 81, 97.md`

---

### 완료된 항목
- [x] About 페이지 랄라/케이 캐릭터 대화 스타일 재작성
- [x] About 페이지 연락처 → 카카오톡 @infoepic
- [x] 애드센스 승인 확인
- [x] 일본 관련 글 6개 japansafe.infoepic.com 배너 삽입
- [x] 비공개 글 현황 파악 및 처리 방향 결정 (전부 비공개 유지)
- [x] 한글 slug 개선 — 하지 않기로 결정

---

### 다음에 할 일
- [ ] **신규 글 작성** — 나라 비교 시리즈 계속 (월드컵 출전국 등)
- [ ] **이미지 없는 글 보강** — quality-stage1.md 기준 `이미지없음` 표시 글들
- [ ] **japansafe 배너** — 일본 관련 신규 글 작성 시 하단에 동일 배너 포함할 것

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
