import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';
import vercel from '@astrojs/vercel';
import react from '@astrojs/react';

export default defineConfig({
  site: 'https://trip.lalalakorea.com',
  trailingSlash: 'never',
  output: 'static',
  adapter: vercel(),
  integrations: [tailwind(), react()],
  markdown: {
    shikiConfig: {
      theme: 'github-light',
    },
  },
});
