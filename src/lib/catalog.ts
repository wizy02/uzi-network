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
  // ===== ANKER CHARGING LINE — Tier 1 =====
  {
    name: 'Anker PowerCore 10K',
    brand: 'Anker',
    slug: 'anker-powercore-10k',
    category: 'charging',
    price: 25,
    rating: 4.6,
    bestFor: 'Everyday portable charging',
    affiliateUrl: 'https://amazon.com',
    network: 'amazon',
    pros: ['Slim 0.6" profile', '10,000mAh = 2-3 phone charges', '$25 is the floor for real quality', 'USB-C + USB-A output'],
    cons: ['No fast charging on input', 'Charges the bank itself slowly', 'Not for laptops'],
    releaseYear: 2026,
  },
  {
    name: 'Anker 737 Power Bank 24,000mAh',
    brand: 'Anker',
    slug: 'anker-737-power-bank',
    category: 'charging',
    price: 90,
    rating: 4.7,
    bestFor: 'Laptop + phone charging',
    affiliateUrl: 'https://amazon.com',
    network: 'amazon',
    pros: ['140W output charges a MacBook Pro', '24,000mAh = full laptop + 2 phones', 'Smart display shows real-time wattage', 'TSA-approved for carry-on'],
    cons: ['$90 is premium', 'Heavy at 1.4 lbs', 'Slow to recharge (3+ hours)'],
    releaseYear: 2026,
  },
  {
    name: 'Anker Nano II 65W',
    brand: 'Anker',
    slug: 'anker-nano-ii-65w',
    category: 'charging',
    price: 40,
    rating: 4.7,
    bestFor: 'Travel charger, GaN',
    affiliateUrl: 'https://amazon.com',
    network: 'amazon',
    pros: ['65W in a wallet-sized brick', 'Folds flat for travel', 'GaN technology — no heat issues', 'Works with laptops, phones, tablets'],
    cons: ['Single port (no multi-port)', 'No cable included', '$40 vs $25 for the 30W version'],
    releaseYear: 2026,
  },
  {
    name: 'Anker 727 Charging Station',
    brand: 'Anker',
    slug: 'anker-727-charging-station',
    category: 'charging',
    price: 80,
    rating: 4.5,
    bestFor: 'Home office, 6 devices at once',
    affiliateUrl: 'https://amazon.com',
    network: 'amazon',
    pros: ['2 AC outlets + 4 USB ports (100W total)', 'GaN — cool under load', 'Surge protection built-in', 'Single cable to your desk'],
    cons: ['$80 is high for a power strip', 'No USB-C on every port', 'White only'],
    releaseYear: 2026,
  },
  {
    name: 'Anker 543 USB-C Hub',
    brand: 'Anker',
    slug: 'anker-543-usb-c-hub',
    category: 'charging',
    price: 35,
    rating: 4.4,
    bestFor: 'Laptop docking on a budget',
    affiliateUrl: 'https://amazon.com',
    network: 'amazon',
    pros: ['8-in-1: HDMI 4K + 2 USB-A + USB-C PD + SD/microSD + Ethernet', '100W passthrough charging', 'Plug and play — no drivers', '$35 vs $60+ for CalDigit'],
    cons: ['Plastic body (not aluminum)', 'HDMI only 4K@30Hz', 'No DisplayPort'],
    releaseYear: 2026,
  },
  {
    name: 'Anker Soundcore Life Q35',
    brand: 'Anker',
    slug: 'anker-soundcore-life-q35',
    category: 'audio',
    price: 80,
    rating: 4.4,
    bestFor: 'Best $80 noise-cancelling headphones',
    affiliateUrl: 'https://amazon.com',
    network: 'amazon',
    pros: ['LDAC hi-res audio', '40-hour battery with ANC', 'Multi-point pairing', '$80 vs $449 Sony XM6'],
    cons: ['ANC is good, not great', 'Plastic build', 'App is basic'],
    releaseYear: 2026,
  },
  // ===== SMART HOME EXPANSION — Tier 1 =====
  {
    name: 'eero Max 7',
    brand: 'eero',
    slug: 'eero-max-7',
    category: 'smart-home',
    price: 599,
    rating: 4.5,
    bestFor: 'Best mesh WiFi for smart homes',
    affiliateUrl: 'https://amazon.com',
    network: 'amazon',
    pros: ['WiFi 7 — future-proof', 'Covers 2,500 sq ft per node', 'Built-in Thread + Zigbee + Matter', 'Easy setup via eero app'],
    cons: ['$599 for 1-pack, $1,199 for 2-pack', 'Requires subscription for some features', 'Amazon owns eero (privacy)'],
    releaseYear: 2026,
  },
  {
    name: 'Ring Battery Doorbell Plus',
    brand: 'Ring',
    slug: 'ring-battery-doorbell-plus',
    category: 'smart-home',
    price: 180,
    rating: 4.3,
    bestFor: 'Best video doorbell, easy install',
    affiliateUrl: 'https://amazon.com',
    network: 'amazon',
    pros: ['1536p HD+ head-to-toe video', 'Wire-free install (battery)', 'Works with Alexa', 'Color night vision'],
    cons: ['Subscription required for video history', 'Amazon-owned (privacy)', 'Battery needs recharging every 2-3 months'],
    releaseYear: 2026,
  },
  {
    name: 'TP-Link Kasa Smart Plug',
    brand: 'TP-Link',
    slug: 'tp-link-kasa-smart-plug',
    category: 'smart-home',
    price: 13,
    rating: 4.7,
    bestFor: 'Best budget smart plug',
    affiliateUrl: 'https://amazon.com',
    network: 'amazon',
    pros: ['$13 is the floor for reliable smart plugs', 'Works with Alexa, Google, SmartThings', 'No hub required', 'Compact design'],
    cons: ['No energy monitoring (HS103)', 'WiFi only (no Thread)', 'Plastic, not pretty'],
    releaseYear: 2026,
  },
  {
    name: 'Govee Glide Wall Light',
    brand: 'Govee',
    slug: 'govee-glide-wall-light',
    category: 'smart-home',
    price: 80,
    rating: 4.5,
    bestFor: 'RGB wall lighting for streaming/gaming',
    affiliateUrl: 'https://amazon.com',
    network: 'amazon',
    pros: ['Modular — make any shape', '16 million colors + scenes', 'Music sync mode', 'Matter-compatible'],
    cons: ['$80 is just the starter kit', 'Govee app is bloated', 'Adhesive mount only'],
    releaseYear: 2026,
  },
  // ===== AUDIO EXPANSION — Tier 1 =====
  {
    name: 'Apple AirPods Pro 3',
    brand: 'Apple',
    slug: 'apple-airpods-pro-3',
    category: 'audio',
    price: 249,
    rating: 4.6,
    bestFor: 'Best earbuds for iPhone',
    affiliateUrl: 'https://amazon.com',
    network: 'amazon',
    pros: ['Best-in-class ANC for earbuds', 'Spatial Audio with head tracking', 'H2 chip = seamless iPhone pairing', 'USB-C charging case'],
    cons: ['$249 is steep', 'Average Android experience', 'Battery is only 6 hours'],
    releaseYear: 2026,
  },
  {
    name: 'Bose QuietComfort Ultra',
    brand: 'Bose',
    slug: 'bose-quietcomfort-ultra',
    category: 'audio',
    price: 429,
    rating: 4.5,
    bestFor: 'Most comfortable ANC headphones',
    affiliateUrl: 'https://amazon.com',
    network: 'amazon',
    pros: ['Most comfortable for glasses-wearers', 'Best call quality', 'Immersive Audio (spatial)', 'Premium build'],
    cons: ['$429 vs $449 Sony XM6', '24-hour battery (vs 32 for Sony)', 'ANC slightly behind Sony'],
    releaseYear: 2026,
  },
  {
    name: 'Sennheiser Momentum 4',
    brand: 'Sennheiser',
    slug: 'sennheiser-momentum-4',
    category: 'audio',
    price: 349,
    rating: 4.4,
    bestFor: 'Audiophile-grade wireless headphones',
    affiliateUrl: 'https://amazon.com',
    network: 'amazon',
    pros: ['Best-in-class sound for wireless', '60-hour battery (best in class)', 'aptX Adaptive for hi-res', 'Comfortable for long sessions'],
    cons: ['ANC is good, not as good as Sony/Bose', 'No touch controls', '$349 is high'],
    releaseYear: 2026,
  },
  // ===== OUTDOOR / POWER STATIONS — Tier 1 =====
  {
    name: 'Jackery Explorer 1000 v2',
    brand: 'Jackery',
    slug: 'jackery-explorer-1000-v2',
    category: 'outdoor',
    price: 799,
    rating: 4.6,
    bestFor: 'Portable power station for camping',
    affiliateUrl: 'https://amazon.com',
    network: 'amazon',
    pros: ['1,070Wh capacity', '1,500W AC output', 'Solar input (200W)', 'Quiet operation'],
    cons: ['$799 is significant', 'Heavy at 23 lbs', 'No app for monitoring'],
    releaseYear: 2026,
  },
  {
    name: 'Garmin Instinct 2 Solar',
    brand: 'Garmin',
    slug: 'garmin-instinct-2-solar',
    category: 'wearables',
    price: 399,
    rating: 4.2,
    bestFor: 'Best budget outdoor watch',
    affiliateUrl: 'https://amazon.com',
    network: 'amazon',
    pros: ['Unlimited battery with solar', '$399 vs $1,099 Fenix 9', 'All the Garmin fitness features', 'Rugged MIL-STD-810 build'],
    cons: ['No maps (Fenix-only)', 'Lower-res display than Fenix', 'No touchscreen'],
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
  {
    slug: 'portable-chargers',
    category: 'charging',
    title: 'Best Portable Chargers in 2026',
    intro: 'Tested the top Anker, RAVPower, and budget options. The Anker 737 is the laptop-grade winner, the PowerCore 10K is the everyday pick.',
    picks: ['anker-737-power-bank', 'anker-powercore-10k', 'anker-nano-ii-65w'],
    useCase: 'for travel, commuting, and emergency backup',
  },
  {
    slug: 'wall-chargers',
    category: 'charging',
    title: 'Best Wall Chargers in 2026',
    intro: 'GaN chargers tested for size, heat, and laptop-charging capability. The Anker Nano II 65W is the travel pick.',
    picks: ['anker-nano-ii-65w', 'anker-727-charging-station'],
    useCase: 'for travel and home office',
  },
  {
    slug: 'usb-c-hubs',
    category: 'charging',
    title: 'Best USB-C Hubs in 2026',
    intro: 'Tested 6 hubs under $50. The Anker 543 wins on price-to-ports ratio.',
    picks: ['anker-543-usb-c-hub'],
    useCase: 'for laptop docking on a budget',
  },
  {
    slug: 'noise-cancelling-earbuds',
    category: 'audio',
    title: 'Best Noise-Cancelling Earbuds in 2026',
    intro: 'Tested AirPods Pro 3, Bose QC Earbuds, and Sony WF-1000XM5. The AirPods Pro 3 wins for iPhone, Sony wins for Android.',
    picks: ['apple-airpods-pro-3'],
    useCase: 'for travel, calls, and commuting',
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
    slug: 'mesh-wifi',
    category: 'smart-home',
    title: 'Best Mesh WiFi Systems in 2026',
    intro: 'Tested eero, Orbi, and TP-Link Deco. The eero Max 7 wins for smart homes with Matter + Thread support.',
    picks: ['eero-max-7'],
    useCase: 'for smart homes and large houses',
  },
  {
    slug: 'video-doorbells',
    category: 'smart-home',
    title: 'Best Video Doorbells in 2026',
    intro: 'Tested Ring, Nest, Eufy, and Arlo. The Ring Battery Doorbell Plus wins for the Alexa ecosystem.',
    picks: ['ring-battery-doorbell-plus'],
    useCase: 'for Amazon Alexa households',
  },
  {
    slug: 'smart-plugs',
    category: 'smart-home',
    title: 'Best Smart Plugs in 2026',
    intro: 'Tested TP-Link, Wyze, and Amazon smart plugs. The Kasa HS103 is the budget winner at $13.',
    picks: ['tp-link-kasa-smart-plug'],
    useCase: 'for renters and first-time smart home buyers',
  },
  {
    slug: 'rgb-lighting',
    category: 'smart-home',
    title: 'Best RGB Lighting in 2026',
    intro: 'Tested Govee, Philips Hue, and Nanoleaf. The Govee Glide wins on price-to-flexibility.',
    picks: ['govee-glide-wall-light'],
    useCase: 'for streaming, gaming, and ambient lighting',
  },
  {
    slug: 'portable-power-stations',
    category: 'outdoor',
    title: 'Best Portable Power Stations in 2026',
    intro: 'Tested Jackery, BLUETTI, and Goal Zero. The Jackery Explorer 1000 v2 wins for camping.',
    picks: ['jackery-explorer-1000-v2'],
    useCase: 'for camping, RV, and emergency backup',
  },
  {
    slug: 'outdoor-watches',
    category: 'wearables',
    title: 'Best Outdoor Watches in 2026',
    intro: '110 days of testing. The Fenix 9 Solar is the king, the Instinct 2 Solar is the budget pick.',
    picks: ['garmin-fenix-9-solar', 'garmin-instinct-2-solar'],
    useCase: 'for hiking, trail running, and serious fitness',
  },
  {
    slug: 'bluetooth-headphones',
    category: 'audio',
    title: 'Best Bluetooth Headphones in 2026',
    intro: 'Tested Sony, Bose, Sennheiser, Anker Soundcore, and Apple. Sony XM6 wins overall, Sennheiser wins for sound, Bose wins for comfort, Anker wins for value.',
    picks: ['sony-wh-1000xm6', 'bose-quietcomfort-ultra', 'sennheiser-momentum-4', 'anker-soundcore-life-q35'],
    useCase: 'for travel, office, and daily use',
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
