import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';
import cloudflare from '@astrojs/cloudflare';
import rehypeImgSize from './src/plugins/rehype-img-size.mjs';

export default defineConfig({
  site: 'https://trip.lalalakorea.com',
  trailingSlash: 'never',
  output: 'static',
  adapter: cloudflare({
    routes: {
      extend: {
        // 존재하지 않는 로컬 폰트/패키지 경로(/packages/pretendard/... 등)를 노리는
        // 봇 트래픽이 Worker를 매번 invoke하지 않도록 Edge Assets에서 바로 404 처리.
        // 실제 폰트는 BaseLayout에서 jsdelivr CDN으로 불러오며 로컬 self-host 자산은 없음.
        exclude: [{ pattern: '/packages/*' }],
      },
    },
  }),
  integrations: [tailwind()],
  markdown: {
    rehypePlugins: [rehypeImgSize],
    shikiConfig: {
      theme: 'github-light',
    },
  },
});
