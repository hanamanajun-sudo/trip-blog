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

  const html = `<!doctype html>
<html>
<head><meta charset="utf-8"></head>
<body>
<p style="font-family:sans-serif;padding:20px;color:#666">GitHub 로그인 중...</p>
<script>
  var savedOpener = window.opener;

  // localStorage 이전 값 초기화
  localStorage.removeItem('cms-auth-result');

  // GitHub OAuth를 서브 팝업으로 열기
  var githubWindow = window.open(
    ${JSON.stringify(githubAuthUrl)},
    'github-oauth',
    'width=600,height=700,toolbar=no,location=no,menubar=no'
  );

  if (!githubWindow || githubWindow.closed) {
    document.querySelector('p').innerHTML = '팝업이 차단됨. <a href="${githubAuthUrl}" target="github-oauth">여기 클릭</a>';
  }

  // localStorage를 300ms마다 폴링 (COOP로 BroadcastChannel이 안 될 때를 대비)
  var poll = setInterval(function() {
    var stored = localStorage.getItem('cms-auth-result');
    if (!stored) return;

    try {
      var result = JSON.parse(stored);
      // 2분 이내 결과만 사용
      if (Date.now() - result.ts > 120000) {
        localStorage.removeItem('cms-auth-result');
        return;
      }
      clearInterval(poll);
      localStorage.removeItem('cms-auth-result');

      if (githubWindow && !githubWindow.closed) githubWindow.close();

      if (savedOpener) {
        // 이 창(팝업A)에서 postMessage → event.source = 팝업A = authWindow ✓
        savedOpener.postMessage(result.msg, '*');
      }
      setTimeout(function() { window.close(); }, 300);
    } catch(e) {}
  }, 300);

  // 5분 후 타임아웃
  setTimeout(function() { clearInterval(poll); }, 300000);
<\/script>
</body>
</html>`;

  return new Response(html, { headers: { 'Content-Type': 'text/html; charset=utf-8' } });
}
