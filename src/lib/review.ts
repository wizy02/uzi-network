/**
 * Review schema and helpers.
 *
 * A "Review" is one product review. The homepage reads `getAllReviews()`,
 * the [slug] page reads `getReviewBySlug()`. Frontmatter lives in MDX
 * files under `src/content/reviews/` so you can publish a review without
 * touching any code.
 */
import { z } from 'astro:content';

export const reviewSchema = z.object({
  title: z.string(),
  slug: z.string(),
  brand: z.string(),
  category: z.enum(['ai', 'laptops', 'audio', 'wearables', 'smart-home', 'productivity']),
  price: z.string(),                 // "$1,299" — string so we can do "$—", "Free", etc.
  priceUsd: z.number().optional(),   // numeric for sorting/comparison
  rating: z.number().min(0).max(5),  // 0-5, supports half stars
  releaseDate: z.coerce.date(),
  lastUpdated: z.coerce.date().optional(),
  cover: z.string().optional(),      // /images/reviews/foo.jpg
  affiliate: z.object({
    url: z.string().url(),
    network: z.enum(['amazon', 'impact', 'partnerstack', 'cj', 'direct', 'other']),
    tag: z.string().optional(),      // optional click-tracking tag
  }),
  pros: z.array(z.string()).default([]),
  cons: z.array(z.string()).default([]),
  verdict: z.string(),               // 1-2 sentence verdict
  tldr: z.string().optional(),       // 1 sentence for cards
  featured: z.boolean().default(false),
  tags: z.array(z.string()).default([]),
});

export type ReviewFrontmatter = z.infer<typeof reviewSchema>;

/** Pretty rating as star string for the template. */
export function starString(rating: number): { filled: number; half: boolean; empty: number } {
  const filled = Math.floor(rating);
  const half = rating - filled >= 0.5;
  const empty = 5 - filled - (half ? 1 : 0);
  return { filled, half, empty };
}

/** Format price for display. */
export function fmtPrice(p: string): string {
  return p;
}