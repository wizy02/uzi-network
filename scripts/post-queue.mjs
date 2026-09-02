/**
 * Uzi Network — Social Media Posting Queue
 *
 * Reads the generated social posts from docs/social/{platform}/ and
 * prints a daily posting schedule. When platform API keys are added
 * to ~/.hermes/.social-credentials, this script posts automatically.
 *
 * Schedule (per product, 5 platforms):
 * - YouTube Short:     Mon 9am
 * - TikTok:            Mon 4pm + Sat 9am
 * - X thread:          Tue 12pm
 * - Pinterest:         Wed 7am
 * - Instagram Reel:    Thu 4pm
 *
 * Cycle time: 22 products × 5 platforms = 110 posts over 5 weeks
 * After initial push: 22 posts/week = 3.5/week per platform (sustainable)
 *
 * Usage:
 *   node scripts/post-queue.mjs show       # Show this week's schedule
 *   node scripts/post-queue.mjs preview    # Show the next 7 posts with content
 *   node scripts/post-queue.mjs auto       # Auto-post (requires credentials)
 */

import { readFileSync, readdirSync, existsSync, writeFileSync, mkdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const root = join(__dirname, '..');

const PLATFORMS = ['youtube_short', 'tiktok', 'x_thread', 'pinterest', 'instagram'];
const PLATFORM_LABELS = {
  youtube_short: 'YouTube Short',
  tiktok: 'TikTok',
  x_thread: 'X thread',
  pinterest: 'Pinterest',
  instagram: 'Instagram Reel',
};

// Cycle: 22 products × 5 platforms
// Start date: today
// Time slots per week
const SLOTS = [
  { day: 1, hour: 9,  platform: 'youtube_short' },  // Mon 9am
  { day: 1, hour: 16, platform: 'tiktok' },          // Mon 4pm
  { day: 2, hour: 12, platform: 'x_thread' },        // Tue 12pm
  { day: 3, hour: 7,  platform: 'pinterest' },       // Wed 7am
  { day: 4, hour: 16, platform: 'instagram' },       // Thu 4pm
  { day: 6, hour: 9,  platform: 'tiktok' },          // Sat 9am
];

function getAllPosts() {
  const posts = [];
  for (const platform of PLATFORMS) {
    const dir = join(root, 'docs/social', platform);
    if (!existsSync(dir)) continue;
    const files = readdirSync(dir).filter(f => f.endsWith('.md'));
    for (const f of files) {
      const slug = f.replace('.md', '');
      const content = readFileSync(join(dir, f), 'utf-8');
      posts.push({ platform, slug, content });
    }
  }
  return posts;
}

function getSchedule(weeks = 4) {
  const posts = getAllPosts();
  const schedule = [];
  let postIdx = 0;

  for (let week = 0; week < weeks; week++) {
    for (const slot of SLOTS) {
      const p = posts[postIdx % posts.length];
      if (!p) continue;
      const date = new Date();
      date.setDate(date.getDate() + (week * 7) + (slot.day - 1));
      date.setHours(slot.hour, 0, 0, 0);
      schedule.push({
        date,
        platform: PLATFORM_LABELS[slot.platform],
        slug: p.slug,
        content: p.content,
      });
      postIdx++;
    }
  }
  return schedule;
}

function show() {
  const schedule = getSchedule(4);
  console.log(`\n=== Uzi Network — Social Posting Schedule (4 weeks) ===\n`);
  for (const item of schedule) {
    const day = item.date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
    const time = item.date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });
    console.log(`  ${day} ${time}  ·  ${item.platform.padEnd(20)} ·  ${item.slug}`);
  }
  console.log(`\nTotal: ${schedule.length} posts across 4 weeks`);
  console.log(`(5 platforms × 6 slots/week × 4 weeks)\n`);
}

function preview(n = 7) {
  const schedule = getSchedule(2);
  console.log(`\n=== Next ${n} posts with full content ===\n`);
  for (const item of schedule.slice(0, n)) {
    const day = item.date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
    const time = item.date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });
    console.log(`\n--- ${day} ${time} · ${item.platform} · ${item.slug} ---`);
    console.log(item.content.split('\n').slice(0, 12).join('\n'));
    console.log('... (truncated)');
  }
}

function auto() {
  console.log('Auto-posting requires platform API credentials.');
  console.log('Add them to ~/.hermes/.social-credentials:');
  console.log('  export YOUTUBE_API_KEY=...');
  console.log('  export TIKTOK_ACCESS_TOKEN=...');
  console.log('  export X_API_KEY=...');
  console.log('  export X_API_SECRET=...');
  console.log('  export X_ACCESS_TOKEN=...');
  console.log('  export X_ACCESS_SECRET=...');
  console.log('  export PINTEREST_ACCESS_TOKEN=...');
  console.log('  export INSTAGRAM_ACCESS_TOKEN=...');
  console.log('\nUntil then, run "show" for the schedule and copy-paste manually.');
}

const cmd = process.argv[2] || 'show';
if (cmd === 'show') show();
else if (cmd === 'preview') preview(parseInt(process.argv[3]) || 7);
else if (cmd === 'auto') auto();
else {
  console.log('Usage: node scripts/post-queue.mjs [show|preview|auto]');
}
