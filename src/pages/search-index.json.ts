export const prerender = true;

import { getCollection } from 'astro:content';

export async function GET() {
  const posts = await getCollection('blog', ({ data }: any) => !data.draft);

  const index = posts.map((post: any) => ({
    title: post.data.title || '',
    description: post.data.description || '',
    category: post.data.category || '',
    url: `/entry/${post.data.entry_slug || post.id}`,
  }));

  return new Response(JSON.stringify(index), {
    headers: { 'Content-Type': 'application/json' },
  });
}
