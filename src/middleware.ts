import { defineMiddleware } from 'astro:middleware';

export const onRequest = defineMiddleware(async (context, next) => {
  // Keystatic 경로에서 localhost URL을 실제 도메인으로 교체
  if (
    context.url.pathname.startsWith('/api/keystatic') ||
    context.url.pathname.startsWith('/keystatic')
  ) {
    const requestUrl = context.request.url;

    if (requestUrl.includes('localhost')) {
      const forwardedHost =
        context.request.headers.get('x-forwarded-host') ||
        context.request.headers.get('host') ||
        'trip.lalalakorea.com';
      const forwardedProto =
        context.request.headers.get('x-forwarded-proto') || 'https';

      const fixedUrl = requestUrl.replace(
        /https?:\/\/localhost(:\d+)?/,
        `${forwardedProto}://${forwardedHost}`
      );

      const newRequest = new Request(fixedUrl, {
        method: context.request.method,
        headers: context.request.headers,
        body: ['GET', 'HEAD'].includes(context.request.method)
          ? undefined
          : context.request.body,
      });

      return next(newRequest);
    }
  }

  return next();
});
