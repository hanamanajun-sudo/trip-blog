export const prerender = false;

export async function GET({ url }: any) {
  const provider = url.searchParams.get('provider');

  if (provider !== 'github') {
    return new Response('지원하지 않는 provider입니다', { status: 400 });
  }

  const clientId = process.env.GITHUB_CLIENT_ID || process.env.KEYSTATIC_GITHUB_CLIENT_ID;
  const callbackUrl = 'https://trip.lalalakorea.com/api/oauth/callback';

  const params = new URLSearchParams({
    client_id: clientId || '',
    redirect_uri: callbackUrl,
    scope: 'repo,user',
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
    var origin = window.opener && window.opener.origin;

    // 1단계: 핸드셰이크 메시지 전송
    if (window.opener) {
      window.opener.postMessage('authorizing:' + provider, origin || '*');
    }

    // 2단계: 부모의 에코백을 기다린 후 GitHub로 이동
    window.addEventListener('message', function onMsg(e) {
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

  return new Response(html, { headers: { 'Content-Type': 'text/html; charset=utf-8' } });
}
