import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';
import vercel from '@astrojs/vercel';
import rehypeImgSize from './src/plugins/rehype-img-size.mjs';

export default defineConfig({
  site: 'https://trip.lalalakorea.com',
  trailingSlash: 'never',
  output: 'static',
  adapter: vercel(),
  integrations: [tailwind()],
  markdown: {
    rehypePlugins: [rehypeImgSize],
    shikiConfig: {
      theme: 'github-light',
    },
  },
});
