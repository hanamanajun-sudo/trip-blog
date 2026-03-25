import { getCollection } from 'astro:content';

export async function GET() {
  const posts = await getCollection('blog', ({ data }) => !data.draft);

  const urls = posts.map(post => {
    const slug = post.data.entry_slug || post.slug;
    const date = new Date(post.data.date).toISOString().split('T')[0];
    return `  <url>
    <loc>https://trip.lalalakorea.com/entry/${slug}</loc>
    <lastmod>${date}</lastmod>
    <changefreq>monthly</changefreq>
  </url>`;
  });

  const sitemap = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://trip.lalalakorea.com/</loc>
    <changefreq>weekly</changefreq>
  </url>
${urls.join('\n')}
</urlset>`;

  return new Response(sitemap, {
    headers: {
      'Content-Type': 'application/xml',
    },
  });
}
