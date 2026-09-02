#!/usr/bin/env bash
# Uzi Network — Daily Social Poster
#
# Posts ONE piece of content per day on rotation:
#   Day 1 (Mon): YouTube Short
#   Day 2 (Tue): X thread
#   Day 3 (Wed): Pinterest pin
#   Day 4 (Thu): Instagram Reel
#   Day 5 (Fri): TikTok
#   Day 6 (Sat): TikTok (second post)
#   Day 7 (Sun): rest
#
# Cycles through all 22 products in the catalog.
# When platform API keys are added to ~/.hermes/.social-credentials,
# this script also auto-posts. Without keys, it logs the content to
# docs/social/delivered/ and notifies the user via Discord.
#
# Usage:
#   bash scripts/daily-social.sh

set -e

WORKDIR="/home/ubuntu/projects/uzi-network"
LOG_DIR="$WORKDIR/docs/social/delivered"
LOG_FILE="$LOG_DIR/$(date +%Y-%m-%d).log"

mkdir -p "$LOG_DIR"

DAY_OF_WEEK=$(date +%u)
case $DAY_OF_WEEK in
  1) PLATFORM="youtube_short"; LABEL="YouTube Short" ;;
  2) PLATFORM="x_thread";      LABEL="X thread" ;;
  3) PLATFORM="pinterest";     LABEL="Pinterest" ;;
  4) PLATFORM="instagram";     LABEL="Instagram Reel" ;;
  5) PLATFORM="tiktok";        LABEL="TikTok" ;;
  6) PLATFORM="tiktok";        LABEL="TikTok (round 2)" ;;
  7) PLATFORM="rest";          LABEL="rest day" ;;
esac

if [ "$PLATFORM" = "rest" ]; then
  echo "$(date +%H:%M) — rest day, no post" >> "$LOG_FILE"
  exit 0
fi

# Pick next product in cycle
INDEX_FILE="$WORKDIR/docs/social/.cycle-index"
if [ -f "$INDEX_FILE" ]; then
  INDEX=$(cat "$INDEX_FILE")
else
  INDEX=0
fi

# Get all slugs
SLUGS=$(node -e "
const src = require('fs').readFileSync('src/lib/catalog.ts', 'utf-8');
const slugs = [...src.matchAll(/slug: '([^']+)'/g)].map(m => m[1]);
process.stdout.write(slugs.join('\n'));
" | head -25)

SLUG=$(echo "$SLUGS" | sed -n "$((INDEX + 1))p")
if [ -z "$SLUG" ]; then
  INDEX=0
  SLUG=$(echo "$SLUGS" | sed -n "1p")
fi

INDEX=$((INDEX + 1))
echo "$INDEX" > "$INDEX_FILE"

# Read the post content
POST_FILE="$WORKDIR/docs/social/$PLATFORM/$SLUG.md"
if [ ! -f "$POST_FILE" ]; then
  echo "$(date +%H:%M) — $PLATFORM: no post for $SLUG, skipping" >> "$LOG_FILE"
  exit 0
fi

# Log the post
cat >> "$LOG_FILE" <<EOF
====================================
$(date +%H:%M) — $LABEL: $SLUG
EOF
cat "$POST_FILE" >> "$LOG_FILE"
echo "====================================" >> "$LOG_FILE"

# Try to auto-post if credentials exist
CREDS="$HOME/.hermes/.social-credentials"
if [ -f "$CREDS" ]; then
  source "$CREDS"
  case $PLATFORM in
    x_thread)
      if [ -n "$X_API_KEY" ]; then
        node scripts/post-to-x.mjs "$SLUG" >> "$LOG_FILE" 2>&1 || echo "X post failed" >> "$LOG_FILE"
      fi
      ;;
    tiktok)
      if [ -n "$TIKTOK_ACCESS_TOKEN" ]; then
        node scripts/post-to-tiktok.mjs "$SLUG" >> "$LOG_FILE" 2>&1 || echo "TikTok post failed" >> "$LOG_FILE"
      fi
      ;;
  esac
fi

echo "Posted: $LABEL for $SLUG → $LOG_FILE"
