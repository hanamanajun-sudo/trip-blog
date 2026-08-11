import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';
import cloudflare from '@astrojs/cloudflare';
import rehypeImgSize from './src/plugins/rehype-img-size.mjs';

export default defineConfig({
  site: 'https://trip.lalalakorea.com',
  trailingSlash: 'never',
  output: 'static',
  adapter: cloudflare(),
  integrations: [tailwind()],
  markdown: {
    rehypePlugins: [rehypeImgSize],
    shikiConfig: {
      theme: 'github-light',
    },
  },
});
