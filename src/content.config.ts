import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const reviews = defineCollection({
  loader: glob({ pattern: '**/*.{md,mdx}', base: './src/content/reviews' }),
  schema: z.object({
    title: z.string(),
    brand: z.string(),
    category: z.enum(['ai', 'laptops', 'audio', 'wearables', 'smart-home', 'productivity']),
    price: z.string(),
    priceUsd: z.number().optional(),
    rating: z.number().min(0).max(5),
    releaseDate: z.coerce.date(),
    lastUpdated: z.coerce.date().optional(),
    cover: z.string().optional(),
    affiliate: z.object({
      url: z.string().url(),
      network: z.enum(['amazon', 'impact', 'partnerstack', 'cj', 'direct', 'other']),
      tag: z.string().optional(),
    }),
    pros: z.array(z.string()).default([]),
    cons: z.array(z.string()).default([]),
    verdict: z.string(),
    tldr: z.string().optional(),
    featured: z.boolean().default(false),
    tags: z.array(z.string()).default([]),
  }),
});

const blog = defineCollection({
  loader: glob({ pattern: '**/*.{md,mdx}', base: './src/content/blog' }),
  schema: z.object({
    title: z.string(),
    description: z.string(),
    date: z.coerce.date(),
    author: z.string().default('Uzi Network'),
    tags: z.array(z.string()).default([]),
    cover: z.string().optional(),
    draft: z.boolean().default(false),
  }),
});

export const collections = { reviews, blog };