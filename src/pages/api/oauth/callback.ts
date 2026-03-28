export const prerender = false;

export async function GET({ url }: any) {
  const code = url.searchParams.get('code');
  const error = url.searchParams.get('error');

  if (error || !code) {
    const html = `<!doctype html><html><body>
<script>
  localStorage.setItem('cms-auth-result', JSON.stringify({msg: 'authorization:github:error:${error || 'no_code'}', ts: Date.now()}));
  setTimeout(function(){ window.close(); }, 500);
<\/script>
</body></html>`;
    return new Response(html, { headers: { 'Content-Type': 'text/html; charset=utf-8' } });
  }

  const clientId = process.env.GITHUB_CLIENT_ID || process.env.KEYSTATIC_GITHUB_CLIENT_ID;
  const clientSecret = process.env.GITHUB_CLIENT_SECRET || process.env.KEYSTATIC_GITHUB_CLIENT_SECRET;

  const tokenRes = await fetch('https://github.com/login/oauth/access_token', {
    method: 'POST',
    headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
    body: JSON.stringify({ client_id: clientId, client_secret: clientSecret, code }),
  });

  const data: any = await tokenRes.json();

  if (!data.access_token) {
    const html = `<!doctype html><html><body>
<p>❌ 토큰 교환 실패</p>
<script>
  localStorage.setItem('cms-auth-result', JSON.stringify({msg: 'authorization:github:error:token_failed', ts: Date.now()}));
  setTimeout(function(){ window.close(); }, 2000);
<\/script>
</body></html>`;
    return new Response(html, { headers: { 'Content-Type': 'text/html; charset=utf-8' } });
  }

  const payload = JSON.stringify({ token: data.access_token, provider: 'github' });
  const message = 'authorization:github:success:' + payload;

  const html = `<!doctype html><html><body>
<p>✅ 로그인 성공! 창이 닫힙니다...</p>
<script>
  // localStorage로 팝업A에 전달 (COOP 우회)
  localStorage.setItem('cms-auth-result', JSON.stringify({msg: ${JSON.stringify(message)}, ts: Date.now()}));
  setTimeout(function(){ window.close(); }, 500);
<\/script>
</body></html>`;
  return new Response(html, { headers: { 'Content-Type': 'text/html; charset=utf-8' } });
}
