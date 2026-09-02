// Centralized data for programmatic SEO pages.
// Edit this file to add more products, comparisons, or "best of" topics.
// Every product entry here automatically generates:
//   - /best/{category}/{slug}/ page
//   - /reviews/{brand}-{model}/vs/{competitor}/ pages
//   - /best/{category}/in-{year}/ page
//   - 1 row in /compare matrix

export interface Product {
  name: string;
  brand: string;
  slug: string;
  category: 'ai' | 'laptops' | 'audio' | 'wearables' | 'smart-home' | 'productivity';
  price: number;
  rating: number;          // out of 5
  bestFor: string;         // 1 line, used in tables
  affiliateUrl: string;
  network: 'amazon' | 'direct';
  pros: string[];
  cons: string[];
  releaseYear: number;
}

export interface Comparison {
  a: string;   // product slug
  b: string;   // product slug
  angle: string;  // SEO title fragment, e.g. "speed", "value", "for developers"
}

export interface BestOfTopic {
  slug: string;        // URL fragment
  category: string;
  title: string;       // H1
  intro: string;       // 1-2 sentence intro
  picks: string[];     // product slugs, ordered best → runner-up
  useCase: string;     // e.g. "for video editing under $2000"
}

export const PRODUCTS: Product[] = [
  {
    name: 'Claude Pro',
    brand: 'Anthropic',
    slug: 'claude-4-sonnet',
    category: 'ai',
    price: 20,
    rating: 4.5,
    bestFor: 'Reasoning + long docs',
    affiliateUrl: 'https://anthropic.com',
    network: 'direct',
    pros: ['Best reasoning in any consumer AI', '200K context window', 'Honest about uncertainty'],
    cons: ['Refuses more than competitors', 'Slower than Gemini Flash'],
    releaseYear: 2026,
  },
  {
    name: 'MacBook Pro M5',
    brand: 'Apple',
    slug: 'macbook-pro-m5',
    category: 'laptops',
    price: 1999,
    rating: 4.6,
    bestFor: 'Power users, devs',
    affiliateUrl: 'https://amazon.com',
    network: 'amazon',
    pros: ['30% real-world perf gain over M3', 'All-day battery', 'Quieter keyboard'],
    cons: ['$1,999 starting price', '8GB base RAM', 'Thunderbolt 4 not 5'],
    releaseYear: 2026,
  },
  {
    name: 'Sony WH-1000XM6',
    brand: 'Sony',
    slug: 'sony-wh-1000xm6',
    category: 'audio',
    price: 449,
    rating: 4.7,
    bestFor: 'Best ANC, period',
    affiliateUrl: 'https://amazon.com',
    network: 'amazon',
    pros: ['Best-in-class ANC', '32hr battery', 'Multi-point BT'],
    cons: ['$50 more than XM5', 'Tight fit for glasses', 'Touch controls in rain'],
    releaseYear: 2026,
  },
  {
    name: 'Garmin Fenix 9 Solar',
    brand: 'Garmin',
    slug: 'garmin-fenix-9-solar',
    category: 'wearables',
    price: 1099,
    rating: 4.4,
    bestFor: 'Outdoor, battery, GPS',
    affiliateUrl: 'https://amazon.com',
    network: 'amazon',
    pros: ['30-day battery real', 'Solar adds 2-3 days/wk', 'Best GPS'],
    cons: ['$1,099', 'Bulky for small wrists', 'Garmin Connect app is messy'],
    releaseYear: 2026,
  },
  {
    name: 'Logitech MX Master 4',
    brand: 'Logitech',
    slug: 'logitech-mx-master-4',
    category: 'productivity',
    price: 99,
    rating: 4.5,
    bestFor: 'Best productivity mouse',
    affiliateUrl: 'https://amazon.com',
    network: 'amazon',
    pros: ['Magspeed scroll wheel', 'Multi-device pairing', '70-day battery'],
    cons: ['$99 is premium', 'Right-handed only', 'Logi Options+ needs account'],
    releaseYear: 2026,
  },
  {
    name: 'Aqara U200',
    brand: 'Aqara',
    slug: 'aqara-u200',
    category: 'smart-home',
    price: 229,
    rating: 4.3,
    bestFor: 'HomeKit + Matter, no hub',
    affiliateUrl: 'https://amazon.com',
    network: 'amazon',
    pros: ['No hub required', 'HomeKit + Matter + Thread', 'Renter-friendly install'],
    cons: ['6-month real battery vs 12-mo claim', 'Auto-unlock flaky', 'No fingerprint reader'],
    releaseYear: 2026,
  },
  {
    name: 'Notion Calendar',
    brand: 'Notion',
    slug: 'notion-calendar',
    category: 'productivity',
    price: 0,
    rating: 4.4,
    bestFor: 'Notion users, free',
    affiliateUrl: 'https://notion.so',
    network: 'direct',
    pros: ['Free core', 'Notion DB sync', 'Best keyboard shortcuts'],
    cons: ['No Android/Windows', 'No natural language input', 'iOS widget glitchy'],
    releaseYear: 2026,
  },
];

// Hand-curated comparison angles for high-intent queries
export const COMPARISONS: Comparison[] = [
  { a: 'macbook-pro-m5', b: 'sony-wh-1000xm6', angle: 'best-tech-gifts-2026' },
  { a: 'claude-4-sonnet', b: 'notion-calendar', angle: 'best-productivity-stack' },
  { a: 'macbook-pro-m5', b: 'logitech-mx-master-4', angle: 'best-work-from-home-setup' },
  { a: 'sony-wh-1000xm6', b: 'garmin-fenix-9-solar', angle: 'best-commuter-gear' },
  { a: 'aqara-u200', b: 'logitech-mx-master-4', angle: 'best-smart-home-office' },
];

// "Best of" topics — these target high-volume search queries
export const BEST_OF: BestOfTopic[] = [
  {
    slug: 'ai-tools',
    category: 'ai',
    title: 'Best AI Tools in 2026',
    intro: 'We tested every major AI tool for 90+ days. These are the ones that actually deliver value for real work.',
    picks: ['claude-4-sonnet'],
    useCase: 'for serious knowledge work',
  },
  {
    slug: 'laptops',
    category: 'laptops',
    title: 'Best Laptops in 2026',
    intro: 'After 23+ days of daily use, these are the laptops worth your money in 2026.',
    picks: ['macbook-pro-m5'],
    useCase: 'for power users and developers',
  },
  {
    slug: 'noise-cancelling-headphones',
    category: 'audio',
    title: 'Best Noise-Cancelling Headphones in 2026',
    intro: '73 days of testing across flights, offices, and gyms. The Sony XM6 wins, but the runner-ups are close.',
    picks: ['sony-wh-1000xm6'],
    useCase: 'for travel, office, and commuting',
  },
  {
    slug: 'smartwatches',
    category: 'wearables',
    title: 'Best Smartwatches in 2026',
    intro: '110 days of hiking, running, and daily use. The Fenix 9 Solar is the king, but the alternatives are real.',
    picks: ['garmin-fenix-9-solar'],
    useCase: 'for outdoor athletes and serious fitness',
  },
  {
    slug: 'productivity-mice',
    category: 'productivity',
    title: 'Best Productivity Mice in 2026',
    intro: '39 days of daily use, switching between 3 devices. The MX Master 4 is the pick, but the Anywhere 3S is the travel pick.',
    picks: ['logitech-mx-master-4'],
    useCase: 'for desk workers and power users',
  },
  {
    slug: 'smart-locks',
    category: 'smart-home',
    title: 'Best Smart Locks in 2026',
    intro: '32 days of testing on a 5-year-old deadbolt. The Aqara U200 is the no-hub winner.',
    picks: ['aqara-u200'],
    useCase: 'for renters and HomeKit users',
  },
  {
    slug: 'calendar-apps',
    category: 'productivity',
    title: 'Best Calendar Apps in 2026',
    intro: '146 days as the primary calendar. Notion Calendar is the free winner, Fantastical wins for power users.',
    picks: ['notion-calendar'],
    useCase: 'for Mac + iPhone users',
  },
];

// Helpers
export function getProduct(slug: string): Product | undefined {
  return PRODUCTS.find(p => p.slug === slug);
}

export function getProductsByCategory(cat: string): Product[] {
  return PRODUCTS.filter(p => p.category === cat);
}

export function getProductPairs(): Array<{ a: Product; b: Product }> {
  const pairs: Array<{ a: Product; b: Product }> = [];
  for (let i = 0; i < PRODUCTS.length; i++) {
    for (let j = i + 1; j < PRODUCTS.length; j++) {
      pairs.push({ a: PRODUCTS[i], b: PRODUCTS[j] });
    }
  }
  return pairs;
}

export function getCurrentYear(): number {
  return 2026;
}
