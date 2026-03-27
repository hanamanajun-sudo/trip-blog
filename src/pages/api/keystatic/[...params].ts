export const prerender = false;

import { makeGenericAPIRouteHandler } from '@keystatic/core/api/generic';
import config from '../../../keystatic.config';

const handler = makeGenericAPIRouteHandler({ config });

export async function ALL(context: any) {
  const { request } = context;

  // Keystatic handler 호출
  const result = await handler(request) as any;
  const { body, headers: rawHeaders, status } = result;

  // 헤더를 Map으로 변환
  const headersMap = new Map<string, string[]>();
  if (Array.isArray(rawHeaders)) {
    for (const [key, value] of rawHeaders) {
      const k = key.toLowerCase();
      if (!headersMap.has(k)) headersMap.set(k, []);
      headersMap.get(k)!.push(value);
    }
  }

  // Location 헤더에서 localhost → 실제 도메인으로 교체
  const locationValues = headersMap.get('location');
  if (locationValues) {
    headersMap.set(
      'location',
      locationValues.map(v =>
        v.replace(/https?:\/\/localhost(:\d+)?/g, 'https://trip.lalalakorea.com')
      )
    );
  }

  const flatHeaders = [...headersMap.entries()].flatMap(([key, vals]) =>
    vals.map(v => [key, v] as [string, string])
  );

  return new Response(body, { status, headers: flatHeaders });
}
