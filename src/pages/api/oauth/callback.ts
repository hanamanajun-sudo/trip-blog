export const prerender = false;

export async function GET({ url }: any) {
  const code = url.searchParams.get('code');
  const error = url.searchParams.get('error');

  if (error || !code) {
    const html = `<!doctype html>
<html><body>
<p>❌ 오류: ${error || 'no_code'}</p>
<script>
  try {
    if (window.opener) {
      window.opener.postMessage('authorization:github:error:${error || 'no_code'}', '*');
    }
    var bc = new BroadcastChannel('cms-auth');
    bc.postMessage('authorization:github:error:${error || 'no_code'}');
    bc.close();
  } catch(e) {}
  setTimeout(function() { window.close(); }, 2000);
<\/script>
</body></html>`;
    return new Response(html, { headers: { 'Content-Type': 'text/html; charset=utf-8' } });
  }

  const clientId = process.env.GITHUB_CLIENT_ID || process.env.KEYSTATIC_GITHUB_CLIENT_ID;
  const clientSecret = process.env.GITHUB_CLIENT_SECRET || process.env.KEYSTATIC_GITHUB_CLIENT_SECRET;

  const tokenRes = await fetch('https://github.com/login/oauth/access_token', {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ client_id: clientId, client_secret: clientSecret, code }),
  });

  const data: any = await tokenRes.json();

  if (!data.access_token) {
    const errDetail = JSON.stringify(data);
    const html = `<!doctype html>
<html><body>
<p>❌ 토큰 교환 실패: ${errDetail}</p>
<script>
  try {
    var bc = new BroadcastChannel('cms-auth');
    bc.postMessage('authorization:github:error:token_failed');
    bc.close();
    if (window.opener) {
      window.opener.postMessage('authorization:github:error:token_failed', '*');
    }
  } catch(e) {}
  setTimeout(function() { window.close(); }, 3000);
<\/script>
</body></html>`;
    return new Response(html, { headers: { 'Content-Type': 'text/html; charset=utf-8' } });
  }

  const payload = JSON.stringify({ token: data.access_token, provider: 'github' });
  const message = 'authorization:github:success:' + payload;

  const html = `<!doctype html>
<html><body>
<p>✅ 로그인 성공! 창이 닫힙니다...</p>
<script>
  var msg = ${JSON.stringify(message)};
  try {
    var bc = new BroadcastChannel('cms-auth');
    bc.postMessage(msg);
    bc.close();
  } catch(e) {}
  try {
    if (window.opener) {
      window.opener.postMessage(msg, '*');
    }
  } catch(e) {}
  setTimeout(function() { window.close(); }, 1000);
<\/script>
</body></html>`;
  return new Response(html, { headers: { 'Content-Type': 'text/html; charset=utf-8' } });
}
