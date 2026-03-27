import { config, fields, collection } from '@keystatic/core';

export default config({
  storage: {
    kind: 'github',
    repo: 'hanamanajun-sudo/trip-blog',
  },
  ui: {
    brand: { name: 'lalalakorea 블로그' },
  },
  collections: {
    blog: collection({
      label: '블로그 글',
      slugField: 'title',
      path: 'src/content/blog/*',
      format: { contentField: 'content' },
      schema: {
        title: fields.slug({ name: { label: '제목' } }),
        date: fields.date({
          label: '날짜',
          defaultValue: { kind: 'today' },
        }),
        category: fields.select({
          label: '카테고리',
          options: [
            { label: '해외 여행', value: '해외 여행' },
            { label: '국내 여행', value: '국내 여행' },
            { label: '여행', value: '여행' },
            { label: '지구 상식', value: '지구 상식' },
            { label: '캠핑', value: '캠핑' },
            { label: '커피', value: '커피' },
            { label: '지구 위기& 재난 대비', value: '지구 위기& 재난 대비' },
            { label: '유튜버 되기 자료', value: '유튜버 되기 자료' },
          ],
          defaultValue: '해외 여행',
        }),
        entry_slug: fields.text({
          label: 'URL 슬러그',
          description: 'URL에 쓰일 주소 (예: 일본-여행-추천)',
          validation: { isRequired: false },
        }),
        description: fields.text({
          label: '요약 설명',
          description: '검색 결과에 표시되는 설명 (SEO)',
          multiline: true,
          validation: { isRequired: false },
        }),
        content: fields.markdoc({
          label: '본문',
          options: {
            image: {
              directory: 'public/images',
              publicPath: '/images/',
            },
          },
        }),
      },
    }),
  },
});
