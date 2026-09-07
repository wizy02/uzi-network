// affiliate.ts — Inject tracking parameters into all affiliate links
// Adds ?via=uzinetwork&utm_source=uzinetwork to outbound links for tracking
// Also rewrites bare amazon.com links to use the uzinetwork20-20 tag

const AFFILIATE_NETWORKS: Record<string, { param: string; tag: string }> = {
  amazon: { param: 'tag', tag: 'uzinetwork20-20' },
  jasper: { param: 'via', tag: 'uzinetwork' },
  make: { param: 'via', tag: 'uzinetwork' },
  surfer: { param: 'via', tag: 'uzinetwork' },
  copyai: { param: 'via', tag: 'uzinetwork' },
  writesonic: { param: 'via', tag: 'uzinetwork' },
  pictory: { param: 'via', tag: 'uzinetwork' },
  elevenlabs: { param: 'via', tag: 'uzinetwork' },
  notion: { param: 'via', tag: 'uzinetwork' },
  anthropic: { param: 'via', tag: 'uzinetwork' },
  default: { param: 'via', tag: 'uzinetwork' },
};

export function buildAffiliateUrl(network: string, baseUrl: string): string {
  const config = AFFILIATE_NETWORKS[network] ?? AFFILIATE_NETWORKS.default;
  try {
    const url = new URL(baseUrl);
    if (!url.searchParams.has(config.param)) {
      url.searchParams.set(config.param, config.tag);
    }
    if (!url.searchParams.has('utm_source')) {
      url.searchParams.set('utm_source', 'uzinetwork');
    }
    if (!url.searchParams.has('utm_medium')) {
      url.searchParams.set('utm_medium', 'affiliate');
    }
    return url.toString();
  } catch {
    return baseUrl;
  }
}
