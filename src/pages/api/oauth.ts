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

  // 이 팝업(A)은 우리 도메인에 머뭄 → window.opener가 살아있음
  // GitHub OAuth는 서브 팝업(B)으로 열기
  // B가 callback으로 리다이렉트 → BroadcastChannel로 토큰 전송
  // A가 토큰 받아서 window.opener(Decap CMS)에 전달 → event.source = A = authWindow ✓
  const html = `<!doctype html>
<html>
<head><meta charset="utf-8"></head>
<body>
<p style="font-family:sans-serif;padding:20px;color:#666">GitHub 로그인 중...</p>
<script>
  var savedOpener = window.opener;

  var githubWindow = window.open(
    ${JSON.stringify(githubAuthUrl)},
    'github-oauth',
    'width=600,height=700,toolbar=no,location=no,menubar=no'
  );

  var bc = new BroadcastChannel('cms-auth');
  bc.onmessage = function(e) {
    bc.close();
    if (githubWindow && !githubWindow.closed) {
      githubWindow.close();
    }
    if (savedOpener) {
      // 이 창(A)에서 postMessage → Decap CMS는 event.source === authWindow(A) ✓
      savedOpener.postMessage(e.data, '*');
    }
    setTimeout(function() { window.close(); }, 300);
  };

  // 서브 팝업이 차단된 경우 링크 표시
  if (!githubWindow || githubWindow.closed) {
    document.body.innerHTML = '<p style="font-family:sans-serif;padding:20px">팝업이 차단되었습니다. <a href="' + ${JSON.stringify(githubAuthUrl)} + '" target="github-oauth" onclick="this.parentNode.innerHTML=\\'로그인 중...\\'">여기를 클릭</a>하세요.</p>';
  }
<\/script>
</body>
</html>`;

  return new Response(html, { headers: { 'Content-Type': 'text/html; charset=utf-8' } });
}
