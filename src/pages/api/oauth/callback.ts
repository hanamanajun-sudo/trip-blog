export const prerender = false;

export async function GET({ url }: any) {
  const code = url.searchParams.get('code');
  const error = url.searchParams.get('error');

  if (error || !code) {
    const errMsg = JSON.stringify({ error: error || 'no_code' });
    const html = `<!doctype html><html><body><script>
      var msg = 'authorization:github:error:' + ${JSON.stringify(errMsg)};
      if (window.opener) window.opener.postMessage(msg, '*');
      try { var bc = new BroadcastChannel('cms-auth'); bc.postMessage(msg); bc.close(); } catch(e){}
      setTimeout(function(){ window.close(); }, 500);
    <\/script></body></html>`;
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
    const errMsg = JSON.stringify({ error: 'token_exchange_failed' });
    const html = `<!doctype html><html><body>
      <p>Token exchange failed</p>
      <script>
        var msg = 'authorization:github:error:' + ${JSON.stringify(errMsg)};
        if (window.opener) window.opener.postMessage(msg, '*');
        try { var bc = new BroadcastChannel('cms-auth'); bc.postMessage(msg); bc.close(); } catch(e){}
      <\/script></body></html>`;
    return new Response(html, { headers: { 'Content-Type': 'text/html; charset=utf-8' } });
  }

  const payload = JSON.stringify({ token: data.access_token, provider: 'github' });
  const message = 'authorization:github:success:' + payload;

  const html = `<!doctype html><html><body><script>
    var msg = ${JSON.stringify(message)};
    if (window.opener) {
      window.opener.postMessage(msg, '*');
    }
    try {
      var bc = new BroadcastChannel('cms-auth');
      bc.postMessage(msg);
      bc.close();
    } catch(e) {}
    setTimeout(function(){ window.close(); }, 500);
  <\/script></body></html>`;
  return new Response(html, { headers: { 'Content-Type': 'text/html; charset=utf-8' } });
}
