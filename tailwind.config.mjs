/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Pretendard', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
      },
      colors: {
        // Travel theme: Sky Blue + Adventure Orange (ui/ux pro max 추천)
        border: '#BAE6FD',
        background: '#F0F9FF',
        foreground: '#0C4A6E',
        muted: {
          DEFAULT: '#E0F2FE',
          foreground: '#64748B',
        },
        accent: {
          DEFAULT: '#EA580C',
          foreground: '#FFFFFF',
        },
        primary: {
          DEFAULT: '#0EA5E9',
          foreground: '#FFFFFF',
        },
        card: {
          DEFAULT: '#FFFFFF',
          foreground: '#0C4A6E',
        },
      },
      typography: {
        DEFAULT: {
          css: {
            maxWidth: 'none',
            color: 'hsl(222.2 84% 4.9%)',
            h1: { fontWeight: '700' },
            h2: { fontWeight: '600' },
            h3: { fontWeight: '600' },
            'blockquote p': {
              fontStyle: 'normal',
            },
            img: {
              borderRadius: '0.5rem',
              margin: '1.5rem auto',
            },
          },
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
};
