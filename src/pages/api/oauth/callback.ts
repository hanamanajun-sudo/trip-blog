import { env } from 'cloudflare:workers';

export const prerender = false;

const SITE_ORIGIN = 'https://trip.lalalakorea.com';
const STATE_COOKIE = 'cms_oauth_state';

// state는 1회용이다. 성공/실패와 무관하게 응답할 때 지운다.
const CLEAR_STATE_COOKIE = `${STATE_COOKIE}=; HttpOnly; Secure; SameSite=Lax; Path=/api/oauth; Max-Age=0`;

function readCookie(header: string | null, name: string) {
  if (!header) return null;
  for (const part of header.split(';')) {
    const [key, ...rest] = part.trim().split('=');
    if (key === name) return rest.join('=');
  }
  return null;
}

function timingSafeEqual(a: string, b: string) {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

// JSON.stringify는 '/'를 이스케이프하지 않아서 인라인 <script> 안에 그대로 넣으면
// 값에 '</script>'가 섞였을 때 태그가 조기 종료된다. '<'를 유니코드로 escape.
function toScriptLiteral(value: unknown) {
  return JSON.stringify(value).replace(/</g, '\\u003c');
}

// GitHub이 돌려주는 에러 코드만 통과시키고, 그 외 입력은 고정 코드로 뭉갠다.
function safeErrorCode(raw: string | null) {
  return raw && /^[A-Za-z0-9_-]{1,64}$/.test(raw) ? raw : 'oauth_error';
}

function popupResponse(message: string) {
  const html = `<!doctype html><html><body><script>
    var msg = ${toScriptLiteral(message)};
    if (window.opener) {
      window.opener.postMessage(msg, ${toScriptLiteral(SITE_ORIGIN)});
    }
    try {
      var bc = new BroadcastChannel('cms-auth');
      bc.postMessage(msg);
      bc.close();
    } catch(e) {}
    setTimeout(function(){ window.close(); }, 500);
  <\/script></body></html>`;

  return new Response(html, {
    headers: {
      'Content-Type': 'text/html; charset=utf-8',
      'Cache-Control': 'no-store',
      'Set-Cookie': CLEAR_STATE_COOKIE,
    },
  });
}

const errorMessage = (code: string) =>
  'authorization:github:error:' + JSON.stringify({ error: code });

export async function GET({ url, request }: any) {
  const code = url.searchParams.get('code');
  const error = url.searchParams.get('error');
  const state = url.searchParams.get('state');
  const expectedState = readCookie(request.headers.get('Cookie'), STATE_COOKIE);

  if (error || !code) {
    return popupResponse(errorMessage(error ? safeErrorCode(error) : 'no_code'));
  }

  // state가 안 맞으면 우리가 시작한 흐름이 아니다. 토큰 교환 전에 끊는다.
  if (!state || !expectedState || !timingSafeEqual(state, expectedState)) {
    return popupResponse(errorMessage('invalid_state'));
  }

  const clientId = (env as any).GITHUB_CLIENT_ID || (env as any).KEYSTATIC_GITHUB_CLIENT_ID;
  const clientSecret = (env as any).GITHUB_CLIENT_SECRET || (env as any).KEYSTATIC_GITHUB_CLIENT_SECRET;

  const tokenRes = await fetch('https://github.com/login/oauth/access_token', {
    method: 'POST',
    headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
    body: JSON.stringify({ client_id: clientId, client_secret: clientSecret, code }),
  });

  const data: any = await tokenRes.json();

  if (!data.access_token) {
    return popupResponse(errorMessage('token_exchange_failed'));
  }

  const payload = JSON.stringify({ token: data.access_token, provider: 'github' });
  return popupResponse('authorization:github:success:' + payload);
}
