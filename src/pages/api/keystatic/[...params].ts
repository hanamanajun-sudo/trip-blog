export const prerender = false;

import { makeGenericAPIRouteHandler } from '@keystatic/core/api/generic';
import config from '../../../../keystatic.config';

const handler = makeGenericAPIRouteHandler({ config });

const DOMAIN = 'https://trip.lalalakorea.com';

function fixLocalhostUrl(url: string): string {
  return url.replace(/https?:\/\/localhost(:\d+)?/g, DOMAIN);
}

// GitHub 토큰 교환을 직접 처리 (expiring/non-expiring 둘 다 지원)
async function handleOAuthCallback(request: Request): Promise<Response> {
  const url = new URL(request.url);
  const code = url.searchParams.get('code');
  const errorDescription = url.searchParams.get('error_description');

  if (errorDescription) {
    return new Response(`GitHub OAuth error: ${errorDescription}`, { status: 400 });
  }

  if (!code) {
    return new Response('Missing authorization code', { status: 400 });
  }

  // GitHub에 코드 → 토큰 교환 요청
  const tokenUrl = new URL('https://github.com/login/oauth/access_token');
  tokenUrl.searchParams.set('client_id', process.env.KEYSTATIC_GITHUB_CLIENT_ID || '');
  tokenUrl.searchParams.set('client_secret', process.env.KEYSTATIC_GITHUB_CLIENT_SECRET || '');
  tokenUrl.searchParams.set('code', code);

  const tokenRes = await fetch(tokenUrl.toString(), {
    method: 'POST',
    headers: { Accept: 'application/json' },
  });

  const tokenData: any = await tokenRes.json();

  console.log('[Keystatic OAuth] GitHub response keys:', Object.keys(tokenData));

  if (!tokenData.access_token) {
    console.error('[Keystatic OAuth] No access_token. Response:', JSON.stringify(tokenData));
    return new Response('Authorization failed', { status: 401 });
  }

  // 쿠키 설정
  const isProduction = process.env.NODE_ENV === 'production';
  const cookieBase = `Path=/; SameSite=Lax${isProduction ? '; Secure' : ''}`;

  const headers = new Headers();

  // access_token 쿠키 (만료 설정은 expires_in이 있을 때만)
  const accessMaxAge = tokenData.expires_in ? `; Max-Age=${tokenData.expires_in}` : '';
  headers.append(
    'Set-Cookie',
    `keystatic-gh-access-token=${tokenData.access_token}; ${cookieBase}${accessMaxAge}`
  );

  // refresh_token 쿠키 (있을 때만)
  if (tokenData.refresh_token) {
    const refreshMaxAge = tokenData.refresh_token_expires_in
      ? `; Max-Age=${tokenData.refresh_token_expires_in}`
      : '';
    headers.append(
      'Set-Cookie',
      `keystatic-gh-refresh-token=${tokenData.refresh_token}; ${cookieBase}; HttpOnly${refreshMaxAge}`
    );
  }

  headers.set('Location', '/keystatic');
  return new Response(null, { status: 307, headers });
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

  const pathname = new URL(request.url).pathname;

  // OAuth 콜백은 직접 처리
  if (pathname === '/api/keystatic/github/oauth/callback') {
    return handleOAuthCallback(request);
  }

  // 나머지는 Keystatic 기본 핸들러 사용
  const result = await handler(request) as any;
  const { body, status, headers: rawHeaders } = result;

  const responseHeaders: [string, string][] = [];
  if (Array.isArray(rawHeaders)) {
    for (const [key, value] of rawHeaders) {
      const fixedValue =
        key.toLowerCase() === 'location' && value.includes('localhost')
          ? fixLocalhostUrl(value)
          : value;
      responseHeaders.push([key, fixedValue]);
    }
  }

  return new Response(body ?? null, { status, headers: responseHeaders });
}
