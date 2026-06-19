export const prerender = true;
import { getCollection } from 'astro:content';
import { slugify } from '../utils/slugify';

const SITE = 'https://trip.lalalakorea.com';
const PAGE_SIZE = 20; // [...page].astro의 paginate pageSize와 일치

export async function GET() {
  const posts = await getCollection('blog', ({ data }) => !data.draft);
  const today = new Date().toISOString().split('T')[0];

  // 1) 개별 글
  const postUrls = posts.map(post => {
    const slug = post.data.entry_slug || post.id;
    const date = new Date(post.data.date).toISOString().split('T')[0];
    return `  <url>
    <loc>${SITE}/entry/${slug}</loc>
    <lastmod>${date}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>`;
  });

  // 2) 카테고리 페이지
  const categories = [...new Set(posts.map(p => p.data.category))];
  const categoryUrls = categories.map(cat => `  <url>
    <loc>${SITE}/category/${slugify(cat)}</loc>
    <lastmod>${today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.6</priority>
  </url>`);

  // 3) 목록 페이지네이션 (/, /2, /3 ...)
  const totalPages = Math.ceil(posts.length / PAGE_SIZE);
  const pageUrls = [];
  for (let i = 1; i <= totalPages; i++) {
    pageUrls.push(`  <url>
    <loc>${i === 1 ? `${SITE}/` : `${SITE}/${i}`}</loc>
    <lastmod>${today}</lastmod>
    <changefreq>${i === 1 ? 'daily' : 'weekly'}</changefreq>
    <priority>${i === 1 ? '1.0' : '0.5'}</priority>
  </url>`);
  }

  const sitemap = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${pageUrls.join('\n')}
${categoryUrls.join('\n')}
${postUrls.join('\n')}
</urlset>`;

  return new Response(sitemap, {
    headers: { 'Content-Type': 'application/xml' },
  });
}
