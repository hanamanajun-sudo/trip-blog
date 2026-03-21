import { defineCollection, z } from 'astro:content';

const blog = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    date: z.coerce.date(),
    category: z.string().default('여행'),
    entry_slug: z.string().optional(),
    description: z.string().optional(),
    thumbnail: z.string().optional(),
    draft: z.boolean().default(false),
  }),
});

export const collections = { blog };
