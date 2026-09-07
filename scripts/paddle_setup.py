#!/usr/bin/env python3
"""
paddle_setup.py — Set up Lemon Squeezy for Uzi Network (SA-friendly Stripe alternative)

Why Lemon Squeezy over Stripe:
- Accepts South African businesses
- No US entity needed
- Handles all tax collection globally
- Pays out via bank transfer or PayPal
- 5% + $0.50 per transaction (same as Stripe)
- Has subscriptions, one-time, and usage-based billing

Setup steps for you (15 min):
1. Go to https://www.lemonsqueezy.com
2. Sign up with uzinetwork+lemonsqueezy@gmail.com
3. Verify email
4. Connect bank account or PayPal for payouts
5. Create product: "Uzi Network Pro" — $9/month subscription
6. Get API key from Settings → API
7. Get Store ID and Product/Variant ID
8. Save to /home/ubuntu/.hermes/.service-credentials

Until then, here's what I'll build:
"""
import json
from pathlib import Path

# Config template
CONFIG = {
    "lemonsqueezy": {
        "api_key": "LEMONSQUEEZY_API_KEY_HERE",  # lsq_xxx
        "store_id": "STORE_ID_HERE",  # numeric
        "product_id": "PRODUCT_ID_HERE",  # numeric
        "variant_id": "VARIANT_ID_HERE",  # numeric
        "webhook_secret": "WEBHOOK_SECRET_HERE",
        "success_url": "https://uzi.network.store/pro/success",
        "cancel_url": "https://uzi.network.store/pro",
    }
}

print(__doc__)
print("=" * 60)
print("Save these to /home/ubuntu/.hermes/.service-credentials:")
print("=" * 60)
for k, v in CONFIG["lemonsqueezy"].items():
    print(f"export LEMONSQUEEZY_{k.upper()}='{v}'")
print()
print("Once you sign up, replace the placeholders with real values.")
print("Then run: python3 paddle_setup.py --test")
