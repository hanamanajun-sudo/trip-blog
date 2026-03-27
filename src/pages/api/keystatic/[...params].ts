export const prerender = false;

import { makeGenericAPIRouteHandler } from '@keystatic/core/api/generic';
import config from '../../../../keystatic.config';

const handler = makeGenericAPIRouteHandler({ config });

function fixLocalhostUrl(url: string): string {
  return url.replace(/https?:\/\/localhost(:\d+)?/g, 'https://trip.lalalakorea.com');
}

export async function ALL(context: any) {
  let { request } = context;

  // localhost URL → 실제 도메인으로 교체
  if (request.url.includes('localhost')) {
    request = new Request(fixLocalhostUrl(request.url), {
      method: request.method,
      headers: request.headers,
      body: ['GET', 'HEAD'].includes(request.method) ? null : request.body,
    });
  }

  // Keystatic handler 호출 → { body, status, headers: [[key,val],...] } 형태 반환
  const result = await handler(request) as any;
  const { body, status, headers: rawHeaders } = result;

  // headers 배열을 ResponseInit 형태로 변환
  const responseHeaders: [string, string][] = [];
  if (Array.isArray(rawHeaders)) {
    for (const [key, value] of rawHeaders) {
      const fixedValue = key.toLowerCase() === 'location' && value.includes('localhost')
        ? fixLocalhostUrl(value)
        : value;
      responseHeaders.push([key, fixedValue]);
    }
  }

  return new Response(body ?? null, { status, headers: responseHeaders });
}
