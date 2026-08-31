/**
 * Single source of truth for site metadata + nav + social.
 * Edit values here to roll out across the whole site.
 */
export const SITE = {
  name: 'Uzi Network',
  tagline: 'Real reviews. Real tests. Real tech.',
  description: 'Hands-on reviews of the tech and AI tools that actually move the needle. No fluff, no paid placement, no AI-generated filler.',
  url: 'https://uzi.network.store',
  ogImage: '/og-default.png',
  twitter: '@uzinetwork',
  email: 'hello@uzi.network.store',
  locale: 'en-US',
} as const;

export const NAV = [
  { href: '/', label: 'Home' },
  { href: '/reviews', label: 'Reviews' },
  { href: '/blog', label: 'Blog' },
  { href: '/about', label: 'About' },
] as const;

export const SOCIAL = [
  { href: 'https://youtube.com/@uzinetwork', label: 'YouTube' },
  { href: 'https://tiktok.com/@uzinetwork', label: 'TikTok' },
  { href: 'https://facebook.com/uzinetwork', label: 'Facebook' },
  { href: 'https://twitter.com/uzinetwork', label: 'X / Twitter' },
] as const;

export const CATEGORIES = [
  { slug: 'ai', label: 'AI Tools' },
  { slug: 'laptops', label: 'Laptops' },
  { slug: 'audio', label: 'Audio' },
  { slug: 'wearables', label: 'Wearables' },
  { slug: 'smart-home', label: 'Smart Home' },
  { slug: 'productivity', label: 'Productivity' },
] as const;

/** Affiliate disclosure shown near every review and CTA. Required by FTC. */
export const AFFILIATE_DISCLOSURE =
  'Uzi Network earns a commission when you buy through our links. We never let that change our verdict. ' +
  'Every review is hands-on, independent, and paid for by us, not by brands.';