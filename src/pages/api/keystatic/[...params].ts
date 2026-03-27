export const prerender = false;

import { makeGenericAPIRouteHandler } from '@keystatic/core/api/generic';
import config from '../../../../keystatic.config';

const handler = makeGenericAPIRouteHandler({ config });

function fixUrl(url: string): string {
  return url.replace(/https?:\/\/localhost(:\d+)?/g, 'https://trip.lalalakorea.com');
}

export async function ALL(context: any) {
  let { request } = context;

  // localhost URL을 실제 도메인으로 교체
  if (request.url.includes('localhost')) {
    request = new Request(fixUrl(request.url), {
      method: request.method,
      headers: request.headers,
      body: ['GET', 'HEAD'].includes(request.method) ? null : request.body,
    });
  }

  // Keystatic handler 호출
  const response = await handler(request);

  // Location 헤더도 localhost면 교체
  const location = response.headers.get('location');
  if (location && location.includes('localhost')) {
    const newHeaders = new Headers(response.headers);
    newHeaders.set('location', fixUrl(location));
    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: newHeaders,
    });
  }

  return response;
}
