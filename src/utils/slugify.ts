/**
 * 카테고리 이름을 URL 슬러그로 변환
 * 예: "해외 여행" → "해외-여행"
 * 예: "지구 위기& 재난 대비" → "지구-위기-재난-대비"
 */
export function slugify(str: string): string {
  return str
    .replace(/&/g, '')        // & 제거
    .replace(/\s+/g, '-')     // 공백 → 하이픈
    .replace(/-+/g, '-')      // 중복 하이픈 제거
    .replace(/^-+|-+$/g, ''); // 앞뒤 하이픈 제거
}
