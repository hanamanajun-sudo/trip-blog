import { env } from 'cloudflare:workers';

export const prerender = false;

const SITE_ORIGIN = 'https://trip.lalalakorea.com';
const STATE_COOKIE = 'cms_oauth_state';

export async function GET({ url }: any) {
  const provider = url.searchParams.get('provider');

  if (provider !== 'github') {
    return new Response('지원하지 않는 provider입니다', { status: 400 });
  }

  const clientId = (env as any).GITHUB_CLIENT_ID || (env as any).KEYSTATIC_GITHUB_CLIENT_ID;
  const callbackUrl = `${SITE_ORIGIN}/api/oauth/callback`;

  // CSRF 방어용 state. HttpOnly 쿠키에 심어두고 콜백에서 대조한다.
  // 이게 없으면 공격자 페이지가 대신 팝업을 열어 인증을 완주시킬 수 있다
  // (이미 앱을 승인한 사용자는 GitHub 동의 화면 없이 그냥 통과하므로).
  const state = crypto.randomUUID();

  const params = new URLSearchParams({
    client_id: clientId || '',
    redirect_uri: callbackUrl,
    // trip-blog는 public 저장소라 repo(=모든 private 저장소 접근) 대신 public_repo면 충분하다.
    scope: 'public_repo,read:user',
    state,
  });

  const githubAuthUrl = `https://github.com/login/oauth/authorize?${params}`;

  // Decap CMS는 2단계 핸드셰이크를 사용:
  // 1) 팝업 → 부모: 'authorizing:github' 전송
  // 2) 부모 → 팝업: 에코백
  // 3) 팝업: GitHub로 리다이렉트
  const html = `<!doctype html>
<html>
<head><meta charset="utf-8"></head>
<body>
<script>
  (function() {
    var provider = 'github';
    var siteOrigin = ${JSON.stringify(SITE_ORIGIN)};

    // 1단계: 핸드셰이크 메시지 전송 (대상 오리진 고정)
    if (window.opener) {
      window.opener.postMessage('authorizing:' + provider, siteOrigin);
    }

    // 2단계: 부모의 에코백을 기다린 후 GitHub로 이동
    window.addEventListener('message', function onMsg(e) {
      if (e.origin !== siteOrigin) return;
      if (e.data === 'authorizing:' + provider) {
        window.removeEventListener('message', onMsg);
        window.location.href = ${JSON.stringify(githubAuthUrl)};
      }
    });

    // 에코가 1초 안에 안 오면 그냥 진행
    setTimeout(function() {
      window.location.href = ${JSON.stringify(githubAuthUrl)};
    }, 1000);
  })();
<\/script>
</body>
</html>`;

  return new Response(html, {
    headers: {
      'Content-Type': 'text/html; charset=utf-8',
      'Cache-Control': 'no-store',
      'Set-Cookie': `${STATE_COOKIE}=${state}; HttpOnly; Secure; SameSite=Lax; Path=/api/oauth; Max-Age=600`,
    },
  });
}
