export const prerender = false;

// GitHub OAuth 콜백 - 코드를 토큰으로 교환 후 Decap CMS 팝업에 전달
export async function GET({ url }: any) {
  const code = url.searchParams.get('code');
  const error = url.searchParams.get('error');

  if (error || !code) {
    const html = `<!doctype html><html><body><script>
      window.opener && window.opener.postMessage(
        'authorization:github:error:${error || 'no_code'}', '*'
      );
      window.close();
    </script></body></html>`;
    return new Response(html, { headers: { 'Content-Type': 'text/html' } });
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
    const html = `<!doctype html><html><body><script>
      window.opener && window.opener.postMessage(
        'authorization:github:error:token_failed', '*'
      );
      window.close();
    </script></body></html>`;
    return new Response(html, { headers: { 'Content-Type': 'text/html' } });
  }

  const content = JSON.stringify({ token: data.access_token, provider: 'github' });
  const html = `<!doctype html><html><body><script>
    window.opener && window.opener.postMessage(
      'authorization:github:success:${content}', '*'
    );
    setTimeout(function() { window.close(); }, 500);
  </script></body></html>`;
  return new Response(html, { headers: { 'Content-Type': 'text/html' } });
}
