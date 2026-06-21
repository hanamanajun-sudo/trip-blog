# CLAUDE.md — trip.lalalakorea.com 작업 가이드

이 파일은 Claude가 이 블로그 작업 시 따라야 할 규칙을 기록한다.

## 프로젝트 개요
- **사이트**: trip.lalalakorea.com (Astro v4 + Vercel, 콘텐츠는 `src/content/blog/*.md`)
- **URL 구조**: `/entry/{entry_slug}` (entry_slug 없으면 파일 id 사용)
- **주력 콘텐츠**: "지구 상식" 카테고리의 **나라 비교 시리즈** (우리나라와 크기·인구·시차 비교)

## ✅ 글 작성 규칙

### slug(entry_slug) 규칙 — 중요
- **entry_slug는 반드시 영어(소문자 + 하이픈)로 작성한다.**
- **slug에는 연도·시즌·"월드컵" 등 시간이 지나면 바뀌는 정보를 절대 넣지 않는다.**
  - 이유: slug는 URL로 고정되어 한번 발행하면 바꾸기 어렵다(바꾸면 기존 링크·검색 색인이 깨짐). 따라서 시간이 지나도 변하지 않을 내용만 넣는다.
- 나라 비교 글 slug 형식: `{country}-vs-korea-size-population-travel`
  - 예) `brazil-vs-korea-size-population-travel`, `germany-vs-korea-size-population-travel`
- 반면 **title(제목)에는 시의성 문구를 넣어도 된다.** title은 언제든 자유롭게 수정 가능하기 때문.
  - 예) 제목: "브라질 vs 한국 크기 비교 ... - 2026 월드컵 최다 우승국 브라질 알아보기" (O)
  - slug: `brazil-vs-korea-size-population-travel` (연도·월드컵 미포함) (O)

### frontmatter 형식
```yaml
---
title: (시의성 문구 포함 가능)
date: YYYY-MM-DD
category: 지구 상식
entry_slug: (영어, 시간 무관 정보만)
description: (검색 미리보기용 2문장 요약)
---
```

### 나라 비교 시리즈 본문 구성 (기존 글 형식 유지)
1. 도입 — 이 나라를 다루게 된 계기(시의성)
2. 위치/크기 — 면적과 **한국 면적의 몇 배인지**
3. **한국 지도를 겹친 크기 비교** (이 시리즈의 핵심)
4. 인구/수도/주요 도시
5. 역사/문화 특징
6. 여행 정보 (비행시간·시차·치안·물가·음식)
7. **한국 vs OO 비교 표**
8. 마무리 감상
- 말투: 반말체 + 솔직한 개인 감상 (예: *"솔직히 우리나라 크기인줄 알았음"*)
- 같은 카테고리 글은 RelatedPosts로 자동 추천되며, 본문에서 관련국 글로 내부링크(`/entry/{slug}`)를 자연스럽게 건다.

### 이미지
- 직접 생성할 수 없는 비교 지도 등은 `<!-- TODO: ... -->` 주석 + `/images/placeholder-*.png` 경로로 자리표시 후, 나중에 실제 이미지로 교체한다.
