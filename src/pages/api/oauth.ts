export const prerender = false;

// GitHub OAuth 시작 - Decap CMS가 팝업으로 이 URL을 열어요
export async function GET({ url, redirect }: any) {
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

  return redirect(`https://github.com/login/oauth/authorize?${params}`);
}
