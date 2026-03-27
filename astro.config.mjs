import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';
import vercel from '@astrojs/vercel/serverless';
import keystatic from '@keystatic/astro';

export default defineConfig({
  site: 'https://trip.lalalakorea.com',
  output: 'hybrid',
  adapter: vercel(),
  integrations: [tailwind(), keystatic()],
  markdown: {
    shikiConfig: {
      theme: 'github-light',
    },
  },
});
