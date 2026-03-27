import { defineMiddleware } from 'astro:middleware';

export const onRequest = defineMiddleware(async (context, next) => {
  const response = await next();

  // Keystatic OAuth 리다이렉트 응답의 Location 헤더에서
  // localhost를 실제 도메인으로 교체
  if (context.url.pathname.startsWith('/api/keystatic')) {
    const location = response.headers.get('location');
    if (location && location.includes('localhost')) {
      const fixedLocation = location.replace(
        /https?:\/\/localhost(:\d+)?/g,
        'https://trip.lalalakorea.com'
      );
      const newHeaders = new Headers(response.headers);
      newHeaders.set('location', fixedLocation);
      return new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers: newHeaders,
      });
    }
  }

  return response;
});
