import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';
import vercel from '@astrojs/vercel';
import keystatic from '@keystatic/astro';
import react from '@astrojs/react';
import markdoc from '@astrojs/markdoc';

export default defineConfig({
  site: 'https://trip.lalalakorea.com',
  output: 'server',
  adapter: vercel({ webAnalytics: { enabled: false } }),
  integrations: [tailwind(), react(), markdoc(), keystatic()],
  markdown: {
    shikiConfig: {
      theme: 'github-light',
    },
  },
});
